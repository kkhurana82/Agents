---
okf_version: '0.3'
title: 'HLD: HLD-DCS-SEAT-002'
description: Seat assignment modernisation decisions and designs. Use it for why seat eligibility is moving
  to a rules table.
---

# HLD: HLD-DCS-SEAT-002

## Decision

* [Seat eligibility rules move to a rules table](/decisions/HLD-DCS-SEAT-002/dec-seat-eligibility-rules-table.md) - Seat eligibility checks become rows in the modernised seat service's rules table; legacy C checks stay authoritative until cut-over.

## Design

* [Seat eligibility evaluation in the seat service](/designs/HLD-DCS-SEAT-002/des-seat-eligibility-service.md) - The seat service evaluates active eligibility rules per passenger-seat pair and returns the first reject reason.
