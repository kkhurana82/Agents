---
type: Change
title: 'SEAT-401: Show infant-restricted seats on the seat map'
description: Seat map greys out seats a passenger with an infant may not select.
tags:
- seat-eligibility
status: stable
generated:
  by: ekp-jira-adapter/0.3
  at: '2026-10-02T11:20:00Z'
sources:
- id: seat-401
  resource: https://jira.example.com/browse/SEAT-401
  title: SEAT-401
- id: seat-402
  resource: https://jira.example.com/browse/SEAT-402
  title: SEAT-402 Grey out exit-row seats for passengers with infants
extra:
  aspects:
    acme-ekp.us-central1.ekp-core:
      concept_id: jira-seat:changes/SEAT-401
      concept_type: Change
      lifecycle: stable
      domain: departure-control
      primary_system: system:dcs
      primary_component: component:dcs.seat-assignment
      primary_capability: capability:seat-eligibility
      source_kind: jira
      source_system: jira
      source_ref: jira:SEAT-401
      source_revision: '2026-10-02T11:20:00Z'
      source_url: https://jira.example.com/browse/SEAT-401
      extraction: deterministic
      trust_tier: unverified
      valid_from: '2026-10-02T11:20:00Z'
      owner_team: team:dcs-seating
      build_id: jira-seat-20261124T180000Z
      profile: jira@1
      ontology_version: '1.1'
      anchors:
      - system:dcs
      - component:dcs.seat-assignment
      - capability:seat-eligibility
      relations: []
    acme-ekp.us-central1.ekp-change:
      change_status: done
      release: '2026.09'
---

<!-- ekp:header v1 -->
> **Change** · departure-control › system:dcs › component:dcs.seat-assignment
> **Source:** `jira:SEAT-401` @ `2026-10-02T11:20:00Z` · extraction: deterministic
> **Trust:** unverified · **Status:** stable · **Valid from:** 2026-10-02
> **Also about:** `capability:seat-eligibility`
<!-- /ekp:header -->

# Change

Seat map greys out seats a passenger with an infant may not select.

# Work items

* SEAT-402 (Story): Grey out exit-row seats for passengers with infants
