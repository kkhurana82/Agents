---
okf_version: '0.3'
title: 'Code: dcs-seat (TPF C)'
description: 'Legacy seat allocation code: modules, seat eligibility rules and record layouts. Use it
  for how the legacy DCS enforces seat rules.'
---

# Code: dcs-seat (TPF C)

## Business Rule

* [Infant passenger may not be assigned an exit-row seat](/rules/seatalloc/infant_rules.c/check_exit_row_infant/eligibility-353743.md) - check_exit_row_infant rejects an exit-row seat (SEAT_REJ_INF_EXIT) when the passenger has a lap infant.

## Data Entity

* [pax_t passenger record](/data/seatalloc/seat_types.h/pax_t.md) - Passenger record used by seat allocation; infant_count holds the number of lap infants.

## Module

* [seatalloc/infant_rules.c](/modules/seatalloc/infant_rules.c.md) - Infant-related seat eligibility checks called during seat assignment.
