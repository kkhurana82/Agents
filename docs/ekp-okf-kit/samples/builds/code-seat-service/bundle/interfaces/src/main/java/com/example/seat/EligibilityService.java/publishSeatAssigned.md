---
type: Interface
title: seat-assigned event (publishSeatAssigned)
description: Event published to Pub/Sub topic seat-assigned after a seat is assigned.
status: stable
generated:
  by: ekp-java-extractor/0.1
  at: '2026-10-01T00:00:00Z'
sources:
- id: src
  resource: https://git.example.com/seat-service/blob/4be09a1c77d2/src/main/java/com/example/seat/EligibilityService.java
extra:
  aspects:
    acme-ekp.us-central1.ekp-core:
      concept_id: code-seat-service:interfaces/src/main/java/com/example/seat/EligibilityService.java/publishSeatAssigned
      concept_type: Interface
      lifecycle: stable
      domain: departure-control
      primary_system: system:dcs
      primary_component: component:dcs.seat-assignment
      source_kind: code
      source_system: git
      source_ref: git:seat-service:src/main/java/com/example/seat/EligibilityService.java#publishSeatAssigned
      source_revision: 4be09a1c77d2
      extraction: deterministic
      trust_tier: unverified
      valid_from: '2026-10-01T00:00:00Z'
      owner_team: team:dcs-seating
      build_id: code-seat-service-20261124T180000Z
      profile: code-repo@2
      ontology_version: '1.1'
      anchors:
      - system:dcs
      - component:dcs.seat-assignment
      relations:
      - rel: provisioned_by
        target: code-seat-service:infra/terraform/pubsub.tf/google_pubsub_topic.seat_assigned
    acme-ekp.us-central1.ekp-interface:
      protocol: pubsub
      direction: outbound
---

<!-- ekp:header v1 -->
> **Interface** · departure-control › system:dcs › component:dcs.seat-assignment
> **Source:** `git:seat-service:src/main/java/com/example/seat/EligibilityService.java#publishSeatAssigned` @ `4be09a1c77d2` · extraction: deterministic
> **Trust:** unverified · **Status:** stable · **Valid from:** 2026-10-01
> **Relations:** provisioned by `code-seat-service:infra/terraform/pubsub.tf/google_pubsub_topic.seat_assigned`
<!-- /ekp:header -->

# Contract

Published by `EligibilityService.assignSeat()` after a successful assignment.
