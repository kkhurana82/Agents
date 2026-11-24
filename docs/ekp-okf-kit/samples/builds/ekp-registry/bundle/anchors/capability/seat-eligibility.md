---
type: Capability
title: Seat eligibility
description: Deciding which passengers may occupy which seats.
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
      concept_id: ekp-registry:anchors/capability/seat-eligibility
      concept_type: Capability
      lifecycle: stable
      domain: departure-control
      source_kind: registry
      source_system: git
      source_ref: registry:capability:seat-eligibility
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
> **Capability** · departure-control
> **Source:** `registry:capability:seat-eligibility` @ `reg-v1.0` · extraction: human
> **Trust:** human_reviewed · **Status:** stable · **Valid from:** 2026-07-01
<!-- /ekp:header -->

# Seat eligibility

Deciding which passengers may occupy which seats.

**Also known as:** `seat eligibility`, `seat restrictions`
