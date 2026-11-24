---
okf_version: '0.3'
title: 'Code: seat-service (Java, OpenAPI, Terraform)'
description: 'Modernised seat service: rules table, REST API, events and the GCP resources behind them.
  Use it for how the new seat service works and is deployed.'
---

# Code: seat-service (Java, OpenAPI, Terraform)

## Business Rule

* [INF_EXIT_ROW: infant passenger may not take an exit-row seat (rules table)](/rules/src/main/resources/rules/seat-eligibility.yaml/INF_EXIT_ROW/eligibility-0945ef.md) - Rules-table row INF_EXIT_ROW rejects an exit-row seat with INF_EXIT when the passenger has a lap infant.

## Infra Resource

* [Pub/Sub topic seat-assigned](/infra/terraform/pubsub.tf/google_pubsub_topic.seat_assigned.md) - Terraform-managed GCP Pub/Sub topic that carries seat-assigned events, retained for one day.

## Interface

* [PUT /passengers/{paxId}/seat (assignSeat)](/interfaces/api/seat-api.yaml/assignSeat.md) - REST operation that assigns a seat or returns 422 with a reason code such as INF_EXIT.
* [seat-assigned event (publishSeatAssigned)](/interfaces/src/main/java/com/example/seat/EligibilityService.java/publishSeatAssigned.md) - Event published to Pub/Sub topic seat-assigned after a seat is assigned.

## Module

* [EligibilityService (seat service)](/modules/src/main/java/com/example/seat/EligibilityService.java.md) - Spring service that evaluates the seat rules table and publishes seat-assigned events.
