---
type: Requirement
title: 'BR-SEAT-014: no exit-row seat for a passenger travelling with an infant'
description: The system shall not assign a seat in an exit row to a passenger travelling with an infant.
tags:
- seat-eligibility
- infant
- exit-row
status: stable
generated:
  by: ekp-brd-adapter/0.3
  at: '2026-03-02T00:00:00Z'
verified:
- by: human:ba-signoff
  at: '2026-03-05T09:00:00Z'
sources:
- id: brd
  resource: https://wiki.example.com/display/BRD/BRD-SEAT
  title: BRD-SEAT Seat Assignment
  author: team:dcs-product
extra:
  aspects:
    acme-ekp.us-central1.ekp-core:
      concept_id: brd-seat:requirements/BRD-SEAT/BR-SEAT-014
      concept_type: Requirement
      lifecycle: stable
      domain: departure-control
      primary_system: system:dcs
      primary_component: component:dcs.seat-assignment
      primary_capability: capability:seat-eligibility
      source_kind: brd
      source_system: confluence
      source_ref: brd:BRD-SEAT#BR-SEAT-014
      source_revision: v12
      source_url: https://wiki.example.com/display/BRD/BRD-SEAT
      extraction: template
      trust_tier: human_reviewed
      valid_from: '2026-03-02T00:00:00Z'
      owner_team: team:dcs-product
      build_id: brd-seat-20261124T180000Z
      profile: brd@1
      ontology_version: '1.1'
      anchors:
      - system:dcs
      - component:dcs.seat-assignment
      - capability:seat-eligibility
      - term:infant
      - term:exit-row
      relations:
      - rel: specifies
        target: brd-seat:rules/BRD-SEAT/BR-SEAT-014/eligibility-3ade07
    acme-ekp.us-central1.ekp-requirement:
      req_id: BR-SEAT-014
      req_kind: functional
      priority: must
      req_status: implemented
---

<!-- ekp:header v1 -->
> **Requirement** · departure-control › system:dcs › component:dcs.seat-assignment
> **Source:** `brd:BRD-SEAT#BR-SEAT-014` @ `v12` · extraction: template
> **Trust:** human_reviewed · **Status:** stable · **Valid from:** 2026-03-02
> **Also about:** `capability:seat-eligibility`, `term:infant`, `term:exit-row`
> **Relations:** specifies `brd-seat:rules/BRD-SEAT/BR-SEAT-014/eligibility-3ade07`
<!-- /ekp:header -->

# Requirement

The system shall not assign a seat in an exit row to a passenger travelling
with an infant.[^brd]

| Priority | Status |
|---|---|
| Must | Implemented |

[^brd]: BRD-SEAT section 4, row BR-SEAT-014
