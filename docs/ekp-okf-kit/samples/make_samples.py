"""Writes the sample builds: one per source kind, plus a broken second Jira run.

This script stands in for the five source adapters. Each block below is what
that adapter would decide from the synthetic input in samples/sources/ (type,
anchors, facet values, relations). The real decisions come from your
extractors; the point here is that every adapter calls the same emit_concept().
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from ekp_okf.emit import emit_concept, write_index  # noqa: E402
from ekp_okf.kit import load_kit  # noqa: E402

KIT = load_kit()
PROJECT, LOCATION = "acme-ekp", "us-central1"
BUILDS = HERE / "builds"
T1 = "20261124T180000Z"


def h6(s: str) -> str:
    return hashlib.sha256(" ".join(s.split()).encode()).hexdigest()[:6]


def workspace(group: str, dirname: str | None = None) -> Path:
    d = BUILDS / (dirname or group)
    if d.exists():
        shutil.rmtree(d)
    (d / "bundle").mkdir(parents=True)
    (d / "catalog.yaml").write_text(f"scope: entryGroup.{PROJECT}.{LOCATION}.{group}\nlayout: okf\n")
    return d


def emit(d: Path, group: str, profile: str, **kw):
    return emit_concept(KIT, d, project=PROJECT, location=LOCATION, entry_group=group, profile=profile, **kw)


# Stable IDs that cross-build relations point at. Derived from source identity.
CODE_RULE_COND = "seat->attrs & SEAT_ATTR_EXIT_ROW && pax->infant_count > 0"
CODE_RULE = f"rules/seatalloc/infant_rules.c/check_exit_row_infant/eligibility-{h6(CODE_RULE_COND)}"
BRD_RULE_STMT = "exit_row(seat) and infant_count(pax) > 0 => reject"
BRD_RULE = f"rules/BRD-SEAT/BR-SEAT-014/eligibility-{h6(BRD_RULE_STMT)}"
HLD_DEC = "decisions/HLD-DCS-SEAT-002/dec-seat-eligibility-rules-table"
BRD_REQ = "requirements/BRD-SEAT/BR-SEAT-014"


# --------------------------------------------------------------------------- registry
def registry():
    g = "ekp-registry"
    d = workspace(g)
    bid = f"{g}-{T1}"
    for a in KIT.anchors.values():
        prefix, rest = a["id"].split(":", 1)
        ctype = KIT.anchor_type_for_prefix(prefix)
        dom = a["id"] if prefix == "domain" else a.get("domain") or \
            KIT.anchors.get(a.get("system", ""), {}).get("domain") or "domain:departure-control"
        aliases = ", ".join(f"`{x}`" for x in a.get("aliases", []))
        emit(d, g, "registry", entry_id=f"anchors/{prefix}/{rest}", ctype=ctype,
             title=a["title"], description=a["description"],
             body=f"# {a['title']}\n\n{a['description']}\n\n**Also known as:** {aliases}\n",
             core=dict(domain=dom.split(":", 1)[1], source_system="git",
                       source_ref=f"registry:{prefix}:{rest}", source_revision="reg-v1.0",
                       extraction="human", valid_from="2026-07-01T00:00:00Z",
                       owner_team="team:ekp-registry", build_id=bid),
             sources=[{"id": "reg", "resource": "anchors/registry.yaml", "title": "EKP anchor registry"}],
             generated={"by": "human:registry-owners", "at": "2026-07-01T00:00:00Z"},
             verified=[{"by": "human:registry-owners", "at": "2026-07-01T00:00:00Z"}])
    write_index(d, "EKP anchor registry", "Canonical domains, systems, components, capabilities and terms every EKP bundle anchors to. Use it to resolve names and aliases.")
    return d, bid


# --------------------------------------------------------------------------- 1. code repo
def code():
    g = "code-dcs-seat"
    d = workspace(g)
    bid = f"{g}-{T1}"
    sha = "9c1e2f7a4b0d"
    common = dict(domain="departure-control", primary_system="system:dcs",
                  primary_component="component:dcs.seat-assignment", source_system="git",
                  source_revision=sha, extraction="deterministic",
                  valid_from="2026-09-14T08:00:00Z", owner_team="team:dcs-seating", build_id=bid)
    gen = {"by": "ekp-tpfc-extractor/0.4", "at": "2026-09-14T08:00:00Z"}
    url = f"https://git.example.com/dcs-seat/blob/{sha}/seatalloc"

    emit(d, g, "code-repo", entry_id=CODE_RULE, ctype="BusinessRule",
         title="Infant passenger may not be assigned an exit-row seat",
         description="check_exit_row_infant rejects an exit-row seat (SEAT_REJ_INF_EXIT) when the passenger has a lap infant.",
         tags=["seat-eligibility", "infant", "exit-row"],
         body=f"""# Rule

If the requested seat has `SEAT_ATTR_EXIT_ROW` set and the passenger's
`infant_count` is greater than 0, seat assignment is rejected with
`SEAT_REJ_INF_EXIT` (41).[^code]

# Condition

```c
{CODE_RULE_COND}
```

# Where it runs

`check_exit_row_infant()` in `seatalloc/infant_rules.c`, part of
[the infant rules module](/modules/seatalloc/infant_rules.c.md).

[^code]: seatalloc/infant_rules.c lines 9-16 at {sha[:7]}
""",
         core={**common, "primary_capability": "capability:seat-eligibility",
               "source_ref": f"git:dcs-seat:seatalloc/infant_rules.c#check_exit_row_infant/eligibility-{h6(CODE_RULE_COND)}",
               "source_url": f"{url}/infant_rules.c#L9-L16",
               "anchors": ["system:dcs", "component:dcs.seat-assignment", "capability:seat-eligibility",
                           "term:infant", "term:exit-row"],
               "relations": [{"rel": "implements", "target": f"brd-seat:{BRD_REQ}"},
                             {"rel": "governed_by", "target": f"hld-dcs-seat:{HLD_DEC}"}]},
         facet={"rule_kind": "eligibility", "enforcement": "code"},
         sources=[{"id": "code", "resource": f"{url}/infant_rules.c#L9-L16",
                   "title": "seatalloc/infant_rules.c", "last_modified": "2026-09-14T08:00:00Z"}],
         generated=gen,
         verified=[{"by": "process:ekp-rule-check", "at": "2026-11-24T18:05:00Z"}])

    emit(d, g, "code-repo", entry_id="modules/seatalloc/infant_rules.c", ctype="Module",
         title="seatalloc/infant_rules.c",
         description="Infant-related seat eligibility checks called during seat assignment.",
         tags=["seat-eligibility", "infant"],
         body="""# Purpose

Holds infant-related seat eligibility checks. Seat assignment calls
`check_exit_row_infant()` before committing a seat.

# Functions

* `check_exit_row_infant(pax, seat)` - rejects exit-row seats for passengers with infants.
""",
         core={**common, "source_ref": "git:dcs-seat:seatalloc/infant_rules.c",
               "source_url": f"{url}/infant_rules.c",
               "anchors": ["system:dcs", "component:dcs.seat-assignment", "term:infant"],
               "relations": [{"rel": "enforces", "target": f"{g}:{CODE_RULE}"},
                             {"rel": "reads", "target": f"{g}:data/seatalloc/seat_types.h/pax_t"}]},
         facet={"language": "tpf-c", "module_kind": "program"},
         sources=[{"id": "code", "resource": f"{url}/infant_rules.c", "title": "seatalloc/infant_rules.c"}],
         generated=gen, verified=[{"by": "process:ekp-rule-check", "at": "2026-11-24T18:05:00Z"}])

    emit(d, g, "code-repo", entry_id="data/seatalloc/seat_types.h/pax_t", ctype="DataEntity",
         title="pax_t passenger record",
         description="Passenger record used by seat allocation; infant_count holds the number of lap infants.",
         tags=["infant"],
         body="""# Schema

| Field | Type | Meaning |
|---|---|---|
| surname | char[32] | Passenger surname |
| infant_count | short | Lap infants travelling with this passenger |
| cabin | char | Booked cabin |
""",
         core={**common, "source_ref": "git:dcs-seat:seatalloc/seat_types.h#pax_t",
               "source_url": f"{url}/seat_types.h",
               "anchors": ["system:dcs", "component:dcs.seat-assignment", "term:infant"]},
         sources=[{"id": "hdr", "resource": f"{url}/seat_types.h", "title": "seatalloc/seat_types.h"}],
         generated=gen, verified=[{"by": "process:ekp-rule-check", "at": "2026-11-24T18:05:00Z"}])
    write_index(d, "Code: dcs-seat (TPF C)", "Legacy seat allocation code: modules, seat eligibility rules and record layouts. Use it for how the legacy DCS enforces seat rules.")
    return d, bid


# --------------------------------------------------------------------------- 2. HLD
def hld():
    g = "hld-dcs-seat"
    d = workspace(g)
    bid = f"{g}-{T1}"
    common = dict(domain="departure-control", primary_system="system:dcs",
                  primary_component="component:dcs.seat-assignment", source_system="git",
                  source_revision="a77d01c3e9f2", extraction="template",
                  owner_team="team:dcs-architecture", build_id=bid,
                  source_url="https://git.example.com/arch-docs/blob/a77d01c/HLD-DCS-SEAT-002.adoc")
    gen = {"by": "ekp-hld-adapter/0.2", "at": "2026-08-20T00:00:00Z"}
    src = [{"id": "hld", "resource": "https://git.example.com/arch-docs/blob/a77d01c/HLD-DCS-SEAT-002.adoc",
            "title": "HLD-DCS-SEAT-002 Seat Assignment Modernisation", "author": "team:dcs-architecture"}]

    emit(d, g, "arch-doc", entry_id=HLD_DEC, ctype="Decision",
         title="Seat eligibility rules move to a rules table",
         description="Seat eligibility checks become rows in the modernised seat service's rules table; legacy C checks stay authoritative until cut-over.",
         tags=["seat-eligibility", "modernisation"],
         body="""# Decision

Express seat eligibility rules as rows in the modernised seat service's rules
table. Legacy C checks stay authoritative until cut-over.[^hld]

# Context

Eligibility checks such as infant-in-exit-row are hard-coded per C function,
so every change needs a release.

# Consequences

Rules become data with owners and effective dates. Every legacy rule needs a
one-to-one migration and a parity test.

[^hld]: HLD-DCS-SEAT-002, section dec-seat-eligibility-rules-table
""",
         core={**common, "primary_capability": "capability:seat-eligibility",
               "source_ref": "hld:HLD-DCS-SEAT-002#dec-seat-eligibility-rules-table",
               "valid_from": "2026-08-20T00:00:00Z",
               "anchors": ["system:dcs", "component:dcs.seat-assignment", "capability:seat-eligibility"]},
         facet={"decision_status": "accepted", "decided_on": "2026-08-20T00:00:00Z"},
         sources=src, generated=gen,
         verified=[{"by": "human:arch-review-board", "at": "2026-08-21T10:00:00Z"}])

    emit(d, g, "arch-doc", entry_id="designs/HLD-DCS-SEAT-002/des-seat-eligibility-service", ctype="Design",
         title="Seat eligibility evaluation in the seat service",
         description="The seat service evaluates active eligibility rules per passenger-seat pair and returns the first reject reason.",
         tags=["seat-eligibility"],
         body="""# Design

The seat service loads active rules for the flight, evaluates them per
passenger-seat pair and returns the first reject reason. Infant, exit-row and
cabin rules run before price rules.
""",
         core={**common, "source_ref": "hld:HLD-DCS-SEAT-002#des-seat-eligibility-service",
               "valid_from": "2026-08-20T00:00:00Z",
               "anchors": ["system:dcs", "component:dcs.seat-assignment", "capability:seat-eligibility"],
               "relations": [{"rel": "governed_by", "target": f"{g}:{HLD_DEC}"},
                             {"rel": "describes", "target": f"code-dcs-seat:{CODE_RULE}"}]},
         sources=src, generated=gen)
    write_index(d, "HLD: HLD-DCS-SEAT-002", "Seat assignment modernisation decisions and designs. Use it for why seat eligibility is moving to a rules table.")
    return d, bid


# --------------------------------------------------------------------------- 3. BRD
def brd():
    g = "brd-seat"
    d = workspace(g)
    bid = f"{g}-{T1}"
    common = dict(domain="departure-control", primary_system="system:dcs",
                  primary_component="component:dcs.seat-assignment",
                  primary_capability="capability:seat-eligibility", source_system="confluence",
                  source_revision="v12", valid_from="2026-03-02T00:00:00Z",
                  owner_team="team:dcs-product", build_id=bid,
                  source_url="https://wiki.example.com/display/BRD/BRD-SEAT")
    src = [{"id": "brd", "resource": "https://wiki.example.com/display/BRD/BRD-SEAT",
            "title": "BRD-SEAT Seat Assignment", "author": "team:dcs-product"}]

    emit(d, g, "brd", entry_id=BRD_REQ, ctype="Requirement",
         title="BR-SEAT-014: no exit-row seat for a passenger travelling with an infant",
         description="The system shall not assign a seat in an exit row to a passenger travelling with an infant.",
         tags=["seat-eligibility", "infant", "exit-row"],
         body="""# Requirement

The system shall not assign a seat in an exit row to a passenger travelling
with an infant.[^brd]

| Priority | Status |
|---|---|
| Must | Implemented |

[^brd]: BRD-SEAT section 4, row BR-SEAT-014
""",
         core={**common, "source_ref": "brd:BRD-SEAT#BR-SEAT-014", "extraction": "template",
               "anchors": ["system:dcs", "component:dcs.seat-assignment", "capability:seat-eligibility",
                           "term:infant", "term:exit-row"],
               "relations": [{"rel": "specifies", "target": f"{g}:{BRD_RULE}"}]},
         facet={"req_id": "BR-SEAT-014", "req_kind": "functional", "priority": "must", "req_status": "implemented"},
         sources=src, generated={"by": "ekp-brd-adapter/0.3", "at": "2026-03-02T00:00:00Z"},
         verified=[{"by": "human:ba-signoff", "at": "2026-03-05T09:00:00Z"}])

    # The rule stated inside the requirement, extracted by an LLM. Unverified,
    # so policy forces status: draft. Its same_as edge to the code rule is a
    # reconciliation candidate for a human to confirm.
    emit(d, g, "brd", entry_id=BRD_RULE, ctype="BusinessRule",
         title="Exit-row seat rejected when passenger has an infant (as stated in BR-SEAT-014)",
         description="Business rule extracted from BR-SEAT-014: reject an exit-row seat if the passenger travels with an infant.",
         tags=["seat-eligibility", "infant", "exit-row"],
         body=f"""# Rule

Reject an exit-row seat when the passenger travels with an infant.

```text
{BRD_RULE_STMT}
```
""",
         core={**common, "source_ref": f"brd:BRD-SEAT#BR-SEAT-014/eligibility-{h6(BRD_RULE_STMT)}",
               "extraction": "llm", "confidence": 0.91,
               "anchors": ["system:dcs", "component:dcs.seat-assignment", "capability:seat-eligibility",
                           "term:infant", "term:exit-row"],
               "relations": [{"rel": "same_as", "target": f"code-dcs-seat:{CODE_RULE}"}]},
         facet={"rule_kind": "eligibility", "enforcement": "unknown"},
         sources=src, generated={"by": "ekp-brd-adapter/0.3+gemini-2.5-pro", "at": "2026-11-24T18:00:00Z"},
         status="draft")
    write_index(d, "BRD: BRD-SEAT", "Seat assignment business requirements and the rules they state. Use it for what the business requires.")
    return d, bid


# --------------------------------------------------------------------------- 4. wiki
def wiki(dirname=None, bid=None, previous=None):
    g = "wiki-dcsops"
    d = workspace(g, dirname)
    bid = bid or f"{g}-{T1}"
    emit(d, g, "wiki", previous_bundle=previous, entry_id="procedures/DCSOPS/48213907", ctype="Procedure",
         title="Gate: passenger with infant holds an exit-row seat",
         description="Gate agent steps to reseat a passenger travelling with an infant out of an exit row.",
         tags=["runbook", "infant", "exit-row"],
         body="""# When to use

The seat map shows reject `INF EXIT`, or a passenger with an infant is found in
an exit row at the gate.

# Steps

1. Open the passenger in the seat map and pick a non-exit seat in the same cabin.
2. If none is free, offer a seat in another cabin per the downgrade/upgrade policy.
3. Re-issue the boarding pass. Do not override the exit-row block.
""",
         core=dict(domain="departure-control", primary_system="system:dcs",
                   primary_component="component:dcs.seat-assignment", source_system="confluence",
                   source_ref="confluence:DCSOPS:48213907", source_revision="7",
                   source_url="https://wiki.example.com/pages/viewpage.action?pageId=48213907",
                   extraction="deterministic", valid_from="2026-10-05T00:00:00Z",
                   owner_team="team:airport-ops", build_id=bid,
                   anchors=["system:dcs", "component:dcs.seat-assignment", "term:infant", "term:exit-row"],
                   relations=[{"rel": "describes", "target": f"code-dcs-seat:{CODE_RULE}"}]),
         sources=[{"id": "page", "resource": "https://wiki.example.com/pages/viewpage.action?pageId=48213907",
                   "title": "DCSOPS / Gate: passenger with infant holds an exit-row seat",
                   "author": "team:airport-ops", "usage_count": 312,
                   "last_modified": "2026-10-05T00:00:00Z"}],
         generated={"by": "ekp-confluence-adapter/0.2", "at": "2026-10-05T00:00:00Z"},
         verified=[{"by": "human:ops-lead", "at": "2026-10-06T08:00:00Z"}])
    write_index(d, "Wiki: DCSOPS", "Departure control operations runbooks. Use it for what an agent or operator does at the airport.")
    return d, bid


# --------------------------------------------------------------------------- 5. Jira
def jira_change(d, g, bid, key, summary, desc, status, release, children, relations, comp_anchor):
    emit(d, g, "jira", entry_id=f"changes/{key}", ctype="Change",
         title=f"{key}: {summary}", description=desc, tags=["seat-eligibility"],
         body=f"# Change\n\n{desc}\n\n# Work items\n\n" +
              "\n".join(f"* {c['key']} ({c['issuetype']}): {c['summary']}" for c in children) + "\n",
         core=dict(domain="departure-control", primary_system="system:dcs",
                   primary_component=comp_anchor, primary_capability="capability:seat-eligibility",
                   source_system="jira", source_ref=f"jira:{key}", source_revision="2026-10-02T11:20:00Z",
                   source_url=f"https://jira.example.com/browse/{key}", extraction="deterministic",
                   valid_from="2026-10-02T11:20:00Z", owner_team="team:dcs-seating", build_id=bid,
                   anchors=["system:dcs", comp_anchor, "capability:seat-eligibility"],
                   relations=relations),
         facet={"change_status": status, "release": release},
         # Child tickets are evidence on the epic, not concepts of their own.
         sources=[{"id": key.lower(), "resource": f"https://jira.example.com/browse/{key}", "title": key}] +
                 [{"id": c["key"].lower(), "resource": f"https://jira.example.com/browse/{c['key']}",
                   "title": f"{c['key']} {c['summary']}"} for c in children],
         generated={"by": "ekp-jira-adapter/0.3", "at": "2026-10-02T11:20:00Z"})


def jira():
    g = "jira-seat"
    d = workspace(g)
    bid = f"{g}-{T1}"
    jira_change(d, g, bid, "SEAT-412",
                "Re-check exit-row eligibility when an infant is added after seat assignment",
                "Exit-row infant check now re-runs when an infant is added to a seated passenger and on kiosk seat changes (release 2026.10).",
                "done", "2026.10",
                [{"key": "SEAT-415", "issuetype": "Story", "summary": "Run exit-row infant check when an infant is added to a seated passenger"},
                 {"key": "SEAT-419", "issuetype": "Bug", "summary": "Exit-row infant check skipped on kiosk seat change"}],
                [{"rel": "changes", "target": f"code-dcs-seat:{CODE_RULE}"}], "component:dcs.seat-assignment")
    jira_change(d, g, bid, "SEAT-401", "Show infant-restricted seats on the seat map",
                "Seat map greys out seats a passenger with an infant may not select.",
                "done", "2026.09",
                [{"key": "SEAT-402", "issuetype": "Story", "summary": "Grey out exit-row seats for passengers with infants"}],
                [], "component:dcs.seat-assignment")
    write_index(d, "Jira: SEAT", "Seat epics: what changed, when and in which release. Use it for change history.")
    return d, bid


def jira_next_broken():
    """The next Jira run, with the defects the gate exists to catch."""
    g = "jira-seat"
    d = workspace(g, "jira-seat-next-broken")
    bid = f"{g}-20261125T060000Z"
    # (a) anchor written as a raw Jira component name instead of its canonical ID
    jira_change(d, g, bid, "SEAT-412",
                "Re-check exit-row eligibility when an infant is added after seat assignment",
                "Exit-row infant check now re-runs when an infant is added to a seated passenger and on kiosk seat changes (release 2026.10).",
                "done", "2026.10",
                [{"key": "SEAT-415", "issuetype": "Story", "summary": "Run exit-row infant check when an infant is added to a seated passenger"}],
                [{"rel": "changes", "target": f"code-dcs-seat:{CODE_RULE}"}], "Seating")
    # (b) SEAT-401 silently dropped: kcmd push would delete its entry
    # (c) path derived from the summary instead of the Jira key
    emit(d, g, "jira", entry_id="changes/kiosk-exit-row-recheck", ctype="Change",
         title="SEAT-430: Kiosk exit-row re-check", description="Kiosk re-runs the exit-row check after a seat change.",
         body="# Change\n\nKiosk re-runs the exit-row check after a seat change.\n",
         core=dict(domain="departure-control", primary_system="system:dcs", source_system="jira",
                   source_ref="jira:SEAT-430", source_revision="2026-11-20T09:00:00Z",
                   extraction="deterministic", valid_from="2026-11-20T09:00:00Z",
                   owner_team="team:dcs-seating", build_id=bid, anchors=["system:dcs"]),
         facet={"change_status": "in_progress"},
         sources=[{"id": "seat-430", "resource": "https://jira.example.com/browse/SEAT-430"}],
         generated={"by": "ekp-jira-adapter/0.3", "at": "2026-11-25T06:00:00Z"})
    # (d) decision pulled from a comment by an LLM, published as stable without verification
    emit(d, g, "jira", entry_id="decisions/SEAT-412/c88123", ctype="Decision",
         title="Kiosk uses the same eligibility call as the agent seat map",
         description="Agreed in SEAT-412 comments: kiosk seat changes call check_exit_row_infant like the agent flow.",
         body="# Decision\n\nKiosk seat changes call the same eligibility check as the agent seat map.\n",
         core=dict(domain="departure-control", primary_system="system:dcs", source_system="jira",
                   source_ref="jira:SEAT-412#comment-88123", source_revision="2026-11-21T10:00:00Z",
                   extraction="llm", confidence=0.84, valid_from="2026-11-21T10:00:00Z",
                   owner_team="team:dcs-seating", build_id=bid, anchors=["system:dcs"]),
         facet={"decision_status": "accepted"},
         sources=[{"id": "c", "resource": "https://jira.example.com/browse/SEAT-412?focusedCommentId=88123"}],
         generated={"by": "ekp-jira-adapter/0.3+gemini-2.5-pro", "at": "2026-11-25T06:00:00Z"},
         status="stable")
    # (e) someone hand-edits trust_tier after generation (header now stale too)
    p = d / "bundle" / "changes" / "SEAT-412.md"
    p.write_text(p.read_text().replace("trust_tier: unverified", "trust_tier: human_reviewed", 1))
    write_index(d, "Jira: SEAT", "Seat epics: what changed, when and in which release. Use it for change history.")
    return d, bid


# --------------------------------------------------------------------------- 1b. any repo kind
SVC_RULE_ROW = "INF_EXIT_ROW: seat.exit_row == true and pax.infant_count > 0 -> reject INF_EXIT"
SVC_RULE = f"rules/src/main/resources/rules/seat-eligibility.yaml/INF_EXIT_ROW/eligibility-{h6(SVC_RULE_ROW)}"
SVC_TOPIC = "infra/terraform/pubsub.tf/google_pubsub_topic.seat_assigned"


def code_seat_service():
    """A modern monorepo: Java service + rules-as-data + OpenAPI + Terraform.
    Four extractors (app-code, rules-config, api-spec, terraform) feed one build
    through the same code-repo profile and the same emit_concept()."""
    g = "code-seat-service"
    d = workspace(g)
    bid = f"{g}-{T1}"
    sha = "4be09a1c77d2"
    url = f"https://git.example.com/seat-service/blob/{sha}"
    common = dict(domain="departure-control", primary_system="system:dcs",
                  primary_component="component:dcs.seat-assignment", source_system="git",
                  source_revision=sha, extraction="deterministic", valid_from="2026-10-01T00:00:00Z",
                  owner_team="team:dcs-seating", build_id=bid)
    at = "2026-10-01T00:00:00Z"      # commit time of the content = last meaningful change
    check = [{"by": "process:ekp-parity-check", "at": "2026-11-24T18:05:00Z"}]

    emit(d, g, "code-repo", entry_id="modules/src/main/java/com/example/seat/EligibilityService.java",
         ctype="Module", title="EligibilityService (seat service)",
         description="Spring service that evaluates the seat rules table and publishes seat-assigned events.",
         tags=["seat-eligibility"],
         body="""# Purpose

`assignSeat()` asks the rules table for the first reject reason. If there is
none, it assigns the seat and publishes a `seat-assigned` event.
""",
         core={**common, "source_ref": "git:seat-service:src/main/java/com/example/seat/EligibilityService.java",
               "anchors": ["system:dcs", "component:dcs.seat-assignment", "capability:seat-eligibility"],
               "relations": [{"rel": "enforces", "target": f"{g}:{SVC_RULE}"},
                             {"rel": "exposes", "target": f"{g}:interfaces/api/seat-api.yaml/assignSeat"},
                             {"rel": "calls", "target": f"{g}:interfaces/src/main/java/com/example/seat/EligibilityService.java/publishSeatAssigned"}]},
         facet={"language": "java", "module_kind": "service"},
         sources=[{"id": "src", "resource": f"{url}/src/main/java/com/example/seat/EligibilityService.java"}],
         generated={"by": "ekp-java-extractor/0.1", "at": at}, verified=check)

    emit(d, g, "code-repo", entry_id=SVC_RULE, ctype="BusinessRule",
         title="INF_EXIT_ROW: infant passenger may not take an exit-row seat (rules table)",
         description="Rules-table row INF_EXIT_ROW rejects an exit-row seat with INF_EXIT when the passenger has a lap infant.",
         tags=["seat-eligibility", "infant", "exit-row"],
         body=f"""# Rule

Row `INF_EXIT_ROW` in `rules/seat-eligibility.yaml`, effective 2026-10-01:
reject with `INF_EXIT` when the seat is an exit row and the passenger's
`infant_count` is greater than 0.

```text
{SVC_RULE_ROW}
```

This is the rules-table form of the legacy TPF check, per the HLD decision.
""",
         core={**common, "primary_capability": "capability:seat-eligibility",
               "source_ref": f"git:seat-service:src/main/resources/rules/seat-eligibility.yaml#INF_EXIT_ROW/eligibility-{h6(SVC_RULE_ROW)}",
               "anchors": ["system:dcs", "component:dcs.seat-assignment", "capability:seat-eligibility",
                           "term:infant", "term:exit-row"],
               "relations": [{"rel": "implements", "target": f"brd-seat:{BRD_REQ}"},
                             {"rel": "governed_by", "target": f"hld-dcs-seat:{HLD_DEC}"},
                             {"rel": "same_as", "target": f"code-dcs-seat:{CODE_RULE}"}]},
         facet={"rule_kind": "eligibility", "enforcement": "config"},
         sources=[{"id": "row", "resource": f"{url}/src/main/resources/rules/seat-eligibility.yaml"}],
         generated={"by": "ekp-rules-config-extractor/0.1", "at": at}, verified=check)

    emit(d, g, "code-repo", entry_id="interfaces/api/seat-api.yaml/assignSeat", ctype="Interface",
         title="PUT /passengers/{paxId}/seat (assignSeat)",
         description="REST operation that assigns a seat or returns 422 with a reason code such as INF_EXIT.",
         tags=["seat-eligibility"],
         body="""# Contract

`PUT /passengers/{paxId}/seat`, operationId `assignSeat`, Seat API 1.4.0.

| Status | Meaning |
|---|---|
| 200 | Seat assigned |
| 422 | Seat not allowed, with a reason code (for example `INF_EXIT`) |
""",
         core={**common, "source_ref": "git:seat-service:api/seat-api.yaml#assignSeat",
               "anchors": ["system:dcs", "component:dcs.seat-assignment"]},
         facet={"protocol": "rest", "direction": "inbound"},
         sources=[{"id": "spec", "resource": f"{url}/api/seat-api.yaml"}],
         generated={"by": "ekp-openapi-extractor/0.1", "at": at})

    emit(d, g, "code-repo",
         entry_id="interfaces/src/main/java/com/example/seat/EligibilityService.java/publishSeatAssigned",
         ctype="Interface", title="seat-assigned event (publishSeatAssigned)",
         description="Event published to Pub/Sub topic seat-assigned after a seat is assigned.",
         body="# Contract\n\nPublished by `EligibilityService.assignSeat()` after a successful assignment.\n",
         core={**common, "source_ref": "git:seat-service:src/main/java/com/example/seat/EligibilityService.java#publishSeatAssigned",
               "anchors": ["system:dcs", "component:dcs.seat-assignment"],
               "relations": [{"rel": "provisioned_by", "target": f"{g}:{SVC_TOPIC}"}]},
         facet={"protocol": "pubsub", "direction": "outbound"},
         sources=[{"id": "src", "resource": f"{url}/src/main/java/com/example/seat/EligibilityService.java"}],
         generated={"by": "ekp-java-extractor/0.1", "at": at})

    emit(d, g, "code-repo", entry_id=SVC_TOPIC, ctype="InfraResource",
         title="Pub/Sub topic seat-assigned",
         description="Terraform-managed GCP Pub/Sub topic that carries seat-assigned events, retained for one day.",
         body="""# Resource

`google_pubsub_topic.seat_assigned` in `terraform/pubsub.tf`.

| Attribute | Value |
|---|---|
| name | seat-assigned |
| message_retention_duration | 86400s |
| labels | system=dcs, component=seat-assignment |
""",
         core={**common, "source_ref": "git:seat-service:terraform/pubsub.tf#google_pubsub_topic.seat_assigned",
               "anchors": ["system:dcs", "component:dcs.seat-assignment"]},
         facet={"tool": "terraform", "provider": "gcp", "resource_kind": "google_pubsub_topic"},
         sources=[{"id": "tf", "resource": f"{url}/terraform/pubsub.tf"}],
         generated={"by": "ekp-terraform-extractor/0.1", "at": at})
    write_index(d, "Code: seat-service (Java, OpenAPI, Terraform)",
                "Modernised seat service: rules table, REST API, events and the GCP resources behind them. "
                "Use it for how the new seat service works and is deployed.")
    return d, bid


def hld_next_changed():
    """Next HLD run after someone edits the decision's text. The emitter carries the
    old human review forward as history, but it is no longer current (OKF v0.3
    §5.3), so trust drops to unverified and the gate flags it for re-review."""
    g = "hld-dcs-seat"
    prev = BUILDS / g / "bundle"
    d = workspace(g, "hld-dcs-seat-next-changed")
    bid = f"{g}-20261125T060000Z"
    common = dict(domain="departure-control", primary_system="system:dcs",
                  primary_component="component:dcs.seat-assignment", source_system="git",
                  source_revision="b81f2e0d44aa", extraction="template",
                  owner_team="team:dcs-architecture", build_id=bid,
                  source_url="https://git.example.com/arch-docs/blob/b81f2e0/HLD-DCS-SEAT-002.adoc")
    src = [{"id": "hld", "resource": "https://git.example.com/arch-docs/blob/b81f2e0/HLD-DCS-SEAT-002.adoc",
            "title": "HLD-DCS-SEAT-002 Seat Assignment Modernisation", "author": "team:dcs-architecture"}]
    # changed: the legacy C checks are now retired on a fixed date
    emit(d, g, "arch-doc", previous_bundle=prev, entry_id=HLD_DEC, ctype="Decision",
         title="Seat eligibility rules move to a rules table",
         description="Seat eligibility checks become rows in the modernised seat service's rules table; legacy C checks are retired on 2027-03-31.",
         tags=["seat-eligibility", "modernisation"],
         body="""# Decision

Express seat eligibility rules as rows in the modernised seat service's rules
table. Legacy C checks are retired on 2027-03-31.[^hld]

# Context

Eligibility checks such as infant-in-exit-row are hard-coded per C function,
so every change needs a release.

# Consequences

Rules become data with owners and effective dates. Every legacy rule needs a
one-to-one migration and a parity test.

[^hld]: HLD-DCS-SEAT-002, section dec-seat-eligibility-rules-table
""",
         core={**common, "primary_capability": "capability:seat-eligibility",
               "source_ref": "hld:HLD-DCS-SEAT-002#dec-seat-eligibility-rules-table",
               "valid_from": "2026-08-20T00:00:00Z",
               "anchors": ["system:dcs", "component:dcs.seat-assignment", "capability:seat-eligibility"]},
         facet={"decision_status": "accepted", "decided_on": "2026-08-20T00:00:00Z"},
         sources=src, generated={"by": "ekp-hld-adapter/0.2", "at": "2026-11-25T05:40:00Z"})
    # unchanged: generated.at carried forward, nothing to re-review
    emit(d, g, "arch-doc", previous_bundle=prev,
         entry_id="designs/HLD-DCS-SEAT-002/des-seat-eligibility-service", ctype="Design",
         title="Seat eligibility evaluation in the seat service",
         description="The seat service evaluates active eligibility rules per passenger-seat pair and returns the first reject reason.",
         tags=["seat-eligibility"],
         body="""# Design

The seat service loads active rules for the flight, evaluates them per
passenger-seat pair and returns the first reject reason. Infant, exit-row and
cabin rules run before price rules.
""",
         core={**{**common, "source_revision": "a77d01c3e9f2",
                  "source_url": "https://git.example.com/arch-docs/blob/a77d01c/HLD-DCS-SEAT-002.adoc"},
               "source_ref": "hld:HLD-DCS-SEAT-002#des-seat-eligibility-service",
               "valid_from": "2026-08-20T00:00:00Z",
               "anchors": ["system:dcs", "component:dcs.seat-assignment", "capability:seat-eligibility"],
               "relations": [{"rel": "governed_by", "target": f"{g}:{HLD_DEC}"},
                             {"rel": "describes", "target": f"code-dcs-seat:{CODE_RULE}"}]},
         sources=[{**src[0], "resource": "https://git.example.com/arch-docs/blob/a77d01c/HLD-DCS-SEAT-002.adoc"}],
         generated={"by": "ekp-hld-adapter/0.2", "at": "2026-11-25T05:40:00Z"})
    write_index(d, "HLD: HLD-DCS-SEAT-002", "Seat assignment modernisation decisions and designs. "
                "Use it for why seat eligibility is moving to a rules table.")
    return d, bid



def wiki_next_llm():
    """Next wiki run: the labelled runbook goes through the deterministic path as
    before; two unlabelled pages go through the LLM lane (pipeline/llm_lane.py)."""
    from pipeline.llm_lane import classify_and_emit, read_confluence_export
    bid = "wiki-dcsops-20261125T010000Z"
    d, _ = wiki("wiki-dcsops-next-llm", bid, previous=BUILDS / "wiki-dcsops" / "bundle")
    results = []
    for page in ("DCSOPS-48219911.md", "DCSOPS-48220450.md"):
        results.append(classify_and_emit(KIT, read_confluence_export(HERE / "sources/wiki" / page),
                                         build_dir=d, build_id=bid,
                                         previous=BUILDS / "wiki-dcsops" / "bundle", model="fake"))
    write_index(d, "Wiki: DCSOPS", "Departure control operations runbooks. Use it for what an agent or operator does at the airport.")
    (HERE / "llm_lane_results.json").write_text(json.dumps(results, indent=2) + "\n")
    return d, bid


if __name__ == "__main__":
    for fn in (registry, code, code_seat_service, hld, brd, wiki, jira, jira_next_broken, hld_next_changed, wiki_next_llm):
        d, bid = fn()
        print(f"wrote {d.relative_to(HERE.parent)}  ({bid})")
