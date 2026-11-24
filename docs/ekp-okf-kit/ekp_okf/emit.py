"""The one function every source adapter calls to write a concept.

Adapters decide WHAT a concept is (type, anchors, facet values, relations).
This module decides HOW it is written, so every build produces the same shape:
  * OKF v0.2 frontmatter (type label, title, description, provenance, trust)
  * ekp-core + per-type facet aspects under `extra.aspects`, which kcmd's
    native OKF layout pushes as real Knowledge Catalog aspects
  * derived fields (concept_id, lifecycle, trust_tier) computed, never typed
  * the reader header rendered into the body
"""
from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path

from . import okf
from .header import strip_header, with_header
from .kit import CORE_ASPECT, Kit, aspect_key


def iso(dt) -> str:
    if isinstance(dt, str):
        return dt
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse(ts) -> datetime | None:
    """OKF v0.3 timestamps: date-time with offset, or date only (start of day UTC)."""
    if ts is None:
        return None
    if isinstance(ts, datetime):
        return ts if ts.tzinfo else None
    if isinstance(ts, date):
        return datetime(ts.year, ts.month, ts.day, tzinfo=timezone.utc)
    s = str(ts)
    if len(s) == 10:
        try:
            return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    try:
        d = datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None
    return d if d.tzinfo else None


def current_events(verified, generated_at) -> list:
    """OKF v0.3 §5.3: an event is current if its `at` >= generated.at (or there is
    no `generated`). Older events stay in the file as history but give no trust."""
    items = verified if isinstance(verified, list) else ([verified] if verified else [])
    items = [v for v in items if isinstance(v, dict) and v.get("by") and _parse(v.get("at"))]
    g = _parse(generated_at)
    return [v for v in items if g is None or _parse(v["at"]) >= g]


def trust_tier(verified, generated_at=None) -> str:
    cur = current_events(verified, generated_at)
    if not cur:
        return "unverified"
    if any(str(v["by"]).startswith("human:") for v in cur):
        return "human_reviewed"
    return "machine_confirmed"


def _meaningful(meta: dict, body: str) -> str:
    """Content identity for carry-forward: everything except generation/verification
    bookkeeping and the build stamp. Same value => no meaningful change."""
    m = json.loads(json.dumps(meta, default=str))
    for k in ("generated", "verified", "status"):
        m.pop(k, None)
    for k, v in ((m.get("extra") or {}).get("aspects") or {}).items():
        if k.endswith("." + CORE_ASPECT):
            for f in ("build_id", "trust_tier", "lifecycle"):
                v.pop(f, None)
    return hashlib.sha256(json.dumps({"m": m, "b": strip_header(body).strip()},
                                     sort_keys=True).encode()).hexdigest()


def emit_concept(
    kit: Kit, build_dir: Path, *,
    project: str, location: str, entry_group: str, profile: str,
    entry_id: str, ctype: str, title: str, description: str, body: str,
    core: dict, facet: dict | None = None,
    sources: list, generated: dict, verified: list | None = None,
    status: str = "stable", tags: list | None = None, resource: str | None = None,
    superseded_by: str | None = None, previous_bundle: Path | None = None,
) -> Path:
    """`generated.at` must be the last MEANINGFUL change to the content (OKF v0.3
    §5.2), not the build time, or every rebuild voids every review. Pass:
      * deterministic/template extraction: the source's own change time;
      * llm extraction: the generation time.
    With `previous_bundle` (the last published bundle), the emitter carries the
    previous `generated` forward when nothing meaningful changed, and always keeps
    earlier `verified` events as history. If the content did change, those events
    stop being current and the trust tier drops until someone re-verifies."""
    prof = kit.profiles[profile]
    core = dict(core)
    core.update(
        concept_id=f"{entry_group}:{entry_id}",
        concept_type=ctype,
        lifecycle=status,
        profile=prof.ref,
        ontology_version=kit.ontology_version,
        source_kind=prof.source_kind,
    )
    for k in ("valid_from", "valid_to"):
        if core.get(k) is not None:
            core[k] = iso(core[k])
    # stable key order = the order in ontology/core.yaml
    core = {k: core[k] for k in kit.core_fields if core.get(k) is not None}

    aspects = {aspect_key(project, location, CORE_ASPECT): core}
    fname = kit.facet_of(ctype)
    if fname:
        aspects[aspect_key(project, location, f"ekp-{fname}")] = dict(facet or {})

    meta = {"type": kit.label_of(ctype), "title": title, "description": description}
    if resource:
        meta["resource"] = resource
    if tags:
        meta["tags"] = tags
    meta["status"] = status
    if superseded_by:
        meta["superseded_by"] = superseded_by
    meta["generated"] = {"by": generated["by"], "at": iso(generated["at"])}
    events = [{"by": v["by"], "at": iso(v["at"])} for v in (verified or [])]
    meta["sources"] = [{**s, **({"last_modified": iso(s["last_modified"])} if s.get("last_modified") else {})}
                       for s in sources]
    meta["extra"] = {"aspects": aspects}

    prev_file = Path(previous_bundle) / f"{entry_id}.md" if previous_bundle else None
    if prev_file and prev_file.exists():
        pmeta, pbody = okf.split(prev_file.read_text(encoding="utf-8"))
        pmeta = pmeta or {}
        if _meaningful(pmeta, pbody) == _meaningful(meta, body) and pmeta.get("generated"):
            meta["generated"] = {"by": pmeta["generated"]["by"], "at": iso(pmeta["generated"]["at"])}
        prev_events = pmeta.get("verified") or []
        prev_events = prev_events if isinstance(prev_events, list) else [prev_events]
        seen = {(e["by"], e["at"]) for e in events}
        events = [{"by": e["by"], "at": iso(e["at"])} for e in prev_events
                  if (e.get("by"), iso(e.get("at"))) not in seen] + events
    if events:
        events.sort(key=lambda e: e["at"])
        meta["verified"] = events
    # keep OKF key order: verified after generated, before sources
    meta = {k: meta[k] for k in ("type", "title", "description", "resource", "tags", "status",
                                  "superseded_by", "generated", "verified", "sources", "extra")
            if k in meta}
    core["trust_tier"] = trust_tier(meta.get("verified"), meta["generated"]["at"])
    core = {k: core[k] for k in kit.core_fields if core.get(k) is not None}
    aspects[aspect_key(project, location, CORE_ASPECT)] = core

    path = Path(build_dir) / "bundle" / f"{entry_id}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(okf.render(meta, with_header(meta, body, kit)), encoding="utf-8")
    return path


def write_index(build_dir: Path, title: str, description: str) -> Path:
    """Bundle-root index.md (OKF v0.3 §8, §8.1): bundle metadata in frontmatter
    (an agent choosing among many EKP bundles reads `description`), then concepts
    grouped by type for progressive disclosure. Existing root frontmatter is kept,
    as v0.3 requires of producers that regenerate index.md."""
    bundle = Path(build_dir) / "bundle"
    path = bundle / "index.md"
    fm = {"okf_version": "0.3", "title": title, "description": description}
    if path.exists():
        old, _ = okf.split(path.read_text(encoding="utf-8"))
        fm = {**(old or {}), **fm}
    groups: dict[str, list] = {}
    for entry_id, p in okf.concept_files(bundle):
        meta, _ = okf.split(p.read_text(encoding="utf-8"))
        if not meta:
            continue
        tag = " (deprecated)" if meta.get("status") == "deprecated" else ""
        groups.setdefault(meta["type"], []).append(
            f"* [{meta.get('title', entry_id)}](/{entry_id}.md) - {meta.get('description', '')}{tag}")
    out = [f"# {title}", ""]
    for label in sorted(groups):
        out += [f"## {label}", "", *groups[label], ""]
    path.write_text(okf.render(fm, "\n".join(out)), encoding="utf-8")
    return path
