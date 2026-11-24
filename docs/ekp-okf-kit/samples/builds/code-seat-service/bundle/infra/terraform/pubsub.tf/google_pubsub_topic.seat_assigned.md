---
type: Infra Resource
title: Pub/Sub topic seat-assigned
description: Terraform-managed GCP Pub/Sub topic that carries seat-assigned events, retained for one day.
status: stable
generated:
  by: ekp-terraform-extractor/0.1
  at: '2026-10-01T00:00:00Z'
sources:
- id: tf
  resource: https://git.example.com/seat-service/blob/4be09a1c77d2/terraform/pubsub.tf
extra:
  aspects:
    acme-ekp.us-central1.ekp-core:
      concept_id: code-seat-service:infra/terraform/pubsub.tf/google_pubsub_topic.seat_assigned
      concept_type: InfraResource
      lifecycle: stable
      domain: departure-control
      primary_system: system:dcs
      primary_component: component:dcs.seat-assignment
      source_kind: code
      source_system: git
      source_ref: git:seat-service:terraform/pubsub.tf#google_pubsub_topic.seat_assigned
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
    acme-ekp.us-central1.ekp-infra:
      tool: terraform
      provider: gcp
      resource_kind: google_pubsub_topic
---

<!-- ekp:header v1 -->
> **Infra Resource** · departure-control › system:dcs › component:dcs.seat-assignment
> **Source:** `git:seat-service:terraform/pubsub.tf#google_pubsub_topic.seat_assigned` @ `4be09a1c77d2` · extraction: deterministic
> **Trust:** unverified · **Status:** stable · **Valid from:** 2026-10-01
<!-- /ekp:header -->

# Resource

`google_pubsub_topic.seat_assigned` in `terraform/pubsub.tf`.

| Attribute | Value |
|---|---|
| name | seat-assigned |
| message_retention_duration | 86400s |
| labels | system=dcs, component=seat-assignment |
