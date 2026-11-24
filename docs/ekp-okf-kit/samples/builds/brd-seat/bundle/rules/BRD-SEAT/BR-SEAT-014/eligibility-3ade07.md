---
type: Business Rule
title: Exit-row seat rejected when passenger has an infant (as stated in BR-SEAT-014)
description: 'Business rule extracted from BR-SEAT-014: reject an exit-row seat if the passenger travels
  with an infant.'
tags:
- seat-eligibility
- infant
- exit-row
status: draft
generated:
  by: ekp-brd-adapter/0.3+gemini-2.5-pro
  at: '2026-11-24T18:00:00Z'
sources:
- id: brd
  resource: https://wiki.example.com/display/BRD/BRD-SEAT
  title: BRD-SEAT Seat Assignment
  author: team:dcs-product
extra:
  aspects:
    acme-ekp.us-central1.ekp-core:
      concept_id: brd-seat:rules/BRD-SEAT/BR-SEAT-014/eligibility-3ade07
      concept_type: BusinessRule
      lifecycle: draft
      domain: departure-control
      primary_system: system:dcs
      primary_component: component:dcs.seat-assignment
      primary_capability: capability:seat-eligibility
      source_kind: brd
      source_system: confluence
      source_ref: brd:BRD-SEAT#BR-SEAT-014/eligibility-3ade07
      source_revision: v12
      source_url: https://wiki.example.com/display/BRD/BRD-SEAT
      extraction: llm
      confidence: 0.91
      trust_tier: unverified
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
      - rel: same_as
        target: code-dcs-seat:rules/seatalloc/infant_rules.c/check_exit_row_infant/eligibility-353743
    acme-ekp.us-central1.ekp-rule:
      rule_kind: eligibility
      enforcement: unknown
---

<!-- ekp:header v1 -->
> **Business Rule** · departure-control › system:dcs › component:dcs.seat-assignment
> **Source:** `brd:BRD-SEAT#BR-SEAT-014/eligibility-3ade07` @ `v12` · extraction: llm (0.91)
> **Trust:** unverified · **Status:** draft · **Valid from:** 2026-03-02
> **Also about:** `capability:seat-eligibility`, `term:infant`, `term:exit-row`
> **Relations:** same as `code-dcs-seat:rules/seatalloc/infant_rules.c/check_exit_row_infant/eligibility-353743`
<!-- /ekp:header -->

# Rule

Reject an exit-row seat when the passenger travels with an infant.

```text
exit_row(seat) and infant_count(pax) > 0 => reject
```
