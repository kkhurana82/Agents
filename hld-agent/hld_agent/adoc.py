"""AsciiDoc normalisation (cheap deterministic fixes) and lint (deterministic review rules).

Mechanical problems are fixed here instead of spending an LLM revision round on them.
Lint findings with severity blocker/major on a section trigger a redraft of that section.
"""
from __future__ import annotations

import re

from .template import HldTemplate, TemplateSection

FENCE_OPEN = re.compile(r"^```\s*([\w+-]*)\s*$")
MD_HEADING = re.compile(r"^(#{1,6})\s+(\S.*)$")
MD_LINK = re.compile(r"(?<!\])\[([^\]\n]+)\]\((https?://[^)\s]+)\)")
ADOC_HEADING = re.compile(r"^(={1,6})\s+(\S.*?)\s*$")
DELIM = re.compile(r"^(-{4,}|\.{4,}|={4,}|\*{4,}|_{4,}|\+{4,}|/{4,}|\|={3,})$")
CITE = re.compile(r"<<\s*(EV-\d+)\s*(?:,[^>]*)?>>")
REQ_ID = re.compile(r"\b((?:FR|NFR|CON)-\d+)\b")
DEC_ID = re.compile(r"\b(DEC-\d+)\b")
PLACEHOLDER = re.compile(r"\b(TBD|TODO|FIXME|XXX|lorem ipsum)\b|<insert[^>]*>|\[placeholder\]", re.I)
DIAGRAM_BLOCK = re.compile(r"^\[(mermaid|plantuml|ditaa|graphviz|d2|c4plantuml)\b", re.I | re.M)
DIAGRAM_KEYWORDS = ("graph", "flowchart", "sequenceDiagram", "classDiagram", "stateDiagram", "erDiagram",
                    "C4Context", "C4Container", "C4Component", "C4Deployment", "C4Dynamic", "journey",
                    "gantt", "architecture-beta", "block-beta", "@startuml", "mindmap", "timeline")


def normalize_body(body: str, section: TemplateSection) -> str:
    """Convert common Markdown slips to AsciiDoc and drop a repeated section heading."""
    out: list[str] = []
    lines = body.replace("\r\n", "\n").strip("\n").split("\n")

    # drop a leading repeat of the section heading (in either syntax)
    first = next((i for i, ln in enumerate(lines) if ln.strip()), None)
    if first is not None:
        m = ADOC_HEADING.match(lines[first].strip()) or MD_HEADING.match(lines[first].strip())
        if m and _norm_title(m.group(2)) == _norm_title(section.title):
            lines = lines[first + 1:]

    in_fence: str | None = None
    in_delim: str | None = None
    for ln in lines:
        if in_fence is not None:
            if ln.strip() == "```":
                out.append("...." if in_fence in ("mermaid", "plantuml") else "----")
                in_fence = None
            else:
                out.append(ln)
            continue
        if in_delim:
            out.append(ln)
            if ln.strip() == in_delim:
                in_delim = None
            continue
        if m := FENCE_OPEN.match(ln.strip()):
            lang = (m.group(1) or "").lower()
            if lang in ("mermaid", "plantuml"):
                out += [f"[{lang}]", "...."]
            else:
                out += [f"[source,{lang}]" if lang else "[source]", "----"]
            in_fence = lang
            continue
        if DELIM.match(ln.strip()):
            in_delim = ln.strip()
            out.append(ln)
            continue
        if m := MD_HEADING.match(ln):
            out.append("=" * (section.level + len(m.group(1))) + " " + m.group(2))
            continue
        out.append(MD_LINK.sub(r"\2[\1]", ln))
    if in_fence is not None:
        out.append("...." if in_fence in ("mermaid", "plantuml") else "----")
    return re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip() + "\n"


def _norm_title(t: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", re.sub(r"^(\d+(\.\d+)*\.?|[A-Z]\.)\s+", "", t.strip()).lower()).strip()


def refs(body: str) -> dict[str, list[str]]:
    return {
        "evidence": sorted(set(CITE.findall(body)), key=_idnum),
        "requirements": sorted(set(REQ_ID.findall(body)), key=lambda x: (x.split("-")[0], _idnum(x))),
        "decisions": sorted(set(DEC_ID.findall(body)), key=_idnum),
    }


def _idnum(x: str) -> int:
    return int(x.rsplit("-", 1)[1])


def _f(section_id, severity, rule, issue, fix=""):
    return {"section_id": section_id, "severity": severity, "rule": rule, "issue": issue, "fix": fix}


def lint_section(sec: TemplateSection, body: str, *, evidence_ids: set[str], req_ids: set[str],
                 dec_ids: set[str], min_citations: int) -> list[dict]:
    sid, f = sec.id, []
    text = body.strip()
    if len(re.sub(r"\s+", " ", text)) < 40:
        return [_f(sid, "blocker", "L001", "Section is empty or trivially short.", "Write the section per the template guidance.")]

    # L008 delimited blocks must balance (an open block swallows the rest of the document)
    open_d = None
    for ln in text.split("\n"):
        s = ln.strip()
        if open_d:
            if s == open_d:
                open_d = None
        elif DELIM.match(s):
            open_d = s
    if open_d:
        f.append(_f(sid, "blocker", "L008", f"Unterminated delimited block '{open_d}'.", f"Close the block with '{open_d}'."))

    if m := PLACEHOLDER.search(text):
        f.append(_f(sid, "major", "L002", f"Placeholder text found: '{m.group(0)}'.",
                    "Replace with content, or move the item to assumptions/open issues."))

    cited = set(CITE.findall(text))
    unknown = sorted(cited - evidence_ids, key=_idnum)
    if unknown:
        f.append(_f(sid, "blocker", "L003", f"Cites evidence that does not exist: {', '.join(unknown)}.",
                    "Cite only provided evidence IDs, or state the claim as an assumption."))
    if len(cited & evidence_ids) < min_citations:
        f.append(_f(sid, "major", "L004",
                    f"Needs at least {min_citations} evidence citation(s); has {len(cited & evidence_ids)}.",
                    "Ground statements about existing systems in the provided evidence with <<EV-n>>."))

    if re.search(r"^```|^#{1,6}\s", text, re.M) or MD_LINK.search(text):
        f.append(_f(sid, "major", "L005", "Markdown syntax in AsciiDoc body.", "Use AsciiDoc syntax."))

    headings = [(len(m.group(1)) - 1, m.group(2).strip()) for m in
                (ADOC_HEADING.match(ln) for ln in _outside_blocks(text)) if m]
    have = {(_norm_title(t), lvl) for lvl, t in headings}
    for sub in sec.subsections:
        if (_norm_title(sub.title), sub.level) not in have:
            f.append(_f(sid, "major", "L006", f"Missing required sub-heading '{sub.heading_line}'.",
                        f"Add '{sub.heading_line}' with content."))
    too_high = [t for lvl, t in headings if lvl <= sec.level]
    if too_high:
        f.append(_f(sid, "major", "L009", f"Heading(s) at or above section level: {too_high}.",
                    f"Use level {sec.level + 1} or deeper ('{'=' * (sec.level + 2)} ...')."))

    if sec.diagram_required and not DIAGRAM_BLOCK.search(text):
        f.append(_f(sid, "major", "L007", f"Required {sec.diagram} diagram is missing.",
                    "Add a [mermaid] or [plantuml] diagram in a .... block."))
    for blk in re.finditer(r"^\[(mermaid|plantuml)[^\]]*\]\n\.{4,}\n(.*?)\n\.{4,}$", text, re.S | re.M):
        first = blk.group(2).strip().split("\n", 1)[0].strip()
        if not first.startswith(DIAGRAM_KEYWORDS):
            f.append(_f(sid, "major", "L010", f"Diagram block does not start with a known diagram type: '{first[:40]}'.",
                        "Start the block with e.g. 'flowchart LR', 'sequenceDiagram' or 'C4Container'."))

    bad_req = sorted(set(REQ_ID.findall(text)) - req_ids)
    if bad_req:
        f.append(_f(sid, "major", "L104", f"References unknown requirement IDs: {bad_req}.", "Use IDs from the brief only."))
    bad_dec = sorted(set(DEC_ID.findall(text)) - dec_ids)
    if bad_dec:
        f.append(_f(sid, "major", "L105", f"References decisions that are not accepted: {bad_dec}.",
                    "Reference accepted decisions only; rejected decisions must not shape the design."))
    return f


def _outside_blocks(text: str):
    open_d = None
    for ln in text.split("\n"):
        s = ln.strip()
        if open_d:
            if s == open_d:
                open_d = None
            continue
        if DELIM.match(s):
            open_d = s
            continue
        yield ln


def lint_document(template: HldTemplate, sections: dict[str, dict], brief: dict, decisions: list[dict]) -> list[dict]:
    """Cross-section rules. Coverage gaps are attributed to the template section that owns them, if any,
    so they trigger a targeted redraft instead of being only reported."""
    f: list[dict] = []
    all_text = "\n".join(s.get("body", "") for s in sections.values())
    mentioned = set(REQ_ID.findall(all_text))
    nfr_owner = template.by_role("nfr")
    req_owner = template.by_role("requirements")
    for r in brief.get("requirements", []):
        if r["id"] in mentioned:
            continue
        if r["kind"] == "non_functional":
            owner = nfr_owner.id if nfr_owner else "document"
            f.append(_f(owner, "major", "L102", f"{r['id']} ({r['text'][:60]}) is not addressed anywhere.",
                        f"Address {r['id']} explicitly, with how the design meets it."))
        else:
            owner = req_owner.id if req_owner else "document"
            f.append(_f(owner, "major", "L101", f"{r['id']} ({r['text'][:60]}) is not traced to any section.",
                        f"Reference {r['id']} where the design satisfies it."))
    dec_owner = template.by_role("decisions")
    for d in decisions:
        if d["status"] in ("accepted", "amended") and d["id"] not in all_text:
            f.append(_f(dec_owner.id if dec_owner else "document", "minor", "L103",
                        f"Accepted decision {d['id']} ({d['title']}) is never referenced.",
                        f"Reference {d['id']} where it shapes the design."))
    return f
