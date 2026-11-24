---
type: Change
title: 'SEAT-430: Kiosk exit-row re-check'
description: Kiosk re-runs the exit-row check after a seat change.
status: stable
generated:
  by: ekp-jira-adapter/0.3
  at: '2026-11-25T06:00:00Z'
sources:
- id: seat-430
  resource: https://jira.example.com/browse/SEAT-430
extra:
  aspects:
    acme-ekp.us-central1.ekp-core:
      concept_id: jira-seat:changes/kiosk-exit-row-recheck
      concept_type: Change
      lifecycle: stable
      domain: departure-control
      primary_system: system:dcs
      source_kind: jira
      source_system: jira
      source_ref: jira:SEAT-430
      source_revision: '2026-11-20T09:00:00Z'
      extraction: deterministic
      trust_tier: unverified
      valid_from: '2026-11-20T09:00:00Z'
      owner_team: team:dcs-seating
      build_id: jira-seat-20261125T060000Z
      profile: jira@1
      ontology_version: '1.1'
      anchors:
      - system:dcs
    acme-ekp.us-central1.ekp-change:
      change_status: in_progress
---

<!-- ekp:header v1 -->
> **Change** · departure-control › system:dcs
> **Source:** `jira:SEAT-430` @ `2026-11-20T09:00:00Z` · extraction: deterministic
> **Trust:** unverified · **Status:** stable · **Valid from:** 2026-11-20
<!-- /ekp:header -->

# Change

Kiosk re-runs the exit-row check after a seat change.
