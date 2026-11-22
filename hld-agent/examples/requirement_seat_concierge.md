# Seat Concierge - natural-language seat requests at check-in

## Context
Passengers ask for seats in natural language ("window seat near my colleague, not in the last rows").
Agents translate these by hand today. We want a service that turns a request into a valid seat assignment
using the existing DCS seat map and seat assignment rules.

## Goals
- Reduce agent handling time for seat change requests
- Increase self-service seat changes in web and mobile check-in

## Functional requirements
- Accept a free-text seat request for a checked-in or check-in-eligible passenger on a flight
- Return up to three valid candidate seats ranked by fit, with a short explanation for each
- Assign the chosen seat through the existing seat assignment path so all carrier rules and restrictions apply
- Keep party members seated together when the request mentions companions on the same PNR

## Non-functional requirements
- Candidate seats returned within p95 1.5 s
- 99.9% availability during check-in windows
- No personal data sent to external model providers beyond the request text

## Constraints
- Seat assignment must go through the existing seat assignment service; no direct seat map writes

## Out of scope
- Paid seat upsell and pricing
