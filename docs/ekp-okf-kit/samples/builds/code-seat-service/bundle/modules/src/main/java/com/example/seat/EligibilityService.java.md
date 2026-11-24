---
type: Module
title: EligibilityService (seat service)
description: Spring service that evaluates the seat rules table and publishes seat-assigned events.
tags:
- seat-eligibility
status: stable
generated:
  by: ekp-java-extractor/0.1
  at: '2026-10-01T00:00:00Z'
verified:
- by: process:ekp-parity-check
  at: '2026-11-24T18:05:00Z'
sources:
- id: src
  resource: https://git.example.com/seat-service/blob/4be09a1c77d2/src/main/java/com/example/seat/EligibilityService.java
extra:
  aspects:
    acme-ekp.us-central1.ekp-core:
      concept_id: code-seat-service:modules/src/main/java/com/example/seat/EligibilityService.java
      concept_type: Module
      lifecycle: stable
      domain: departure-control
      primary_system: system:dcs
      primary_component: component:dcs.seat-assignment
      source_kind: code
      source_system: git
      source_ref: git:seat-service:src/main/java/com/example/seat/EligibilityService.java
      source_revision: 4be09a1c77d2
      extraction: deterministic
      trust_tier: machine_confirmed
      valid_from: '2026-10-01T00:00:00Z'
      owner_team: team:dcs-seating
      build_id: code-seat-service-20261124T180000Z
      profile: code-repo@2
      ontology_version: '1.1'
      anchors:
      - system:dcs
      - component:dcs.seat-assignment
      - capability:seat-eligibility
      relations:
      - rel: enforces
        target: code-seat-service:rules/src/main/resources/rules/seat-eligibility.yaml/INF_EXIT_ROW/eligibility-0945ef
      - rel: exposes
        target: code-seat-service:interfaces/api/seat-api.yaml/assignSeat
      - rel: calls
        target: code-seat-service:interfaces/src/main/java/com/example/seat/EligibilityService.java/publishSeatAssigned
    acme-ekp.us-central1.ekp-module:
      language: java
      module_kind: service
---

<!-- ekp:header v1 -->
> **Module** · departure-control › system:dcs › component:dcs.seat-assignment
> **Source:** `git:seat-service:src/main/java/com/example/seat/EligibilityService.java` @ `4be09a1c77d2` · extraction: deterministic
> **Trust:** machine_confirmed · **Status:** stable · **Valid from:** 2026-10-01
> **Also about:** `capability:seat-eligibility`
> **Relations:** enforces `code-seat-service:rules/src/main/resources/rules/seat-eligibility.yaml/INF_EXIT_ROW/eligibility-0945ef`; exposes `code-seat-service:interfaces/api/seat-api.yaml/assignSeat`; calls `code-seat-service:interfaces/src/main/java/com/example/seat/EligibilityService.java/publishSeatAssigned`
<!-- /ekp:header -->

# Purpose

`assignSeat()` asks the rules table for the first reject reason. If there is
none, it assigns the seat and publishes a `seat-assigned` event.
