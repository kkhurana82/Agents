# ADR-0007: Seat availability read model

## Status
Accepted

## Decision
Display paths read seat availability from an event-fed read model (SeatMapView) updated from SeatAssigned and
SeatReleased events. The seat assignment service remains the system of record and validates every assignment
synchronously at commit time.

## Consequences
Display may lag the system of record by up to a few seconds; the commit-time check prevents double assignment.
