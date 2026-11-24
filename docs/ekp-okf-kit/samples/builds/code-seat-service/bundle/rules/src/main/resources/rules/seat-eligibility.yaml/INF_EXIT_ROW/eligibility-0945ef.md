---
type: Business Rule
title: 'INF_EXIT_ROW: infant passenger may not take an exit-row seat (rules table)'
description: Rules-table row INF_EXIT_ROW rejects an exit-row seat with INF_EXIT when the passenger has
  a lap infant.
tags:
- seat-eligibility
- infant
- exit-row
status: stable
generated:
  by: ekp-rules-config-extractor/0.1
  at: '2026-10-01T00:00:00Z'
verified:
- by: process:ekp-parity-check
  at: '2026-11-24T18:05:00Z'
sources:
- id: row
  resource: https://git.example.com/seat-service/blob/4be09a1c77d2/src/main/resources/rules/seat-eligibility.yaml
extra:
  aspects:
    acme-ekp.us-central1.ekp-core:
      concept_id: code-seat-service:rules/src/main/resources/rules/seat-eligibility.yaml/INF_EXIT_ROW/eligibility-0945ef
      concept_type: BusinessRule
      lifecycle: stable
      domain: departure-control
      primary_system: system:dcs
      primary_component: component:dcs.seat-assignment
      primary_capability: capability:seat-eligibility
      source_kind: code
      source_system: git
      source_ref: git:seat-service:src/main/resources/rules/seat-eligibility.yaml#INF_EXIT_ROW/eligibility-0945ef
      source_revision: 4be09a1c77d2
      extraction: deterministic
      trust_tier: machine_confirmed
      valid_from: '2026-10-01T00:00:00Z'
      owner_team: team:dcs-seating
      build_id: code-seat-service-20261124T180000Z
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
      - rel: same_as
        target: code-dcs-seat:rules/seatalloc/infant_rules.c/check_exit_row_infant/eligibility-353743
    acme-ekp.us-central1.ekp-rule:
      rule_kind: eligibility
      enforcement: config
---

<!-- ekp:header v1 -->
> **Business Rule** · departure-control › system:dcs › component:dcs.seat-assignment
> **Source:** `git:seat-service:src/main/resources/rules/seat-eligibility.yaml#INF_EXIT_ROW/eligibility-0945ef` @ `4be09a1c77d2` · extraction: deterministic
> **Trust:** machine_confirmed · **Status:** stable · **Valid from:** 2026-10-01
> **Also about:** `capability:seat-eligibility`, `term:infant`, `term:exit-row`
> **Relations:** implements `brd-seat:requirements/BRD-SEAT/BR-SEAT-014`; governed by `hld-dcs-seat:decisions/HLD-DCS-SEAT-002/dec-seat-eligibility-rules-table`; same as `code-dcs-seat:rules/seatalloc/infant_rules.c/check_exit_row_infant/eligibility-353743`
<!-- /ekp:header -->

# Rule

Row `INF_EXIT_ROW` in `rules/seat-eligibility.yaml`, effective 2026-10-01:
reject with `INF_EXIT` when the seat is an exit row and the passenger's
`infant_count` is greater than 0.

```text
INF_EXIT_ROW: seat.exit_row == true and pax.infant_count > 0 -> reject INF_EXIT
```

This is the rules-table form of the legacy TPF check, per the HLD decision.
