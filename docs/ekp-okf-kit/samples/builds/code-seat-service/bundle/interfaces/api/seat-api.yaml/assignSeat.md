---
type: Interface
title: PUT /passengers/{paxId}/seat (assignSeat)
description: REST operation that assigns a seat or returns 422 with a reason code such as INF_EXIT.
tags:
- seat-eligibility
status: stable
generated:
  by: ekp-openapi-extractor/0.1
  at: '2026-10-01T00:00:00Z'
sources:
- id: spec
  resource: https://git.example.com/seat-service/blob/4be09a1c77d2/api/seat-api.yaml
extra:
  aspects:
    acme-ekp.us-central1.ekp-core:
      concept_id: code-seat-service:interfaces/api/seat-api.yaml/assignSeat
      concept_type: Interface
      lifecycle: stable
      domain: departure-control
      primary_system: system:dcs
      primary_component: component:dcs.seat-assignment
      source_kind: code
      source_system: git
      source_ref: git:seat-service:api/seat-api.yaml#assignSeat
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
    acme-ekp.us-central1.ekp-interface:
      protocol: rest
      direction: inbound
---

<!-- ekp:header v1 -->
> **Interface** · departure-control › system:dcs › component:dcs.seat-assignment
> **Source:** `git:seat-service:api/seat-api.yaml#assignSeat` @ `4be09a1c77d2` · extraction: deterministic
> **Trust:** unverified · **Status:** stable · **Valid from:** 2026-10-01
<!-- /ekp:header -->

# Contract

`PUT /passengers/{paxId}/seat`, operationId `assignSeat`, Seat API 1.4.0.

| Status | Meaning |
|---|---|
| 200 | Seat assigned |
| 422 | Seat not allowed, with a reason code (for example `INF_EXIT`) |
