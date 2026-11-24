"""Builds samples/EXAMPLES.md from the real files: for each source kind, the
input, the OKF concept the build wrote, the Knowledge Catalog entry kcmd turns
it into (samples/catalog_preview, produced by Google's own converter), the
gate verdict, and the searchEntries predicate that finds it."""
from __future__ import annotations

import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
P, L = "acme-ekp", "us-central1"

SVC_HASH = next((HERE / "builds/code-seat-service/bundle/rules/src/main/resources/rules/"
                  "seat-eligibility.yaml/INF_EXIT_ROW").glob("*.md")).stem.split("-")[-1]

EXAMPLES = [
    ("1. Code repo (TPF C)", "code-dcs-seat", "code-repo",
     "sources/code/dcs-seat/seatalloc/infant_rules.c",
     "rules/seatalloc/infant_rules.c/check_exit_row_infant/eligibility-353743",
     {"concept_type": "BusinessRule", "primary_component": "component:dcs.seat-assignment", "lifecycle": "stable"},
     "ekp-rule", {"rule_kind": "eligibility"}),
    ("1b. Any repo kind: rules-as-data in a Java service repo", "code-seat-service", "code-repo",
     "sources/code/seat-service/src/main/resources/rules/seat-eligibility.yaml",
     "rules/src/main/resources/rules/seat-eligibility.yaml/INF_EXIT_ROW/eligibility-" + SVC_HASH,
     {"concept_type": "BusinessRule", "primary_component": "component:dcs.seat-assignment"},
     "ekp-rule", {"enforcement": "config"}),
    ("1c. Any repo kind: Terraform in the same repo", "code-seat-service", "code-repo",
     "sources/code/seat-service/terraform/pubsub.tf",
     "infra/terraform/pubsub.tf/google_pubsub_topic.seat_assigned",
     {"concept_type": "InfraResource", "primary_component": "component:dcs.seat-assignment"},
     "ekp-infra", {"resource_kind": "google_pubsub_topic"}),
    ("2. HLD (AsciiDoc template)", "hld-dcs-seat", "arch-doc",
     "sources/hld/HLD-DCS-SEAT-002.adoc",
     "decisions/HLD-DCS-SEAT-002/dec-seat-eligibility-rules-table",
     {"concept_type": "Decision", "primary_capability": "capability:seat-eligibility", "trust_tier": "human_reviewed"},
     "ekp-decision", {"decision_status": "accepted"}),
    ("3. BRD", "brd-seat", "brd",
     "sources/brd/BRD-SEAT.md",
     "requirements/BRD-SEAT/BR-SEAT-014",
     {"concept_type": "Requirement", "domain": "departure-control"},
     "ekp-requirement", {"req_id": "BR-SEAT-014"}),
    ("4. Wiki (Confluence runbook)", "wiki-dcsops", "wiki",
     "sources/wiki/DCSOPS-48213907.md",
     "procedures/DCSOPS/48213907",
     {"concept_type": "Procedure", "primary_component": "component:dcs.seat-assignment"},
     None, {}),
    ("5. Jira (epic)", "jira-seat", "jira",
     "sources/jira/SEAT-412.json",
     "changes/SEAT-412",
     {"concept_type": "Change", "primary_capability": "capability:seat-eligibility"},
     "ekp-change", {"release": "2026.10"}),
]


def predicate(core: dict, facet_name, facet: dict) -> str:
    parts = [f'aspect:{P}.{L}.ekp-core.{k}="{v}"' for k, v in core.items()]
    if facet_name:
        parts += [f'aspect:{P}.{L}.{facet_name}.{k}="{v}"' for k, v in facet.items()]
    return "\n".join(parts)


def verdict(group: str) -> str:
    out = (HERE / "demo_output.txt").read_text()
    pass2 = out.split("== pass 2")[1].split("== pass 3")[0]
    block = next(b for b in pass2.split("\n\n") if f"entry group {group} " in b)
    return block.strip()


def main():
    md = ["# Worked examples: one per source kind", "",
          "All inputs are synthetic. One storyline runs through every source: *a passenger travelling "
          "with an infant may not sit in an exit row*. Each source contributes a different kind of "
          "knowledge, and all five share anchors, so retrieval can join them.", ""]
    for title, group, profile, src, eid, core, fname, facet in EXAMPLES:
        concept = (HERE / "builds" / group / "bundle" / f"{eid}.md").read_text()
        entry = json.loads((HERE / "catalog_preview" / f"{group}.entries.json").read_text())[eid]
        aspects = {k: v["data"] for k, v in entry["aspects"].items() if "overview" not in k}
        md += [f"## {title}", "",
               f"Profile `{profile}` → entry group `{group}` → concept `{eid}`", "",
               "### Input", "", "```", (HERE / src).read_text().strip(), "```", "",
               "### OKF concept written by the build", "", "````markdown", concept.strip(), "````", "",
               "### Knowledge Catalog entry (kcmd's own converter, no GCP call)", "",
               f"`entryType`: `{entry['entryType']}`  ", f"`name`: `{entry['name']}`", "",
               "```json", json.dumps(aspects, indent=2), "```", "",
               "The body (`dataplex-types.global.overview`) carries the reader header, the markdown, "
               "and kcmd's trailing `## OKF Metadata` block.", "",
               "### Gate verdict (steady state)", "", "```", verdict(group), "```", "",
               "### searchEntries predicate that finds it", "", "```", predicate(core, fname, facet), "```", ""]
    broken = (HERE / "demo_output.txt").read_text().split("== pass 3: next Jira run with defects ==")[1].strip()
    md += ["## 6. What the gate blocks: the next Jira run", "",
           "`samples/builds/jira-seat-next-broken` is the same entry group one run later, with five "
           "planted defects: an alias used as an anchor, a vanished concept, a title-derived ID, an "
           "unverified LLM decision published as stable, and a hand-edited trust tier.", "",
           "```", broken, "```", ""]
    p4 = (HERE / "demo_output.txt").read_text().split("== pass 4: next HLD run, decision text changed since its human review ==")[1].strip()
    dec = (HERE / "builds/hld-dcs-seat-next-changed/bundle/decisions/HLD-DCS-SEAT-002/"
           "dec-seat-eligibility-rules-table.md").read_text()
    head = dec.split("extra:")[0].strip()
    md += ["## 7. OKF v0.3 trust: an edit voids an old review", "",
           "The HLD decision's text changed after the architecture board reviewed it. The emitter "
           "sets `generated.at` to the change time and keeps the old `verified` event as history. "
           "Under OKF v0.3 §5.3 only events at or after `generated.at` count, so trust drops from "
           "human_reviewed to unverified. The unchanged Design concept keeps its original "
           "`generated.at` through carry-forward, so its standing is untouched.", "",
           "```yaml", head, "```", "", "```", p4, "```", ""]
    p5 = (HERE / "demo_output.txt").read_text().split("== pass 5: next wiki run, two unlabelled pages through the LLM lane ==")[1].strip()
    llm = (HERE / "builds/wiki-dcsops-next-llm/bundle/procedures/DCSOPS/48219911.md").read_text()
    md += ["## 8. LLM lane: unlabelled wiki pages", "",
           "Two wiki pages have no label, so no deterministic rule classifies them. `pipeline/llm_lane.py` "
           "sends each to a model with the prompt in `.agents/skills/ekp-okf/references/classify.md` (the "
           "same text an Antigravity session follows) and the JSON schema from `ekp_okf.spec.model_schema()`. "
           "Code owns identity (entry ID, source_ref, owner, dates); the model owns meaning (type, text, "
           "anchors, confidence). The model outputs here are canned fixtures "
           "(`samples/llm_lane_fixtures.json`), not a live model call.", "",
           "* Page 48219911: confidence 0.86, at or above the wiki minimum of 0.8, so it becomes a `Procedure`. As "
           "LLM output with no review, it is `draft`.",
           "* Page 48220450: confidence 0.41, so policy overrides the model's `Procedure` and "
           "quarantines it as `Unclassified` (draft).",
           "* Both report `unresolved_terms` (kiosk) as registry candidates instead of guessing an anchor.", "",
           "````markdown", llm.split("extra:")[0].strip() + "\n...", "````", "", "```", p5, "```", ""]
    (HERE / "EXAMPLES.md").write_text("\n".join(md))
    print("wrote samples/EXAMPLES.md")


if __name__ == "__main__":
    main()
