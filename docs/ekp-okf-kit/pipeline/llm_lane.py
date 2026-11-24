"""The pipeline's LLM lane: same skill, same schema, same emitter, same gate.

Most of ingestion needs no model: code, IaC, API specs, template HLDs and Jira
epics go through deterministic adapters. This lane handles only documents with
no deterministic signal (an unlabelled wiki page, a decision in a Jira comment,
a rule stated in BRD prose). Split of responsibility:

  code decides   identity: entry ID (profile path template), source_ref,
                 revision, URL, system, domain, owner, valid_from, generated.at
  model decides  meaning: type, title, description, body, anchors, facet, confidence
  policy decides confidence < profile minimum -> Unclassified; llm output -> draft
  gate decides   whether the build may be pushed

The prompt is .agents/skills/ekp-okf/references/classify.md, the same text an
Antigravity session follows, and the output schema comes from the ontology,
so the model cannot return an unknown type or an alias anchor.

    python -m pipeline.llm_lane samples/sources/wiki/DCSOPS-48219911.md \
        --build-dir build/ --build-id wiki-dcsops-20261125T010000Z \
        --previous last-bundle/ --model fake|gemini-2.5-pro|agy
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import jsonschema
import yaml

from ekp_okf.emit_cli import emit_specs
from ekp_okf.kit import KIT_ROOT, load_kit
from ekp_okf.spec import model_schema, path_for

PROMPT_FILE = KIT_ROOT / ".agents/skills/ekp-okf/references/classify.md"
MODEL_ACTOR = {"fake": "ekp-llm-lane/0.1+fixture"}


# ------------------------------------------------------------------ prompt
def build_prompt(kit, profile: str, document: str) -> str:
    template = PROMPT_FILE.read_text().split("\n---\n", 1)[1]
    raw = yaml.safe_load((KIT_ROOT / "profiles" / f"{profile}.yaml").read_text())
    prof = kit.profiles[profile]
    types = "\n".join(f"- {t}: {kit.knowledge_types[t]['description']}"
                      for t in prof.emits if not kit.is_anchor_type(t))
    anchors = "\n".join(f"- {a['id']}: {a['title']}; aliases: {', '.join(map(str, a.get('aliases', [])))}"
                        for a in kit.anchors.values())
    return (template.replace("{profile_rules}", yaml.safe_dump(raw.get("classification"), sort_keys=False))
            .replace("{types}", types).replace("{anchors}", anchors)
            .replace("{min_confidence}", str(prof.policy.get("min_confidence")))
            .replace("{document}", document))


# ------------------------------------------------------------------ models
def call_fake(prompt: str, schema: dict, page_id: str) -> dict:
    """Offline demo: canned outputs from samples/llm_lane_fixtures.json."""
    fixtures = json.loads((KIT_ROOT / "samples/llm_lane_fixtures.json").read_text())
    return fixtures[page_id]


def call_gemini(prompt: str, schema: dict, model: str, project: str, location: str) -> dict:
    """Vertex AI Gemini with JSON-schema-constrained output. Not run in this kit's
    tests (no GCP access here). pip install google-genai."""
    from google import genai
    from google.genai import types
    client = genai.Client(vertexai=True, project=project, location=location)
    resp = client.models.generate_content(
        model=model, contents=prompt,
        config=types.GenerateContentConfig(temperature=0, response_mime_type="application/json",
                                           response_json_schema=schema))
    return json.loads(resp.text)


def call_agy(prompt: str, schema: dict, model: str | None) -> dict:
    """Antigravity CLI headless mode with --json-schema. Fine for small scheduled
    runs under your own login; for enterprise-scale ingestion prefer Vertex AI.
    Not run in this kit's tests."""
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(schema, f)
    cmd = ["agy", "-p", prompt, "--output-format", "json", "--json-schema", f.name, "--print-timeout", "300s"]
    if model:
        cmd += ["--model", model]
    out = subprocess.run(cmd, capture_output=True, text=True, check=True)
    envelope = json.loads(out.stdout)
    if envelope.get("status") not in (None, "SUCCESS", "success") or "structured_output" not in envelope:
        raise RuntimeError(f"agy run did not return structured output: {envelope.get('error') or envelope}")
    return envelope["structured_output"]


# ------------------------------------------------------------------ the lane
def read_confluence_export(path: Path) -> dict:
    """Stand-in for the Confluence adapter: identity comes from page metadata."""
    text = path.read_text()
    meta = dict(re.findall(r"(Space|Page ID|Version|Labels|Last modified):\s*(\S[^\n]*?)(?=\s{2,}|\n)", text))
    return {"space": meta["Space"], "page": meta["Page ID"], "version": meta["Version"],
            "last_modified": meta["Last modified"], "text": text}


def classify_and_emit(kit, page: dict, *, build_dir: Path, build_id: str, previous: Path | None,
                      model: str, project: str = "", location: str = "") -> dict:
    profile = "wiki"
    schema = model_schema(kit, profile)
    prompt = build_prompt(kit, profile, page["text"])
    if model == "fake":
        out = call_fake(prompt, schema, page["page"])
    elif model == "agy":
        out = call_agy(prompt, schema, None)
    else:
        out = call_gemini(prompt, schema, model, project, location)
    jsonschema.validate(out, schema)                    # never trust a model's JSON blindly

    min_conf = kit.profiles[profile].policy.get("min_confidence") or 0
    ctype = out["type"] if out["confidence"] >= min_conf else "Unclassified"
    ids = {"space": page["space"], "page": page["page"],
           "hash": hashlib.sha256(out["body"].encode()).hexdigest()[:6]}
    entry_id = path_for(kit, profile, ctype, **ids)
    url = f"https://wiki.example.com/pages/viewpage.action?pageId={page['page']}"
    anchors = out["anchors"]
    spec = {
        "entry_id": entry_id, "type": ctype, "title": out["title"],
        "description": out["description"], "body": out["body"], "tags": out.get("tags"),
        "status": "draft",
        "core": {
            "domain": "departure-control", "primary_system": "system:dcs",      # space -> system: adapter alias table
            "primary_component": out.get("primary_component") or None,
            "primary_capability": out.get("primary_capability") or None,
            "source_system": "confluence",
            "source_ref": f"confluence:{page['space']}:{page['page']}" + (f"#d-{ids['hash']}" if ctype == "Decision" else ""),
            "source_revision": page["version"], "source_url": url,
            "extraction": "llm", "confidence": round(float(out["confidence"]), 2),
            "valid_from": page["last_modified"], "owner_team": "team:airport-ops",
            "anchors": sorted(set(["system:dcs"] + anchors)),
        },
        "facet": out.get("facet") or None,
        "sources": [{"id": "page", "resource": url, "title": f"{page['space']} page {page['page']}",
                     "last_modified": page["last_modified"]}],
        "generated": {"by": MODEL_ACTOR.get(model, f"ekp-llm-lane/0.1+{model}"),
                      "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")},
    }
    if ctype == "Unclassified":
        spec["facet"] = None
    emit_specs(kit, build_dir, profile, build_id, [spec], previous)
    return {"entry_id": entry_id, "type": ctype, "model_type": out["type"],
            "confidence": out["confidence"], "registry_candidates": out.get("unresolved_terms", [])}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pages", type=Path, nargs="+")
    ap.add_argument("--build-dir", type=Path, required=True)
    ap.add_argument("--build-id", required=True)
    ap.add_argument("--previous", type=Path)
    ap.add_argument("--model", default="fake")
    ap.add_argument("--project", default="")
    ap.add_argument("--location", default="us-central1")
    ap.add_argument("--print-prompt", action="store_true")
    a = ap.parse_args(argv)
    kit = load_kit()
    for p in a.pages:
        page = read_confluence_export(p)
        if a.print_prompt:
            print(build_prompt(kit, "wiki", page["text"]))
            continue
        r = classify_and_emit(kit, page, build_dir=a.build_dir, build_id=a.build_id,
                              previous=a.previous, model=a.model, project=a.project, location=a.location)
        print(json.dumps(r))


if __name__ == "__main__":
    sys.exit(main())
