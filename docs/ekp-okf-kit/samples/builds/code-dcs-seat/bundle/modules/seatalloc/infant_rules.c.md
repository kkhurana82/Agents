---
type: Module
title: seatalloc/infant_rules.c
description: Infant-related seat eligibility checks called during seat assignment.
tags:
- seat-eligibility
- infant
status: stable
generated:
  by: ekp-tpfc-extractor/0.4
  at: '2026-09-14T08:00:00Z'
verified:
- by: process:ekp-rule-check
  at: '2026-11-24T18:05:00Z'
sources:
- id: code
  resource: https://git.example.com/dcs-seat/blob/9c1e2f7a4b0d/seatalloc/infant_rules.c
  title: seatalloc/infant_rules.c
extra:
  aspects:
    acme-ekp.us-central1.ekp-core:
      concept_id: code-dcs-seat:modules/seatalloc/infant_rules.c
      concept_type: Module
      lifecycle: stable
      domain: departure-control
      primary_system: system:dcs
      primary_component: component:dcs.seat-assignment
      source_kind: code
      source_system: git
      source_ref: git:dcs-seat:seatalloc/infant_rules.c
      source_revision: 9c1e2f7a4b0d
      source_url: https://git.example.com/dcs-seat/blob/9c1e2f7a4b0d/seatalloc/infant_rules.c
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
      - term:infant
      relations:
      - rel: enforces
        target: code-dcs-seat:rules/seatalloc/infant_rules.c/check_exit_row_infant/eligibility-353743
      - rel: reads
        target: code-dcs-seat:data/seatalloc/seat_types.h/pax_t
    acme-ekp.us-central1.ekp-module:
      language: tpf-c
      module_kind: program
---

<!-- ekp:header v1 -->
> **Module** · departure-control › system:dcs › component:dcs.seat-assignment
> **Source:** `git:dcs-seat:seatalloc/infant_rules.c` @ `9c1e2f7a4b0d` · extraction: deterministic
> **Trust:** machine_confirmed · **Status:** stable · **Valid from:** 2026-09-14
> **Also about:** `term:infant`
> **Relations:** enforces `code-dcs-seat:rules/seatalloc/infant_rules.c/check_exit_row_infant/eligibility-353743`; reads `code-dcs-seat:data/seatalloc/seat_types.h/pax_t`
<!-- /ekp:header -->

# Purpose

Holds infant-related seat eligibility checks. Seat assignment calls
`check_exit_row_infant()` before committing a seat.

# Functions

* `check_exit_row_infant(pax, seat)` - rejects exit-row seats for passengers with infants.
