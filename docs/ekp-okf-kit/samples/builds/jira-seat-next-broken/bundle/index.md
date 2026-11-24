---
okf_version: '0.3'
title: 'Jira: SEAT'
description: 'Seat epics: what changed, when and in which release. Use it for change history.'
---

# Jira: SEAT

## Change

* [SEAT-412: Re-check exit-row eligibility when an infant is added after seat assignment](/changes/SEAT-412.md) - Exit-row infant check now re-runs when an infant is added to a seated passenger and on kiosk seat changes (release 2026.10).
* [SEAT-430: Kiosk exit-row re-check](/changes/kiosk-exit-row-recheck.md) - Kiosk re-runs the exit-row check after a seat change.

## Decision

* [Kiosk uses the same eligibility call as the agent seat map](/decisions/SEAT-412/c88123.md) - Agreed in SEAT-412 comments: kiosk seat changes call check_exit_row_infant like the agent flow.
