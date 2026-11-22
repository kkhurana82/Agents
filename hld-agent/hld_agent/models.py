"""Structured outputs exchanged with the LLM and kept in graph state.

State holds plain dicts (model_dump) so any LangGraph checkpointer can serialise it;
nodes re-hydrate into these models when they need validation.

ID conventions (all referenced verbatim in the AsciiDoc body and checked by lint):
  FR-n / NFR-n / CON-n  requirements      DEC-n  design decisions
  Q-n                   architect questions  EV-n   evidence (cited as <<EV-n>>)
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


# ---------- intake ----------
class Requirement(BaseModel):
    id: str = Field(description="FR-n, NFR-n or CON-n")
    kind: Literal["functional", "non_functional", "constraint"]
    text: str
    category: str | None = Field(None, description="NFR category: performance, availability, security, ...")
    measurable_target: str | None = Field(None, description="Only if stated in the requirement; never invent")


class RequirementBrief(BaseModel):
    title: str
    summary: str
    business_goals: list[str]
    in_scope: list[str]
    out_of_scope: list[str]
    actors: list[str]
    requirements: list[Requirement]
    assumptions: list[str] = Field(description="Implied but not stated")
    unknowns: list[str] = Field(description="Missing information a designer needs")
    search_queries: list[str] = Field(description="5-10 short KB queries using domain identifiers verbatim")


# ---------- retrieval ----------
class Evidence(BaseModel):
    id: str = ""                 # EV-n, assigned by EvidencePool
    source: str                  # provider name: "stratum", "local-kb", ...
    kind: str = "doc"            # code | interface | datastore | adr | standard | hld | doc
    title: str
    uri: str
    snippet: str
    score: float = 0.0
    revision: str | None = None  # commit SHA / document version, for drift checks
    key: str = ""                # dedupe key (source|uri|snippet hash)


# ---------- clarification ----------
class Question(BaseModel):
    id: str = Field(description="Q-n")
    question: str
    why_it_matters: str = Field(description="Which design choice changes depending on the answer")
    blocking: bool = Field(description="True only when no reasonable default exists")
    affects_sections: list[str] = Field(default_factory=list)
    default_assumption: str = Field(description="Used if the architect does not answer")


class QuestionSet(BaseModel):
    questions: list[Question]


# ---------- decisions ----------
class Decision(BaseModel):
    id: str = Field(description="DEC-n")
    title: str
    context: str
    options: list[str] = Field(description="At least two real options")
    choice: str
    rationale: str = Field(description="Tie to requirement IDs and evidence IDs")
    consequences: list[str]
    evidence_ids: list[str] = Field(default_factory=list)
    status: Literal["proposed", "accepted", "amended", "rejected"] = "proposed"


class DecisionSet(BaseModel):
    decisions: list[Decision]


# ---------- drafting ----------
class SectionOutput(BaseModel):
    """What the LLM returns for one template section. References are parsed from body, not trusted from the model."""
    body: str = Field(description="AsciiDoc content below the section heading; do not repeat the heading")
    assumptions: list[str] = Field(default_factory=list)
    open_issues: list[str] = Field(default_factory=list)


# ---------- review ----------
class Finding(BaseModel):
    section_id: str              # template section id, or "document"
    severity: Literal["blocker", "major", "minor"]
    rule: str                    # lint rule id (L0xx/L1xx) or "critic"
    issue: str
    fix: str = ""


class CriticReport(BaseModel):
    findings: list[Finding]
