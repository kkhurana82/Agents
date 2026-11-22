"""Parse an AsciiDoc HLD template into draftable sections.

The template stays the team's own .adoc file. The parser reads:
  * the document header (= Title + :attributes:) -> kept, title rewritten
  * each level-1 section (== Title) -> one drafting unit
  * nested headings (=== / ====) -> required outline the draft must reproduce
  * body text, // comments and //// comment blocks under a heading -> drafting guidance
  * block attribute / anchor lines just above a heading ([[id]], [#id], [appendix]) -> preserved verbatim

Optional agent hints, as AsciiDoc comments (invisible when rendered):
  // hld: mode=manual            keep this section verbatim (revision history, approvals ...)
  // hld: diagram=container      require a diagram (context|container|sequence|deployment|none)
  // hld: min_citations=1        minimum <<EV-n>> citations
  // hld: evidence=adr|standard  evidence kinds preferred for this section
  // hld: role=nfr               section that must cover every NFR (also: decisions, open_issues, requirements)
  // hld: grounded=true          section describes existing systems: must cite retrieved evidence
  // hld-check: <text>           a reviewer check the critic applies to this section
Without hints, sensible defaults are inferred from the section title.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

HEADING_RE = re.compile(r"^(={1,6})\s+(\S.*?)\s*$")
DELIM_RE = re.compile(r"^(-{4,}|\.{4,}|={4,}|\*{4,}|_{4,}|\+{4,}|/{4,}|\|={3,}|`{3})$")
BLOCK_ATTR_RE = re.compile(r"^\[.*\]$")
HINT_RE = re.compile(r"^//\s*hld:\s*(.+)$", re.I)
CHECK_RE = re.compile(r"^//\s*hld-check:\s*(.+)$", re.I)
ANCHOR_ID_RE = re.compile(r"^\[\[([A-Za-z_][\w\-.]*)(?:,[^\]]*)?\]\]$|^\[#([A-Za-z_][\w\-.]*)[^\]]*\]$")
NUMBER_PREFIX_RE = re.compile(r"^(\d+(\.\d+)*\.?|[A-Z]\.)\s+")

MANUAL_TITLE_RE = re.compile(
    r"revision|change\s*history|version\s*history|document\s*control|approv|sign[\s-]?off|"
    r"distribution|reviewers?\b|table\s+of\s+contents|references?$",
    re.I,
)
DIAGRAM_TITLE_HINTS = [
    (re.compile(r"system\s+context|context\s+(view|diagram)", re.I), "context"),
    (re.compile(r"deploy|infrastructure|topology|environment", re.I), "deployment"),
    (re.compile(r"sequence|interaction|flow|integration|interface", re.I), "sequence"),
    (re.compile(r"component|container|solution\s+architecture|logical\s+architecture|architecture\s+overview", re.I), "container"),
]
# Sections that describe existing systems must cite evidence when relevant evidence was retrieved.
GROUNDED_TITLE_RE = re.compile(
    r"current\s+state|as[\s-]?is|existing|integration|interface|dependenc|impact|data\s+(architecture|model)|"
    r"solution\s+architecture|component|deployment|migration", re.I)
ROLE_TITLE_HINTS = [
    (re.compile(r"non[\s-]?functional|quality\s+attribute|\bnfr", re.I), "nfr"),
    (re.compile(r"decision", re.I), "decisions"),
    (re.compile(r"open\s+issue|assumption", re.I), "open_issues"),
    (re.compile(r"requirement", re.I), "requirements"),
]


@dataclass
class SubHeading:
    level: int
    title: str
    guidance: str
    pre_lines: list[str] = field(default_factory=list)

    @property
    def heading_line(self) -> str:
        return f"{'=' * (self.level + 1)} {self.title}"


@dataclass
class TemplateSection:
    id: str
    title: str
    level: int
    heading_line: str
    pre_lines: list[str]
    guidance: str
    subsections: list[SubHeading]
    raw_body: str                      # everything under the heading, verbatim (used for manual sections)
    mode: str = "generate"             # generate | manual
    diagram: str | None = None
    diagram_required: bool = False
    min_citations: int | None = None   # None = adaptive (see `grounded`)
    grounded: bool = False             # describes existing systems -> must cite retrieved evidence
    evidence_kinds: list[str] = field(default_factory=list)
    role: str | None = None
    checks: list[str] = field(default_factory=list)

    def to_ctx(self) -> dict:
        return {
            "id": self.id, "title": self.title, "level": self.level, "mode": self.mode,
            "diagram": self.diagram, "diagram_required": self.diagram_required,
            "min_citations": self.min_citations, "role": self.role,
            "subsections": [s.heading_line for s in self.subsections],
        }


@dataclass
class HldTemplate:
    path: str
    header_lines: list[str]
    preamble: str
    sections: list[TemplateSection]

    @property
    def generate_sections(self) -> list[TemplateSection]:
        return [s for s in self.sections if s.mode == "generate"]

    def section(self, sid: str) -> TemplateSection:
        for s in self.sections:
            if s.id == sid:
                return s
        raise KeyError(sid)

    def by_role(self, role: str) -> TemplateSection | None:
        return next((s for s in self.generate_sections if s.role == role), None)


def slugify(title: str) -> str:
    t = NUMBER_PREFIX_RE.sub("", title).lower()
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    return t or "section"


def _clean_guidance(lines: list[str]) -> tuple[str, dict, list[str]]:
    """Return (guidance text, hints, checks). Comments become guidance text; hints are removed."""
    hints: dict[str, str] = {}
    checks: list[str] = []
    out: list[str] = []
    for ln in lines:
        s = ln.strip()
        if m := HINT_RE.match(s):
            for part in re.split(r"[,\s]+", m.group(1).strip()):
                if "=" in part:
                    k, v = part.split("=", 1)
                    hints[k.strip().lower()] = v.strip()
                elif part:
                    hints[part.lower()] = "true"
            continue
        if m := CHECK_RE.match(s):
            checks.append(m.group(1).strip())
            continue
        if re.fullmatch(r"/{4,}", s):
            continue
        if s.startswith("//"):
            s = s[2:].strip()
        out.append(s)
    text = "\n".join(out).strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text, hints, checks


def _split_trailing_attrs(buf: list[str]) -> list[str]:
    """Pop block-attribute/anchor lines that sit directly above a heading (they belong to it)."""
    pre: list[str] = []
    while buf and BLOCK_ATTR_RE.match(buf[-1].strip()) and buf[-1].strip():
        pre.insert(0, buf.pop())
    return pre


def parse_template(path: str | Path) -> HldTemplate:
    text = Path(path).read_text(encoding="utf-8")
    lines = text.splitlines()

    # --- document header: up to first blank line after the "= Title" line ---
    header: list[str] = []
    i = 0
    while i < len(lines) and (not lines[i].strip() or lines[i].lstrip().startswith("//")) and not header:
        i += 1
    if i < len(lines) and re.match(r"^=\s+\S", lines[i]):
        while i < len(lines) and lines[i].strip():
            header.append(lines[i])
            i += 1

    # --- walk body, tracking delimited blocks so headings inside listings are ignored ---
    nodes: list[dict] = []          # {"level", "title", "pre", "body": [..]}
    preamble: list[str] = []
    current = preamble
    open_delim: str | None = None
    for ln in lines[i:]:
        s = ln.rstrip()
        if open_delim:
            current.append(s)
            if s == open_delim:
                open_delim = None
            continue
        if DELIM_RE.match(s) or s.startswith("```"):
            open_delim = "```" if s.startswith("```") else s
            current.append(s)
            continue
        m = HEADING_RE.match(s)
        if m and len(m.group(1)) >= 2:
            pre = _split_trailing_attrs(current)
            node = {"level": len(m.group(1)) - 1, "title": m.group(2), "pre": pre, "body": []}
            nodes.append(node)
            current = node["body"]
            continue
        current.append(s)
    if open_delim:
        raise ValueError(f"{path}: unterminated delimited block '{open_delim}'")

    # --- group into level-1 sections; deeper headings become the outline ---
    sections: list[TemplateSection] = []
    seen_ids: set[str] = set()
    idx = 0
    while idx < len(nodes):
        top = nodes[idx]
        if top["level"] != 1:
            raise ValueError(f"{path}: heading '{top['title']}' appears before any level-1 (==) section")
        children = []
        j = idx + 1
        while j < len(nodes) and nodes[j]["level"] > 1:
            children.append(nodes[j])
            j += 1

        guidance, hints, checks = _clean_guidance(top["body"])
        subs: list[SubHeading] = []
        for ch in children:
            g, h, c = _clean_guidance(ch["body"])
            checks.extend(c)
            for k, v in h.items():
                hints.setdefault(k, v)
            subs.append(SubHeading(level=ch["level"], title=ch["title"], guidance=g, pre_lines=ch["pre"]))

        raw_parts = top["body"][:]
        for ch in children:
            raw_parts += ch["pre"] + [f"{'=' * (ch['level'] + 1)} {ch['title']}"] + ch["body"]
        raw_body = "\n".join(ln for ln in raw_parts
                             if not (HINT_RE.match(ln.strip()) or CHECK_RE.match(ln.strip()))).strip("\n")

        sid = None
        for p in top["pre"]:
            if am := ANCHOR_ID_RE.match(p.strip()):
                sid = am.group(1) or am.group(2)
        sid = sid or slugify(top["title"])
        base, n = sid, 2
        while sid in seen_ids:
            sid, n = f"{base}-{n}", n + 1
        seen_ids.add(sid)

        sec = TemplateSection(
            id=sid, title=top["title"], level=1, heading_line=f"== {top['title']}",
            pre_lines=top["pre"], guidance=guidance, subsections=subs, raw_body=raw_body, checks=checks,
        )
        _apply_defaults_and_hints(sec, hints)
        sections.append(sec)
        idx = j

    if not sections:
        raise ValueError(f"{path}: no level-1 (==) sections found")
    return HldTemplate(path=str(path), header_lines=header, preamble="\n".join(preamble).strip(), sections=sections)


def _apply_defaults_and_hints(sec: TemplateSection, hints: dict) -> None:
    title = NUMBER_PREFIX_RE.sub("", sec.title)
    if MANUAL_TITLE_RE.search(title):
        sec.mode = "manual"
    for rx, kind in DIAGRAM_TITLE_HINTS:
        if rx.search(title):
            sec.diagram = kind
            break
    sec.grounded = bool(GROUNDED_TITLE_RE.search(title))
    for rx, role in ROLE_TITLE_HINTS:
        if rx.search(title):
            sec.role = role
            break

    mode = hints.get("mode") or ("manual" if "skip" in hints or "manual" in hints else None)
    if mode in ("manual", "skip"):
        sec.mode = "manual"
    elif mode == "generate":
        sec.mode = "generate"
    if "diagram" in hints:
        d = hints["diagram"].lower()
        sec.diagram = None if d in ("none", "false", "no") else d
        sec.diagram_required = sec.diagram is not None
    if "min_citations" in hints:
        sec.min_citations = int(hints["min_citations"])
    if "evidence" in hints:
        sec.evidence_kinds = [k for k in re.split(r"[;|/]", hints["evidence"]) if k]
    if "role" in hints:
        sec.role = hints["role"].lower()
    if "grounded" in hints:
        sec.grounded = hints["grounded"].lower() not in ("false", "no", "0")
