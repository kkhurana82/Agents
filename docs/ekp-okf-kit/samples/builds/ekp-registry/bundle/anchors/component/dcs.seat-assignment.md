---
type: Component
title: Seat Assignment
description: Allocates and changes seats, applying seat eligibility rules.
status: stable
generated:
  by: human:registry-owners
  at: '2026-07-01T00:00:00Z'
verified:
- by: human:registry-owners
  at: '2026-07-01T00:00:00Z'
sources:
- id: reg
  resource: anchors/registry.yaml
  title: EKP anchor registry
extra:
  aspects:
    acme-ekp.us-central1.ekp-core:
      concept_id: ekp-registry:anchors/component/dcs.seat-assignment
      concept_type: Component
      lifecycle: stable
      domain: departure-control
      source_kind: registry
      source_system: git
      source_ref: registry:component:dcs.seat-assignment
      source_revision: reg-v1.0
      extraction: human
      trust_tier: human_reviewed
      valid_from: '2026-07-01T00:00:00Z'
      owner_team: team:ekp-registry
      build_id: ekp-registry-20261124T180000Z
      profile: registry@1
      ontology_version: '1.1'
---

<!-- ekp:header v1 -->
> **Component** · departure-control
> **Source:** `registry:component:dcs.seat-assignment` @ `reg-v1.0` · extraction: human
> **Trust:** human_reviewed · **Status:** stable · **Valid from:** 2026-07-01
<!-- /ekp:header -->

# Seat Assignment

Allocates and changes seats, applying seat eligibility rules.

**Also known as:** `seat assignment`, `seatalloc`, `seat-alloc`, `seat-service`, `SA`, `Seating`
