---
type: Design
title: Seat eligibility evaluation in the seat service
description: The seat service evaluates active eligibility rules per passenger-seat pair and returns the
  first reject reason.
tags:
- seat-eligibility
status: stable
generated:
  by: ekp-hld-adapter/0.2
  at: '2026-08-20T00:00:00Z'
sources:
- id: hld
  resource: https://git.example.com/arch-docs/blob/a77d01c/HLD-DCS-SEAT-002.adoc
  title: HLD-DCS-SEAT-002 Seat Assignment Modernisation
  author: team:dcs-architecture
extra:
  aspects:
    acme-ekp.us-central1.ekp-core:
      concept_id: hld-dcs-seat:designs/HLD-DCS-SEAT-002/des-seat-eligibility-service
      concept_type: Design
      lifecycle: stable
      domain: departure-control
      primary_system: system:dcs
      primary_component: component:dcs.seat-assignment
      source_kind: arch_doc
      source_system: git
      source_ref: hld:HLD-DCS-SEAT-002#des-seat-eligibility-service
      source_revision: a77d01c3e9f2
      source_url: https://git.example.com/arch-docs/blob/a77d01c/HLD-DCS-SEAT-002.adoc
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
      relations:
      - rel: governed_by
        target: hld-dcs-seat:decisions/HLD-DCS-SEAT-002/dec-seat-eligibility-rules-table
      - rel: describes
        target: code-dcs-seat:rules/seatalloc/infant_rules.c/check_exit_row_infant/eligibility-353743
---

<!-- ekp:header v1 -->
> **Design** · departure-control › system:dcs › component:dcs.seat-assignment
> **Source:** `hld:HLD-DCS-SEAT-002#des-seat-eligibility-service` @ `a77d01c3e9f2` · extraction: template
> **Trust:** unverified · **Status:** stable · **Valid from:** 2026-08-20
> **Also about:** `capability:seat-eligibility`
> **Relations:** governed by `hld-dcs-seat:decisions/HLD-DCS-SEAT-002/dec-seat-eligibility-rules-table`; describes `code-dcs-seat:rules/seatalloc/infant_rules.c/check_exit_row_infant/eligibility-353743`
<!-- /ekp:header -->

# Design

The seat service loads active rules for the flight, evaluates them per
passenger-seat pair and returns the first reject reason. Infant, exit-row and
cabin rules run before price rules.
