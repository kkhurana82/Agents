---
type: Decision
title: Seat eligibility rules move to a rules table
description: Seat eligibility checks become rows in the modernised seat service's rules table; legacy
  C checks are retired on 2027-03-31.
tags:
- seat-eligibility
- modernisation
status: stable
generated:
  by: ekp-hld-adapter/0.2
  at: '2026-11-25T05:40:00Z'
verified:
- by: human:arch-review-board
  at: '2026-08-21T10:00:00Z'
sources:
- id: hld
  resource: https://git.example.com/arch-docs/blob/b81f2e0/HLD-DCS-SEAT-002.adoc
  title: HLD-DCS-SEAT-002 Seat Assignment Modernisation
  author: team:dcs-architecture
extra:
  aspects:
    acme-ekp.us-central1.ekp-core:
      concept_id: hld-dcs-seat:decisions/HLD-DCS-SEAT-002/dec-seat-eligibility-rules-table
      concept_type: Decision
      lifecycle: stable
      domain: departure-control
      primary_system: system:dcs
      primary_component: component:dcs.seat-assignment
      primary_capability: capability:seat-eligibility
      source_kind: arch_doc
      source_system: git
      source_ref: hld:HLD-DCS-SEAT-002#dec-seat-eligibility-rules-table
      source_revision: b81f2e0d44aa
      source_url: https://git.example.com/arch-docs/blob/b81f2e0/HLD-DCS-SEAT-002.adoc
      extraction: template
      trust_tier: unverified
      valid_from: '2026-08-20T00:00:00Z'
      owner_team: team:dcs-architecture
      build_id: hld-dcs-seat-20261125T060000Z
      profile: arch-doc@1
      ontology_version: '1.1'
      anchors:
      - system:dcs
      - component:dcs.seat-assignment
      - capability:seat-eligibility
    acme-ekp.us-central1.ekp-decision:
      decision_status: accepted
      decided_on: '2026-08-20T00:00:00Z'
---

<!-- ekp:header v1 -->
> **Decision** · departure-control › system:dcs › component:dcs.seat-assignment
> **Source:** `hld:HLD-DCS-SEAT-002#dec-seat-eligibility-rules-table` @ `b81f2e0d44aa` · extraction: template
> **Trust:** unverified · **Status:** stable · **Valid from:** 2026-08-20
> **Also about:** `capability:seat-eligibility`
<!-- /ekp:header -->

# Decision

Express seat eligibility rules as rows in the modernised seat service's rules
table. Legacy C checks are retired on 2027-03-31.[^hld]

# Context

Eligibility checks such as infant-in-exit-row are hard-coded per C function,
so every change needs a release.

# Consequences

Rules become data with owners and effective dates. Every legacy rule needs a
one-to-one migration and a parity test.

[^hld]: HLD-DCS-SEAT-002, section dec-seat-eligibility-rules-table
