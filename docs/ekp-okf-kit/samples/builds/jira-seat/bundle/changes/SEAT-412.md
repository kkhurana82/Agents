---
type: Change
title: 'SEAT-412: Re-check exit-row eligibility when an infant is added after seat assignment'
description: Exit-row infant check now re-runs when an infant is added to a seated passenger and on kiosk
  seat changes (release 2026.10).
tags:
- seat-eligibility
status: stable
generated:
  by: ekp-jira-adapter/0.3
  at: '2026-10-02T11:20:00Z'
sources:
- id: seat-412
  resource: https://jira.example.com/browse/SEAT-412
  title: SEAT-412
- id: seat-415
  resource: https://jira.example.com/browse/SEAT-415
  title: SEAT-415 Run exit-row infant check when an infant is added to a seated passenger
- id: seat-419
  resource: https://jira.example.com/browse/SEAT-419
  title: SEAT-419 Exit-row infant check skipped on kiosk seat change
extra:
  aspects:
    acme-ekp.us-central1.ekp-core:
      concept_id: jira-seat:changes/SEAT-412
      concept_type: Change
      lifecycle: stable
      domain: departure-control
      primary_system: system:dcs
      primary_component: component:dcs.seat-assignment
      primary_capability: capability:seat-eligibility
      source_kind: jira
      source_system: jira
      source_ref: jira:SEAT-412
      source_revision: '2026-10-02T11:20:00Z'
      source_url: https://jira.example.com/browse/SEAT-412
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
      relations:
      - rel: changes
        target: code-dcs-seat:rules/seatalloc/infant_rules.c/check_exit_row_infant/eligibility-353743
    acme-ekp.us-central1.ekp-change:
      change_status: done
      release: '2026.10'
---

<!-- ekp:header v1 -->
> **Change** · departure-control › system:dcs › component:dcs.seat-assignment
> **Source:** `jira:SEAT-412` @ `2026-10-02T11:20:00Z` · extraction: deterministic
> **Trust:** unverified · **Status:** stable · **Valid from:** 2026-10-02
> **Also about:** `capability:seat-eligibility`
> **Relations:** changes `code-dcs-seat:rules/seatalloc/infant_rules.c/check_exit_row_infant/eligibility-353743`
<!-- /ekp:header -->

# Change

Exit-row infant check now re-runs when an infant is added to a seated passenger and on kiosk seat changes (release 2026.10).

# Work items

* SEAT-415 (Story): Run exit-row infant check when an infant is added to a seated passenger
* SEAT-419 (Bug): Exit-row infant check skipped on kiosk seat change
