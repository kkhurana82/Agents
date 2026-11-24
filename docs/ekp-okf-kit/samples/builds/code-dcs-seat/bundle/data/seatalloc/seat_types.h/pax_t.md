---
type: Data Entity
title: pax_t passenger record
description: Passenger record used by seat allocation; infant_count holds the number of lap infants.
tags:
- infant
status: stable
generated:
  by: ekp-tpfc-extractor/0.4
  at: '2026-09-14T08:00:00Z'
verified:
- by: process:ekp-rule-check
  at: '2026-11-24T18:05:00Z'
sources:
- id: hdr
  resource: https://git.example.com/dcs-seat/blob/9c1e2f7a4b0d/seatalloc/seat_types.h
  title: seatalloc/seat_types.h
extra:
  aspects:
    acme-ekp.us-central1.ekp-core:
      concept_id: code-dcs-seat:data/seatalloc/seat_types.h/pax_t
      concept_type: DataEntity
      lifecycle: stable
      domain: departure-control
      primary_system: system:dcs
      primary_component: component:dcs.seat-assignment
      source_kind: code
      source_system: git
      source_ref: git:dcs-seat:seatalloc/seat_types.h#pax_t
      source_revision: 9c1e2f7a4b0d
      source_url: https://git.example.com/dcs-seat/blob/9c1e2f7a4b0d/seatalloc/seat_types.h
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
---

<!-- ekp:header v1 -->
> **Data Entity** · departure-control › system:dcs › component:dcs.seat-assignment
> **Source:** `git:dcs-seat:seatalloc/seat_types.h#pax_t` @ `9c1e2f7a4b0d` · extraction: deterministic
> **Trust:** machine_confirmed · **Status:** stable · **Valid from:** 2026-09-14
> **Also about:** `term:infant`
<!-- /ekp:header -->

# Schema

| Field | Type | Meaning |
|---|---|---|
| surname | char[32] | Passenger surname |
| infant_count | short | Lap infants travelling with this passenger |
| cabin | char | Booked cabin |
