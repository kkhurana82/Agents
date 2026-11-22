"""Assemble the final AsciiDoc document from template + drafted sections, plus traceability appendices."""
from __future__ import annotations

import datetime as dt
import re

from .adoc import CITE, refs
from .template import HldTemplate


def _esc_cell(s: str) -> str:
    return (s or "").replace("|", "\\|").replace("\n", " ")


def assemble(template: HldTemplate, state: dict, *, generator: str = "hld-agent") -> str:
    brief = state["brief"]
    sections = state.get("sections", {})
    evidence = state.get("evidence", {})
    decisions = [d for d in state.get("decisions", []) if d["status"] in ("accepted", "amended")]
    today = dt.date.today().isoformat()

    # ---- header: keep template attributes, rewrite title, add draft metadata ----
    out: list[str] = []
    hdr = template.header_lines or ["= High-Level Design"]
    out.append(f"= {brief['title']} - High-Level Design")
    existing_attrs = {re.match(r"^:([\w-]+!?):", ln).group(1) for ln in hdr[1:] if re.match(r"^:([\w-]+!?):", ln)}
    out += [ln for ln in hdr[1:]]
    for k, v in (("hld-status", "DRAFT"), ("hld-generated", today), ("hld-generator", generator),
                 ("hld-story", state.get("story_id") or "n/a")):
        if k not in existing_attrs:
            out.append(f":{k}: {v}")
    out.append("")
    out.append("[IMPORTANT]")
    out.append("====")
    out.append(f"AI-assisted draft generated {today} by {generator}. An architect must review every section. "
               "Statements about existing systems cite the evidence appendix; anything uncited is a proposal or "
               "an explicit assumption.")
    out.append("====")
    out.append("")

    # ---- body in template order ----
    for sec in template.sections:
        out += sec.pre_lines
        out.append(sec.heading_line)
        out.append("")
        if sec.mode == "manual":
            out.append(sec.raw_body.strip())
        else:
            body = sections.get(sec.id, {}).get("body", "").strip()
            out.append(body or "NOTE: Not drafted.")
        out.append("")

    has = {r: template.by_role(r) is not None for r in ("decisions", "open_issues")}

    # ---- appendices ----
    if not has["decisions"] and decisions:
        out += ["[appendix]", "== Design Decision Log", ""]
        for d in decisions:
            out += [f"[[{d['id']}]]", f"=== {d['id']}: {d['title']}", "",
                    f"*Status:* {d['status']}", "", f"*Context:* {d['context']}", "",
                    "*Options considered:*", ""] + [f"* {o}" for o in d["options"]] + [
                    "", f"*Decision:* {d['choice']}", "", f"*Rationale:* {d['rationale']}", ""]
            if d.get("consequences"):
                out += ["*Consequences:*", ""] + [f"* {c}" for c in d["consequences"]] + [""]
            if d.get("evidence_ids"):
                out += ["*Evidence:* " + ", ".join(f"<<{e}>>" for e in d["evidence_ids"] if e in evidence), ""]

    if not has["open_issues"]:
        clar = state.get("clarifications", [])
        assumptions = [(sid, a) for sid, s in sections.items() for a in s.get("assumptions", [])]
        issues = [(sid, i) for sid, s in sections.items() for i in s.get("open_issues", [])]
        if clar or assumptions or issues:
            out += ["[appendix]", "== Assumptions and Open Issues", ""]
            if clar:
                out += ["=== Clarifications", "", '[cols="1,4,4,1",options="header"]', "|===",
                        "|ID |Question |Answer / assumption |Source"]
                for c in clar:
                    out.append(f"|{c['id']} |{_esc_cell(c['question'])} |{_esc_cell(c['answer'])} |{c['source']}")
                out += ["|===", ""]
            if assumptions:
                out += ["=== Assumptions", ""] + [f"* {a} _(section: {sid})_" for sid, a in assumptions] + [""]
            if issues:
                out += ["=== Open Issues", ""] + [f"* {i} _(section: {sid})_" for sid, i in issues] + [""]

    # requirements traceability
    req_where: dict[str, list[str]] = {}
    for sec in template.generate_sections:
        for rid in refs(sections.get(sec.id, {}).get("body", ""))["requirements"]:
            req_where.setdefault(rid, []).append(re.sub(r"^(\d+(\.\d+)*\.?)\s+", "", sec.title))
    out += ["[appendix]", "== Requirements Traceability", "", '[cols="1,5,3",options="header"]', "|===",
            "|ID |Requirement |Addressed in"]
    for r in brief.get("requirements", []):
        where = ", ".join(req_where.get(r["id"], [])) or "*NOT ADDRESSED*"
        target = f" (target: {r['measurable_target']})" if r.get("measurable_target") else ""
        out.append(f"|{r['id']} |{_esc_cell(r['text'] + target)} |{_esc_cell(where)}")
    out += ["|===", ""]

    # evidence (anchors make every <<EV-n>> a working cross-reference)
    doc_text = "\n".join(out)
    cited = sorted(set(CITE.findall(doc_text)), key=lambda x: int(x.split("-")[1]))
    out += ["[appendix]", "== Evidence", "",
            f"Cited {len(cited)} of {len(evidence)} retrieved items. Revision is the source commit/version at retrieval time.", ""]
    for eid in cited:
        e = evidence.get(eid)
        if not e:
            continue
        rev = f" @ `{e['revision']}`" if e.get("revision") else ""
        out.append(f"* [[{eid},{eid}]]*{eid}* {_esc_cell(e['title'])} ({e['kind']}, {e['source']}) - `{e['uri']}`{rev}")
    out.append("")
    return "\n".join(out).rstrip() + "\n"
