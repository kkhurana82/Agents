"""The HLD authoring graph.

  intake -> retrieve -> gap_analysis -> ask_architect* -> propose_decisions -> confirm_decisions*
         -> draft_sections -> review --(blocker/major & rounds left)--> draft_sections
                                     \\-> assemble
  (* = human interrupt; needs a checkpointer)

Design choices
- Decisions before prose: the architect confirms 3-8 decisions (cheap to correct) before any section is
  written (expensive to correct). Sections must not contradict accepted decisions; lint enforces references.
- Template is data: sections, outline and guidance come from the team's .adoc template.
- Grounding is checked, not hoped for: citations must resolve to the evidence pool (lint L003) and sections
  with relevant evidence must cite it (L004). The critic checks that citations support the claims.
- Only failing sections are redrafted; revision rounds are capped.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from . import prompts
from .adoc import lint_document, lint_section, normalize_body, refs
from .llm import LLM
from .models import CriticReport, DecisionSet, QuestionSet, RequirementBrief, SectionOutput
from .render import assemble
from .retrieval.base import ContextProvider, EvidencePool
from .template import HldTemplate, TemplateSection

log = logging.getLogger(__name__)


class HLDState(TypedDict, total=False):
    requirement: str
    story_id: str
    brief: dict
    evidence: dict[str, dict]
    section_evidence: dict[str, list[str]]
    shared_evidence: list[str]
    retrieval_warnings: list[str]
    questions: list[dict]
    clarifications: list[dict]
    decisions: list[dict]
    sections: dict[str, dict]
    critic_findings: dict[str, list[dict]]
    findings: list[dict]
    redraft: list[str]
    last_drafted: list[str]
    revision: int
    document: str
    review: dict


@dataclass
class Settings:
    max_questions: int = 5
    max_revisions: int = 2
    k_per_query: int = 5
    evidence_per_section: int = 6
    shared_evidence: int = 6
    snippet_chars: int = 700
    auto_approve_decisions: bool = False
    ask_questions: bool = True
    run_critic: bool = True
    redraft_on: tuple[str, ...] = ("blocker", "major")
    diagram_syntax: str = "mermaid"        # mermaid | plantuml (needs asciidoctor-diagram or Kroki to render)
    generator: str = "hld-agent"

    @classmethod
    def from_dict(cls, d: dict | None) -> "Settings":
        d = dict(d or {})
        if "redraft_on" in d:
            d["redraft_on"] = tuple(d["redraft_on"])
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


DIAGRAM_RULES = {
    "mermaid": "Diagrams: [mermaid] then a .... delimited block (asciidoctor-diagram), using C4Context/C4Container, "
               "flowchart or sequenceDiagram syntax.",
    "plantuml": "Diagrams: [plantuml] then a .... delimited block (asciidoctor-diagram), starting @startuml and "
                "ending @enduml; C4-PlantUML macros are allowed.",
}


def _j(obj) -> str:
    return json.dumps(obj, indent=1, ensure_ascii=False)


def _evidence_block(ids: list[str], pool: dict, chars: int) -> str:
    if not ids:
        return "(no evidence retrieved for this section)"
    parts = []
    for eid in ids:
        e = pool[eid]
        rev = f" @ {e['revision']}" if e.get("revision") else ""
        parts.append(f"[{eid}] ({e['kind']}, {e['source']}) {e['title']} - {e['uri']}{rev}\n{e['snippet'][:chars]}")
    return "\n\n".join(parts)


def _brief_compact(brief: dict) -> str:
    keep = {k: brief[k] for k in ("title", "summary", "business_goals", "in_scope", "out_of_scope", "actors",
                                  "requirements", "assumptions") if k in brief}
    return _j(keep)


def build_graph(*, llm: LLM, template: HldTemplate, providers: list[ContextProvider],
                settings: Settings | None = None, checkpointer=None):
    S = settings or Settings()
    gen_sections = template.generate_sections

    # ------------------------------------------------------------------ intake
    def intake(state: HLDState) -> dict:
        brief = llm.structured(RequirementBrief, prompts.INTAKE,
                               f"Story: {state.get('story_id') or 'n/a'}\n\nRequirement:\n{state['requirement']}",
                               task="intake", ctx={"requirement": state["requirement"]})
        log.info("intake: %d requirements, %d unknowns", len(brief.requirements), len(brief.unknowns))
        return {"brief": brief.model_dump(), "revision": 0}

    # ---------------------------------------------------------------- retrieve
    def retrieve(state: HLDState) -> dict:
        brief = state["brief"]
        pool = EvidencePool(state.get("evidence"))
        warnings: list[str] = []
        shared_q = brief.get("search_queries", [])[:10] or [brief["title"]]
        sec_q = [f"{brief['title']} {s.title} {' '.join(s.guidance.split()[:25])}".strip() for s in gen_sections]
        queries = shared_q + sec_q

        merged: list[list[tuple[str, float]]] = [[] for _ in queries]
        for prov in providers:
            try:
                results = prov.search_many(queries, S.k_per_query)
            except Exception as exc:  # degrade, but make it visible in the review report
                msg = f"retrieval provider '{getattr(prov, 'name', prov)}' failed: {exc}"
                log.warning(msg)
                warnings.append(msg)
                continue
            for qi, hits in enumerate(results):
                merged[qi] += [(pool.add(h), h.score) for h in hits]

        def top(pairs, n, kinds=()):
            best: dict[str, float] = {}
            for eid, sc in pairs:
                if kinds and pool.get(eid)["kind"] not in kinds:
                    sc *= 0.5
                best[eid] = max(best.get(eid, 0), sc)
            return [e for e, _ in sorted(best.items(), key=lambda x: -x[1])][:n]

        shared = top([p for qi in range(len(shared_q)) for p in merged[qi]], S.shared_evidence)
        per_sec = {s.id: top(merged[len(shared_q) + i], S.evidence_per_section, tuple(s.evidence_kinds))
                   for i, s in enumerate(gen_sections)}
        log.info("retrieve: %d evidence items from %d provider(s)", len(pool.items), len(providers))
        return {"evidence": pool.items, "shared_evidence": shared, "section_evidence": per_sec,
                "retrieval_warnings": warnings}

    # ------------------------------------------------------------ gap analysis
    def gap_analysis(state: HLDState) -> dict:
        if not S.ask_questions:
            return {"questions": []}
        sec_list = "\n".join(f"- {s.id}: {s.title}" for s in gen_sections)
        user = (f"## Brief\n{_brief_compact(state['brief'])}\n\n## Unknowns from intake\n"
                f"{_j(state['brief'].get('unknowns', []))}\n\n## Template sections\n{sec_list}\n\n"
                f"## Evidence already available\n"
                f"{_evidence_block(state['shared_evidence'], state['evidence'], 300)}")
        qs = llm.structured(QuestionSet, prompts.GAP.format(max_questions=S.max_questions), user,
                            task="gap", ctx={"brief": state["brief"]})
        questions = [q.model_dump() for q in qs.questions[:S.max_questions]]
        for n, q in enumerate(questions, 1):
            q["id"] = f"Q-{n}"
        return {"questions": questions}

    # ----------------------------------------------------- human: questions
    def ask_architect(state: HLDState) -> dict:
        questions = state.get("questions", [])
        if not questions:
            return {"clarifications": []}
        # Resume payload: {"answers": {"Q-1": "...", ...}}. Always an envelope: LangGraph ignores an empty resume value.
        resp = interrupt({"type": "questions", "questions": questions}) or {}
        answers = resp.get("answers", resp) if isinstance(resp, dict) else {}
        clar = []
        for q in questions:
            a = (answers.get(q["id"]) or "").strip()
            clar.append({"id": q["id"], "question": q["question"],
                         "answer": a or q["default_assumption"], "source": "architect" if a else "default"})
        return {"clarifications": clar}

    # ---------------------------------------------------------------- decisions
    def propose_decisions(state: HLDState) -> dict:
        ev_ids = list(dict.fromkeys(state["shared_evidence"] + [e for ids in state["section_evidence"].values() for e in ids]))
        user = (f"## Brief\n{_brief_compact(state['brief'])}\n\n## Architect clarifications\n"
                f"{_j(state.get('clarifications', []))}\n\n## Evidence\n"
                f"{_evidence_block(ev_ids[:14], state['evidence'], S.snippet_chars)}")
        ds = llm.structured(DecisionSet, prompts.DECISIONS, user, task="decisions",
                            ctx={"brief": state["brief"], "evidence_ids": ev_ids,
                                 "clarifications": state.get("clarifications", [])})
        decisions = []
        for n, d in enumerate(ds.decisions, 1):
            dd = d.model_dump()
            dd["id"], dd["status"] = f"DEC-{n}", "proposed"
            dd["evidence_ids"] = [e for e in dd["evidence_ids"] if e in state["evidence"]]
            decisions.append(dd)
        return {"decisions": decisions}

    # ----------------------------------------------------- human: decisions
    def confirm_decisions(state: HLDState) -> dict:
        decisions = [dict(d) for d in state["decisions"]]
        if S.auto_approve_decisions:
            resp = {"approve_all": True}
        else:
            resp = interrupt({"type": "decisions", "decisions": decisions}) or {}
        if not isinstance(resp, dict):
            resp = {}
        per = resp.get("decisions", {}) if isinstance(resp, dict) else {}
        for d in decisions:
            r = per.get(d["id"], "accept")
            if resp.get("approve_all") or r in ("accept", "accepted", None):
                d["status"] = "accepted"
            elif r in ("reject", "rejected"):
                d["status"] = "rejected"
            elif isinstance(r, dict):
                d.update({k: v for k, v in r.items() if k in ("choice", "rationale", "title", "consequences")})
                d["status"] = "amended"
        return {"decisions": decisions}

    # ------------------------------------------------------------- drafting
    def draft_sections(state: HLDState) -> dict:
        redraft = state.get("redraft") or []
        revision = state.get("revision", 0) + (1 if redraft else 0)
        targets = [s for s in gen_sections if not redraft or s.id in redraft]
        sections = dict(state.get("sections", {}))
        accepted = [d for d in state["decisions"] if d["status"] in ("accepted", "amended")]
        findings_by_sec: dict[str, list[dict]] = {}
        for fnd in state.get("findings", []):
            findings_by_sec.setdefault(fnd["section_id"], []).append(fnd)

        for sec in targets:
            sections[sec.id] = _draft_one(state, sec, sections, accepted, findings_by_sec.get(sec.id, []), revision)
            log.info("draft[r%d]: %s", revision, sec.id)
        return {"sections": sections, "revision": revision, "last_drafted": [s.id for s in targets], "redraft": []}

    def _min_citations(state: HLDState, sec: TemplateSection) -> int:
        if sec.min_citations is not None:
            return sec.min_citations
        return 1 if sec.grounded and state["section_evidence"].get(sec.id) else 0

    def _draft_one(state, sec: TemplateSection, sections, accepted, findings, revision) -> dict:
        ev_ids = list(dict.fromkeys(state["section_evidence"].get(sec.id, []) + state["shared_evidence"]))
        ev_ids += [e for d in accepted for e in d.get("evidence_ids", []) if e not in ev_ids]
        outline = "\n".join(f"{s.heading_line}\n  guidance: {s.guidance or '-'}" for s in sec.subsections) or "(none)"
        diagram = ""
        if sec.diagram:
            diagram = (f"{'REQUIRED' if sec.diagram_required else 'Recommended'}: a {sec.diagram} diagram as a "
                       f"[{S.diagram_syntax}] block.")
        others = "\n".join(f"- {sid}: {s['body'][:350].replace(chr(10), ' ')}"
                           for sid, s in sections.items() if sid != sec.id) or "(none yet)"
        so_far = [a for s in sections.values() for a in s.get("assumptions", []) + s.get("open_issues", [])]
        prev = sections.get(sec.id, {}).get("body") if findings else None
        user = "\n\n".join(filter(None, [
            f"## Requirement brief\n{_brief_compact(state['brief'])}",
            f"## Architect clarifications\n{_j(state.get('clarifications', []))}",
            f"## Accepted decisions\n{_j(accepted)}",
            f"## Section to write\nTitle: {sec.title}\nSection heading level: {'=' * (sec.level + 1)} "
            f"(written by the system; sub-headings use {'=' * (sec.level + 2)})\n"
            f"Template guidance:\n{sec.guidance or '(none)'}\n\nRequired sub-headings, in order:\n{outline}\n"
            f"{diagram}\nReviewer checks:\n" + ("\n".join(f"- {c}" for c in sec.checks) or "- (none)") +
            f"\nMinimum evidence citations: {_min_citations(state, sec)}",
            f"## Evidence you may cite (as <<EV-n>>)\n{_evidence_block(ev_ids, state['evidence'], S.snippet_chars)}",
            f"## Other sections so far (summaries, keep consistent)\n{others}",
            f"## Assumptions and open issues raised so far\n{_j(so_far)}" if so_far else "",
            f"## Reviewer findings to fix\n{_j(findings)}" if findings else "",
            f"## Your previous draft (revise it; keep what is correct)\n{prev}" if prev else "",
        ]))
        out = llm.structured(SectionOutput, prompts.DRAFT.replace("{diagram_rule}", DIAGRAM_RULES[S.diagram_syntax]),
                             user, task="draft",
                             ctx={"section": sec.to_ctx(), "evidence_ids": ev_ids, "brief": state["brief"],
                                  "decisions": accepted, "findings": findings, "revision": revision,
                                  "previous_body": prev})
        body = normalize_body(out.body, sec)
        return {"body": body, "assumptions": out.assumptions, "open_issues": out.open_issues,
                "refs": refs(body), "revision": revision}

    # ---------------------------------------------------------------- review
    def review(state: HLDState) -> dict:
        pool_ids = set(state["evidence"])
        req_ids = {r["id"] for r in state["brief"]["requirements"]}
        dec_ids = {d["id"] for d in state["decisions"] if d["status"] in ("accepted", "amended")}
        sections = state["sections"]

        lint: list[dict] = []
        for sec in gen_sections:
            lint += lint_section(sec, sections.get(sec.id, {}).get("body", ""), evidence_ids=pool_ids,
                                 req_ids=req_ids, dec_ids=dec_ids, min_citations=_min_citations(state, sec))
        lint += lint_document(template, sections, state["brief"], state["decisions"])

        critic = dict(state.get("critic_findings", {}))
        if S.run_critic:
            accepted = [d for d in state["decisions"] if d["status"] in ("accepted", "amended")]
            for sid in state.get("last_drafted", []):
                sec = template.section(sid)
                body = sections[sid]["body"]
                cited = sections[sid]["refs"]["evidence"]
                summaries = "\n".join(f"- {o}: {s['body'][:250].replace(chr(10), ' ')}"
                                      for o, s in sections.items() if o != sid)
                user = (f"## Section: {sec.title} (id: {sid})\nTemplate guidance:\n{sec.guidance or '-'}\n"
                        f"Reviewer checks:\n" + ("\n".join(f"- {c}" for c in sec.checks) or "- (none)") +
                        f"\n\n## Requirements\n{_j(state['brief']['requirements'])}\n\n## Accepted decisions\n"
                        f"{_j(accepted)}\n\n## Evidence cited in this section\n"
                        f"{_evidence_block([c for c in cited if c in pool_ids], state['evidence'], S.snippet_chars)}\n\n"
                        f"## Other sections (summaries)\n{summaries}\n\n## Section text\n{body}")
                rep = llm.structured(CriticReport, prompts.CRITIC, user, task="critic",
                                     ctx={"section_id": sid, "body": body, "revision": state.get("revision", 0)})
                critic[sid] = [dict(f.model_dump(), section_id=sid, rule="critic") for f in rep.findings]

        findings = lint + [f for fs in critic.values() for f in fs]
        redraft = sorted({f["section_id"] for f in findings
                          if f["severity"] in S.redraft_on and f["section_id"] != "document"})
        log.info("review[r%d]: %d findings, redraft=%s", state.get("revision", 0), len(findings), redraft)
        return {"findings": findings, "critic_findings": critic, "redraft": redraft}

    def route_after_review(state: HLDState) -> str:
        if state.get("redraft") and state.get("revision", 0) < S.max_revisions:
            return "draft_sections"
        return "finalize"

    # -------------------------------------------------------------- finalize
    def finalize(state: HLDState) -> dict:
        doc = assemble(template, state, generator=S.generator)
        order = {"blocker": 0, "major": 1, "minor": 2}
        remaining = sorted(state.get("findings", []), key=lambda f: (order[f["severity"]], f["section_id"]))
        cited = set(refs(doc)["evidence"]) & set(state["evidence"])
        reqs = state["brief"]["requirements"]
        covered = {r for s in state["sections"].values() for r in s["refs"]["requirements"]}
        review_rep = {
            "status": "needs_attention" if any(f["severity"] in ("blocker", "major") for f in remaining) else "ready_for_review",
            "revision_rounds": state.get("revision", 0),
            "sections_drafted": len(state["sections"]),
            "evidence_retrieved": len(state["evidence"]),
            "evidence_cited": len(cited),
            "requirements_covered": f"{len(covered & {r['id'] for r in reqs})}/{len(reqs)}",
            "decisions": {d["id"]: d["status"] for d in state["decisions"]},
            "retrieval_warnings": state.get("retrieval_warnings", []),
            "findings": remaining,
        }
        return {"document": doc, "review": review_rep}

    g = StateGraph(HLDState)
    for name, fn in [("intake", intake), ("retrieve", retrieve), ("gap_analysis", gap_analysis),
                     ("ask_architect", ask_architect), ("propose_decisions", propose_decisions),
                     ("confirm_decisions", confirm_decisions), ("draft_sections", draft_sections),
                     ("review", review), ("finalize", finalize)]:
        g.add_node(name, fn)
    g.add_edge(START, "intake")
    g.add_edge("intake", "retrieve")
    g.add_edge("retrieve", "gap_analysis")
    g.add_edge("gap_analysis", "ask_architect")
    g.add_edge("ask_architect", "propose_decisions")
    g.add_edge("propose_decisions", "confirm_decisions")
    g.add_edge("confirm_decisions", "draft_sections")
    g.add_edge("draft_sections", "review")
    g.add_conditional_edges("review", route_after_review, {"draft_sections": "draft_sections", "finalize": "finalize"})
    g.add_edge("finalize", END)
    return g.compile(checkpointer=checkpointer)
