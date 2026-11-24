---
type: Business Rule
title: Infant passenger may not be assigned an exit-row seat
description: check_exit_row_infant rejects an exit-row seat (SEAT_REJ_INF_EXIT) when the passenger has
  a lap infant.
tags:
- seat-eligibility
- infant
- exit-row
status: stable
generated:
  by: ekp-tpfc-extractor/0.4
  at: '2026-09-14T08:00:00Z'
verified:
- by: process:ekp-rule-check
  at: '2026-11-24T18:05:00Z'
sources:
- id: code
  resource: https://git.example.com/dcs-seat/blob/9c1e2f7a4b0d/seatalloc/infant_rules.c#L9-L16
  title: seatalloc/infant_rules.c
  last_modified: '2026-09-14T08:00:00Z'
extra:
  aspects:
    acme-ekp.us-central1.ekp-core:
      concept_id: code-dcs-seat:rules/seatalloc/infant_rules.c/check_exit_row_infant/eligibility-353743
      concept_type: BusinessRule
      lifecycle: stable
      domain: departure-control
      primary_system: system:dcs
      primary_component: component:dcs.seat-assignment
      primary_capability: capability:seat-eligibility
      source_kind: code
      source_system: git
      source_ref: git:dcs-seat:seatalloc/infant_rules.c#check_exit_row_infant/eligibility-353743
      source_revision: 9c1e2f7a4b0d
      source_url: https://git.example.com/dcs-seat/blob/9c1e2f7a4b0d/seatalloc/infant_rules.c#L9-L16
      extraction: deterministic
      trust_tier: machine_confirmed
      valid_from: '2026-09-14T08:00:00Z'
      owner_team: team:dcs-seating
      build_id: code-dcs-seat-20261124T180000Z
      profile: code-repo@2
      ontology_version: '1.1'
      anchors:
      - system:dcs
      - component:dcs.seat-assignment
      - capability:seat-eligibility
      - term:infant
      - term:exit-row
      relations:
      - rel: implements
        target: brd-seat:requirements/BRD-SEAT/BR-SEAT-014
      - rel: governed_by
        target: hld-dcs-seat:decisions/HLD-DCS-SEAT-002/dec-seat-eligibility-rules-table
    acme-ekp.us-central1.ekp-rule:
      rule_kind: eligibility
      enforcement: code
---

<!-- ekp:header v1 -->
> **Business Rule** · departure-control › system:dcs › component:dcs.seat-assignment
> **Source:** `git:dcs-seat:seatalloc/infant_rules.c#check_exit_row_infant/eligibility-353743` @ `9c1e2f7a4b0d` · extraction: deterministic
> **Trust:** machine_confirmed · **Status:** stable · **Valid from:** 2026-09-14
> **Also about:** `capability:seat-eligibility`, `term:infant`, `term:exit-row`
> **Relations:** implements `brd-seat:requirements/BRD-SEAT/BR-SEAT-014`; governed by `hld-dcs-seat:decisions/HLD-DCS-SEAT-002/dec-seat-eligibility-rules-table`
<!-- /ekp:header -->

# Rule

If the requested seat has `SEAT_ATTR_EXIT_ROW` set and the passenger's
`infant_count` is greater than 0, seat assignment is rejected with
`SEAT_REJ_INF_EXIT` (41).[^code]

# Condition

```c
seat->attrs & SEAT_ATTR_EXIT_ROW && pax->infant_count > 0
```

# Where it runs

`check_exit_row_infant()` in `seatalloc/infant_rules.c`, part of
[the infant rules module](/modules/seatalloc/infant_rules.c.md).

[^code]: seatalloc/infant_rules.c lines 9-16 at 9c1e2f7
