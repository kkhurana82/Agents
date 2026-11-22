"""Scripted, deterministic stand-in for the LLM so the whole graph runs offline (tests, demos, CI).

It builds outputs from `ctx`, not from understanding. It deliberately injects two realistic faults in the
first drafting round so the safety nets are exercised:
  * a Markdown ``` mermaid fence  -> fixed by the AsciiDoc normaliser (no LLM round spent)
  * a hallucinated citation <<EV-99>> in the sequence-diagram section -> lint L003 blocker -> targeted redraft
"""
from __future__ import annotations

import re

from ..models import (CriticReport, Decision, DecisionSet, Finding, Question, QuestionSet, Requirement,
                      RequirementBrief, SectionOutput)

DIAGRAMS = {
    "context": ["C4Context", '  Person(agent, "Actor")', '  System(sys, "New capability")',
                '  System_Ext(ext, "Existing system")', '  Rel(agent, sys, "uses")', '  Rel(sys, ext, "calls")'],
    "container": ["flowchart LR", "  UI[Channel] --> API[Capability API]", "  API --> SVC[Domain service]",
                  "  SVC --> DB[(Data store)]", "  SVC --> EXT[Existing system]"],
    "sequence": ["sequenceDiagram", "  participant C as Channel", "  participant S as Capability service",
                 "  participant E as Existing system", "  C->>S: request", "  S->>E: query", "  E-->>S: result",
                 "  S-->>C: response"],
    "deployment": ["flowchart TB", "  subgraph GKE[Kubernetes cluster]", "    SVC[Capability service x3]",
                   "  end", "  SVC --> DB[(Managed database)]"],
}


class ScriptedLLM:
    def __init__(self):
        self.calls: list[str] = []

    def structured(self, schema, system, user, *, task, ctx=None):
        self.calls.append(task)
        ctx = ctx or {}
        return getattr(self, f"_{task}")(ctx)

    # ------------------------------------------------------------------ intake
    def _intake(self, ctx) -> RequirementBrief:
        text = ctx["requirement"]
        lines = text.splitlines()
        title = next((re.sub(r"^#+\s*|^=+\s*", "", ln).strip() for ln in lines if ln.strip()), "Untitled")
        buckets: dict[str, list[str]] = {}
        current = "summary"
        for ln in lines[1:]:
            if m := re.match(r"^(#{2,}|={2,})\s+(.*)", ln):
                current = m.group(2).strip().lower()
                continue
            if m := re.match(r"^\s*[-*]\s+(.*)", ln):
                buckets.setdefault(current, []).append(m.group(1).strip())
            elif ln.strip():
                buckets.setdefault(current + ":text", []).append(ln.strip())

        def pick(*keys):
            return next((buckets[k] for k in buckets if any(x in k for x in keys) and not k.endswith(":text")), [])

        reqs, n_fr, n_nfr, n_con = [], 0, 0, 0
        for t in pick("non-functional", "nfr", "quality"):
            n_nfr += 1
            tgt = re.search(r"(p\d{2}\s*[\d.]+\s*(ms|s)\b|\d+(\.\d+)?\s*%|\d+\s*(ms|tps|rps)\b)", t, re.I)
            reqs.append(Requirement(id=f"NFR-{n_nfr}", kind="non_functional", text=t,
                                    measurable_target=tgt.group(0).strip() if tgt else None))
        for k in buckets:
            if "functional" in k and "non" not in k and not k.endswith(":text"):
                for t in buckets[k]:
                    n_fr += 1
                    reqs.append(Requirement(id=f"FR-{n_fr}", kind="functional", text=t))
        for t in pick("constraint"):
            n_con += 1
            reqs.append(Requirement(id=f"CON-{n_con}", kind="constraint", text=t))
        words = [w for w in re.findall(r"[A-Za-z][\w-]+", title) if len(w) > 3]
        return RequirementBrief(
            title=title,
            summary=" ".join(buckets.get("summary:text", []) + buckets.get("context:text", []))[:600] or title,
            business_goals=pick("goal", "objective"), in_scope=pick("in scope", "scope"),
            out_of_scope=pick("out of scope"), actors=pick("actor", "user") or ["End user"],
            requirements=sorted(reqs, key=lambda r: (r.kind != "functional", r.id)),
            assumptions=[], unknowns=[f"No measurable target stated for {r.id}" for r in reqs
                                      if r.kind == "non_functional" and not r.measurable_target],
            search_queries=[title, *words[:4], *[r.text[:60] for r in reqs if r.kind == "functional"][:3]],
        )

    # --------------------------------------------------------------------- gap
    def _gap(self, ctx) -> QuestionSet:
        return QuestionSet(questions=[
            Question(id="Q-1", question="Must the new capability read inventory synchronously from the system of "
                                        "record, or is a cached read model acceptable for display paths?",
                     why_it_matters="Decides between a synchronous call chain and an event-fed read model.",
                     blocking=False, affects_sections=["solution-architecture", "data-architecture"],
                     default_assumption="Cached read model for display; synchronous check at commit time."),
            Question(id="Q-2", question="Is a phased rollout per carrier required, or a single cut-over?",
                     why_it_matters="Determines feature-flag design and the migration plan.",
                     blocking=False, affects_sections=["migration-and-rollout"],
                     default_assumption="Phased rollout per carrier behind a feature flag."),
        ])

    # --------------------------------------------------------------- decisions
    def _decisions(self, ctx) -> DecisionSet:
        ev = ctx.get("evidence_ids", [])
        req = [r["id"] for r in ctx["brief"]["requirements"]]
        nfr = [r for r in req if r.startswith("NFR")]
        return DecisionSet(decisions=[
            Decision(id="DEC-1", title="Reuse the existing domain service instead of a new store",
                     context="Evidence shows an existing service already owns this data.",
                     options=["Reuse existing service API", "New dedicated data store"],
                     choice="Reuse existing service API",
                     rationale=f"Avoids dual writes; satisfies {req[0] if req else 'FR-1'} with less change.",
                     consequences=["Dependency on existing service availability"], evidence_ids=ev[:2]),
            Decision(id="DEC-2", title="Event-fed read model for display paths",
                     context="Display traffic is read-heavy; commit path needs strong consistency.",
                     options=["Synchronous reads everywhere", "CQRS read model fed by events"],
                     choice="CQRS read model fed by events, synchronous validation at commit",
                     rationale=f"Meets {nfr[0] if nfr else 'NFR-1'} without loading the system of record.",
                     consequences=["Eventual consistency on display paths", "Needs replay on consumer lag"],
                     evidence_ids=ev[2:3]),
            Decision(id="DEC-3", title="Introduce a new message broker",
                     context="Events need transport.", options=["Use the existing platform broker", "New broker"],
                     choice="New broker", rationale="Isolation.", consequences=["Extra operational cost"],
                     evidence_ids=[]),
        ])

    # ------------------------------------------------------------------- draft
    def _draft(self, ctx) -> SectionOutput:
        sec, brief, rev = ctx["section"], ctx["brief"], ctx.get("revision", 0)
        ev = ctx.get("evidence_ids", [])
        decs = [d["id"] for d in ctx.get("decisions", [])]
        reqs = brief["requirements"]
        frs = [r for r in reqs if r["kind"] == "functional"]
        nfrs = [r for r in reqs if r["kind"] == "non_functional"]
        cite = f" <<{ev[0]}>>" if ev else ""
        lines: list[str] = []

        def para(topic: str):
            lines.append(f"This part covers {topic.lower()} for {brief['title']}. It builds on the existing "
                         f"platform capability{cite}" + (f" and applies {decs[0]}." if decs else "."))
            lines.append("")

        def req_table(rs):
            lines.extend(['[cols="1,5",options="header"]', "|===", "|ID |Requirement"])
            lines.extend(f"|{r['id']} |{r['text']}" for r in rs)
            lines.extend(["|===", ""])

        role, title = sec.get("role"), sec["title"].lower()
        subs = sec.get("subsections") or []
        if not subs:
            para(sec["title"])
        for h in subs:
            lines += [h, ""]
            t = h.lower()
            if "non-functional" in t or "non functional" in t:
                req_table(nfrs)
            elif "functional" in t:
                req_table(frs + [r for r in reqs if r["kind"] == "constraint"])
            elif "decision" in t and decs:
                lines += [f"* {d}: see the decision log." for d in decs] + [""]
            else:
                para(h.lstrip("= "))

        if role == "nfr" or "non-functional" in title:
            lines += ['[cols="1,4",options="header"]', "|===", "|NFR |How the design meets it"]
            lines += [f"|{r['id']} |Addressed by horizontal scaling and the read model{cite}." for r in nfrs]
            lines += ["|===", ""]
        if role == "decisions" and not any("decision" in h.lower() for h in subs):
            lines += [f"* {d}" for d in decs] + [""]
        if sec.get("diagram"):
            body = DIAGRAMS.get(sec["diagram"], DIAGRAMS["container"])
            lines += ["```mermaid", *body, "```", ""] if rev == 0 else ["[mermaid]", "....", *body, "....", ""]
        if sec.get("diagram") == "sequence" and rev == 0:
            lines.append("Retries follow the platform resilience standard <<EV-99>>.")   # hallucinated citation
        if frs and "solution" in title:
            lines.append(f"The flow satisfies {', '.join(r['id'] for r in frs)}.")
        # act on reviewer findings the way a compliant model would
        for f in ctx.get("findings") or []:
            if f["rule"] == "L004" and ev:
                lines.append(f"This relies on the existing implementation <<{ev[0]}>>.")
            elif f["rule"] in ("L101", "L102"):
                ids = re.findall(r"\b(?:FR|NFR|CON)-\d+\b", f["issue"])
                lines.append(f"The design addresses {', '.join(ids)} as described above.")
        return SectionOutput(body="\n".join(lines),
                             assumptions=[f"Volumes for {sec['title']} assumed similar to current peak."]
                             if role == "nfr" else [],
                             open_issues=["Confirm rollout order with carrier operations."]
                             if "rollout" in title else [])

    # ------------------------------------------------------------------ critic
    def _critic(self, ctx) -> CriticReport:
        if ctx["section_id"] == "security" and ctx.get("revision", 0) == 0:
            return CriticReport(findings=[Finding(section_id="security", severity="minor", rule="critic",
                                                  issue="Token lifetime for service-to-service calls not stated.",
                                                  fix="State the token lifetime or cite the IAM standard.")])
        return CriticReport(findings=[])
