# Worked examples: one per source kind

All inputs are synthetic. One storyline runs through every source: *a passenger travelling with an infant may not sit in an exit row*. Each source contributes a different kind of knowledge, and all five share anchors, so retrieval can join them.

## 1. Code repo (TPF C)

Profile `code-repo` → entry group `code-dcs-seat` → concept `rules/seatalloc/infant_rules.c/check_exit_row_infant/eligibility-353743`

### Input

```
/*
 * seatalloc/infant_rules.c
 * SYNTHETIC SAMPLE for the EKP OKF kit. Not real airline code.
 */
#include "seat_types.h"

/* Returns SEAT_OK, or a reject code if the passenger may not take the seat. */
int check_exit_row_infant(const pax_t *pax, const seat_t *seat)
{
    if (seat->attrs & SEAT_ATTR_EXIT_ROW) {
        if (pax->infant_count > 0) {
            return SEAT_REJ_INF_EXIT;   /* infant may not sit in an exit row */
        }
    }
    return SEAT_OK;
}
```

### OKF concept written by the build

````markdown
---
type: Business Rule
title: Infant passenger may not be assigned an exit-row seat
description: check_exit_row_infant rejects an exit-row seat (SEAT_REJ_INF_EXIT) when the passenger has
  a lap infant.
tags:
- seat-eligibility
- infant
- exit-row
status: stable
generated:
  by: ekp-tpfc-extractor/0.4
  at: '2026-09-14T08:00:00Z'
verified:
- by: process:ekp-rule-check
  at: '2026-11-24T18:05:00Z'
sources:
- id: code
  resource: https://git.example.com/dcs-seat/blob/9c1e2f7a4b0d/seatalloc/infant_rules.c#L9-L16
  title: seatalloc/infant_rules.c
  last_modified: '2026-09-14T08:00:00Z'
extra:
  aspects:
    acme-ekp.us-central1.ekp-core:
      concept_id: code-dcs-seat:rules/seatalloc/infant_rules.c/check_exit_row_infant/eligibility-353743
      concept_type: BusinessRule
      lifecycle: stable
      domain: departure-control
      primary_system: system:dcs
      primary_component: component:dcs.seat-assignment
      primary_capability: capability:seat-eligibility
      source_kind: code
      source_system: git
      source_ref: git:dcs-seat:seatalloc/infant_rules.c#check_exit_row_infant/eligibility-353743
      source_revision: 9c1e2f7a4b0d
      source_url: https://git.example.com/dcs-seat/blob/9c1e2f7a4b0d/seatalloc/infant_rules.c#L9-L16
      extraction: deterministic
      trust_tier: machine_confirmed
      valid_from: '2026-09-14T08:00:00Z'
      owner_team: team:dcs-seating
      build_id: code-dcs-seat-20261124T180000Z
      profile: code-repo@2
      ontology_version: '1.1'
      anchors:
      - system:dcs
      - component:dcs.seat-assignment
      - capability:seat-eligibility
      - term:infant
      - term:exit-row
      relations:
      - rel: implements
        target: brd-seat:requirements/BRD-SEAT/BR-SEAT-014
      - rel: governed_by
        target: hld-dcs-seat:decisions/HLD-DCS-SEAT-002/dec-seat-eligibility-rules-table
    acme-ekp.us-central1.ekp-rule:
      rule_kind: eligibility
      enforcement: code
---

<!-- ekp:header v1 -->
> **Business Rule** · departure-control › system:dcs › component:dcs.seat-assignment
> **Source:** `git:dcs-seat:seatalloc/infant_rules.c#check_exit_row_infant/eligibility-353743` @ `9c1e2f7a4b0d` · extraction: deterministic
> **Trust:** machine_confirmed · **Status:** stable · **Valid from:** 2026-09-14
> **Also about:** `capability:seat-eligibility`, `term:infant`, `term:exit-row`
> **Relations:** implements `brd-seat:requirements/BRD-SEAT/BR-SEAT-014`; governed by `hld-dcs-seat:decisions/HLD-DCS-SEAT-002/dec-seat-eligibility-rules-table`
<!-- /ekp:header -->

# Rule

If the requested seat has `SEAT_ATTR_EXIT_ROW` set and the passenger's
`infant_count` is greater than 0, seat assignment is rejected with
`SEAT_REJ_INF_EXIT` (41).[^code]

# Condition

```c
seat->attrs & SEAT_ATTR_EXIT_ROW && pax->infant_count > 0
```

# Where it runs

`check_exit_row_infant()` in `seatalloc/infant_rules.c`, part of
[the infant rules module](/modules/seatalloc/infant_rules.c.md).

[^code]: seatalloc/infant_rules.c lines 9-16 at 9c1e2f7
````

### Knowledge Catalog entry (kcmd's own converter, no GCP call)

`entryType`: `projects/dataplex-types/locations/global/entryTypes/document`  
`name`: `projects/acme-ekp/locations/us-central1/entryGroups/code-dcs-seat/entries/rules/seatalloc/infant_rules.c/check_exit_row_infant/eligibility-353743`

```json
{
  "acme-ekp.us-central1.ekp-core": {
    "concept_id": "code-dcs-seat:rules/seatalloc/infant_rules.c/check_exit_row_infant/eligibility-353743",
    "concept_type": "BusinessRule",
    "lifecycle": "stable",
    "domain": "departure-control",
    "primary_system": "system:dcs",
    "primary_component": "component:dcs.seat-assignment",
    "primary_capability": "capability:seat-eligibility",
    "source_kind": "code",
    "source_system": "git",
    "source_ref": "git:dcs-seat:seatalloc/infant_rules.c#check_exit_row_infant/eligibility-353743",
    "source_revision": "9c1e2f7a4b0d",
    "source_url": "https://git.example.com/dcs-seat/blob/9c1e2f7a4b0d/seatalloc/infant_rules.c#L9-L16",
    "extraction": "deterministic",
    "trust_tier": "machine_confirmed",
    "valid_from": "2026-09-14T08:00:00Z",
    "owner_team": "team:dcs-seating",
    "build_id": "code-dcs-seat-20261124T180000Z",
    "profile": "code-repo@2",
    "ontology_version": "1.1",
    "anchors": [
      "system:dcs",
      "component:dcs.seat-assignment",
      "capability:seat-eligibility",
      "term:infant",
      "term:exit-row"
    ],
    "relations": [
      {
        "rel": "implements",
        "target": "brd-seat:requirements/BRD-SEAT/BR-SEAT-014"
      },
      {
        "rel": "governed_by",
        "target": "hld-dcs-seat:decisions/HLD-DCS-SEAT-002/dec-seat-eligibility-rules-table"
      }
    ]
  },
  "acme-ekp.us-central1.ekp-rule": {
    "rule_kind": "eligibility",
    "enforcement": "code"
  },
  "dataplex-types.global.document": {
    "type": "business-rule"
  }
}
```

The body (`dataplex-types.global.overview`) carries the reader header, the markdown, and kcmd's trailing `## OKF Metadata` block.

### Gate verdict (steady state)

```
build code-dcs-seat-20261124T180000Z  profile code-repo@2  entry group code-dcs-seat  concepts 3
  golden recall@3: 1.00 over 2 question(s)
  => PASS: 0 error(s), 0 warning(s)
```

### searchEntries predicate that finds it

```
aspect:acme-ekp.us-central1.ekp-core.concept_type="BusinessRule"
aspect:acme-ekp.us-central1.ekp-core.primary_component="component:dcs.seat-assignment"
aspect:acme-ekp.us-central1.ekp-core.lifecycle="stable"
aspect:acme-ekp.us-central1.ekp-rule.rule_kind="eligibility"
```

## 1b. Any repo kind: rules-as-data in a Java service repo

Profile `code-repo` → entry group `code-seat-service` → concept `rules/src/main/resources/rules/seat-eligibility.yaml/INF_EXIT_ROW/eligibility-0945ef`

### Input

```
# SYNTHETIC SAMPLE. Seat eligibility rules as data (per HLD-DCS-SEAT-002).
rules:
  - id: INF_EXIT_ROW
    when: { seat.exit_row: true, pax.infant_count: { gt: 0 } }
    reject: INF_EXIT
    owner: team:dcs-seating
    effective_from: 2026-10-01
```

### OKF concept written by the build

````markdown
---
type: Business Rule
title: 'INF_EXIT_ROW: infant passenger may not take an exit-row seat (rules table)'
description: Rules-table row INF_EXIT_ROW rejects an exit-row seat with INF_EXIT when the passenger has
  a lap infant.
tags:
- seat-eligibility
- infant
- exit-row
status: stable
generated:
  by: ekp-rules-config-extractor/0.1
  at: '2026-10-01T00:00:00Z'
verified:
- by: process:ekp-parity-check
  at: '2026-11-24T18:05:00Z'
sources:
- id: row
  resource: https://git.example.com/seat-service/blob/4be09a1c77d2/src/main/resources/rules/seat-eligibility.yaml
extra:
  aspects:
    acme-ekp.us-central1.ekp-core:
      concept_id: code-seat-service:rules/src/main/resources/rules/seat-eligibility.yaml/INF_EXIT_ROW/eligibility-0945ef
      concept_type: BusinessRule
      lifecycle: stable
      domain: departure-control
      primary_system: system:dcs
      primary_component: component:dcs.seat-assignment
      primary_capability: capability:seat-eligibility
      source_kind: code
      source_system: git
      source_ref: git:seat-service:src/main/resources/rules/seat-eligibility.yaml#INF_EXIT_ROW/eligibility-0945ef
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
      - term:infant
      - term:exit-row
      relations:
      - rel: implements
        target: brd-seat:requirements/BRD-SEAT/BR-SEAT-014
      - rel: governed_by
        target: hld-dcs-seat:decisions/HLD-DCS-SEAT-002/dec-seat-eligibility-rules-table
      - rel: same_as
        target: code-dcs-seat:rules/seatalloc/infant_rules.c/check_exit_row_infant/eligibility-353743
    acme-ekp.us-central1.ekp-rule:
      rule_kind: eligibility
      enforcement: config
---

<!-- ekp:header v1 -->
> **Business Rule** · departure-control › system:dcs › component:dcs.seat-assignment
> **Source:** `git:seat-service:src/main/resources/rules/seat-eligibility.yaml#INF_EXIT_ROW/eligibility-0945ef` @ `4be09a1c77d2` · extraction: deterministic
> **Trust:** machine_confirmed · **Status:** stable · **Valid from:** 2026-10-01
> **Also about:** `capability:seat-eligibility`, `term:infant`, `term:exit-row`
> **Relations:** implements `brd-seat:requirements/BRD-SEAT/BR-SEAT-014`; governed by `hld-dcs-seat:decisions/HLD-DCS-SEAT-002/dec-seat-eligibility-rules-table`; same as `code-dcs-seat:rules/seatalloc/infant_rules.c/check_exit_row_infant/eligibility-353743`
<!-- /ekp:header -->

# Rule

Row `INF_EXIT_ROW` in `rules/seat-eligibility.yaml`, effective 2026-10-01:
reject with `INF_EXIT` when the seat is an exit row and the passenger's
`infant_count` is greater than 0.

```text
INF_EXIT_ROW: seat.exit_row == true and pax.infant_count > 0 -> reject INF_EXIT
```

This is the rules-table form of the legacy TPF check, per the HLD decision.
````

### Knowledge Catalog entry (kcmd's own converter, no GCP call)

`entryType`: `projects/dataplex-types/locations/global/entryTypes/document`  
`name`: `projects/acme-ekp/locations/us-central1/entryGroups/code-seat-service/entries/rules/src/main/resources/rules/seat-eligibility.yaml/INF_EXIT_ROW/eligibility-0945ef`

```json
{
  "acme-ekp.us-central1.ekp-core": {
    "concept_id": "code-seat-service:rules/src/main/resources/rules/seat-eligibility.yaml/INF_EXIT_ROW/eligibility-0945ef",
    "concept_type": "BusinessRule",
    "lifecycle": "stable",
    "domain": "departure-control",
    "primary_system": "system:dcs",
    "primary_component": "component:dcs.seat-assignment",
    "primary_capability": "capability:seat-eligibility",
    "source_kind": "code",
    "source_system": "git",
    "source_ref": "git:seat-service:src/main/resources/rules/seat-eligibility.yaml#INF_EXIT_ROW/eligibility-0945ef",
    "source_revision": "4be09a1c77d2",
    "extraction": "deterministic",
    "trust_tier": "machine_confirmed",
    "valid_from": "2026-10-01T00:00:00Z",
    "owner_team": "team:dcs-seating",
    "build_id": "code-seat-service-20261124T180000Z",
    "profile": "code-repo@2",
    "ontology_version": "1.1",
    "anchors": [
      "system:dcs",
      "component:dcs.seat-assignment",
      "capability:seat-eligibility",
      "term:infant",
      "term:exit-row"
    ],
    "relations": [
      {
        "rel": "implements",
        "target": "brd-seat:requirements/BRD-SEAT/BR-SEAT-014"
      },
      {
        "rel": "governed_by",
        "target": "hld-dcs-seat:decisions/HLD-DCS-SEAT-002/dec-seat-eligibility-rules-table"
      },
      {
        "rel": "same_as",
        "target": "code-dcs-seat:rules/seatalloc/infant_rules.c/check_exit_row_infant/eligibility-353743"
      }
    ]
  },
  "acme-ekp.us-central1.ekp-rule": {
    "rule_kind": "eligibility",
    "enforcement": "config"
  },
  "dataplex-types.global.document": {
    "type": "business-rule"
  }
}
```

The body (`dataplex-types.global.overview`) carries the reader header, the markdown, and kcmd's trailing `## OKF Metadata` block.

### Gate verdict (steady state)

```
build code-seat-service-20261124T180000Z  profile code-repo@2  entry group code-seat-service  concepts 5
  golden recall@3: 1.00 over 2 question(s)
  => PASS: 0 error(s), 0 warning(s)
```

### searchEntries predicate that finds it

```
aspect:acme-ekp.us-central1.ekp-core.concept_type="BusinessRule"
aspect:acme-ekp.us-central1.ekp-core.primary_component="component:dcs.seat-assignment"
aspect:acme-ekp.us-central1.ekp-rule.enforcement="config"
```

## 1c. Any repo kind: Terraform in the same repo

Profile `code-repo` → entry group `code-seat-service` → concept `infra/terraform/pubsub.tf/google_pubsub_topic.seat_assigned`

### Input

```
# SYNTHETIC SAMPLE
resource "google_pubsub_topic" "seat_assigned" {
  name   = "seat-assigned"
  labels = { system = "dcs", component = "seat-assignment" }
  message_retention_duration = "86400s"
}
```

### OKF concept written by the build

````markdown
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
````

### Knowledge Catalog entry (kcmd's own converter, no GCP call)

`entryType`: `projects/dataplex-types/locations/global/entryTypes/document`  
`name`: `projects/acme-ekp/locations/us-central1/entryGroups/code-seat-service/entries/infra/terraform/pubsub.tf/google_pubsub_topic.seat_assigned`

```json
{
  "acme-ekp.us-central1.ekp-core": {
    "concept_id": "code-seat-service:infra/terraform/pubsub.tf/google_pubsub_topic.seat_assigned",
    "concept_type": "InfraResource",
    "lifecycle": "stable",
    "domain": "departure-control",
    "primary_system": "system:dcs",
    "primary_component": "component:dcs.seat-assignment",
    "source_kind": "code",
    "source_system": "git",
    "source_ref": "git:seat-service:terraform/pubsub.tf#google_pubsub_topic.seat_assigned",
    "source_revision": "4be09a1c77d2",
    "extraction": "deterministic",
    "trust_tier": "unverified",
    "valid_from": "2026-10-01T00:00:00Z",
    "owner_team": "team:dcs-seating",
    "build_id": "code-seat-service-20261124T180000Z",
    "profile": "code-repo@2",
    "ontology_version": "1.1",
    "anchors": [
      "system:dcs",
      "component:dcs.seat-assignment"
    ]
  },
  "acme-ekp.us-central1.ekp-infra": {
    "tool": "terraform",
    "provider": "gcp",
    "resource_kind": "google_pubsub_topic"
  },
  "dataplex-types.global.document": {
    "type": "infra-resource"
  }
}
```

The body (`dataplex-types.global.overview`) carries the reader header, the markdown, and kcmd's trailing `## OKF Metadata` block.

### Gate verdict (steady state)

```
build code-seat-service-20261124T180000Z  profile code-repo@2  entry group code-seat-service  concepts 5
  golden recall@3: 1.00 over 2 question(s)
  => PASS: 0 error(s), 0 warning(s)
```

### searchEntries predicate that finds it

```
aspect:acme-ekp.us-central1.ekp-core.concept_type="InfraResource"
aspect:acme-ekp.us-central1.ekp-core.primary_component="component:dcs.seat-assignment"
aspect:acme-ekp.us-central1.ekp-infra.resource_kind="google_pubsub_topic"
```

## 2. HLD (AsciiDoc template)

Profile `arch-doc` → entry group `hld-dcs-seat` → concept `decisions/HLD-DCS-SEAT-002/dec-seat-eligibility-rules-table`

### Input

```
= HLD: Seat Assignment Modernisation
:doc-id: HLD-DCS-SEAT-002
:system: system:dcs
:component: component:dcs.seat-assignment
// SYNTHETIC SAMPLE written from the HLD AsciiDoc template.

[[ctx-overview]]
== Context
Seat eligibility checks are hard-coded in seatalloc C functions and are hard
to change without a release.

[[dec-seat-eligibility-rules-table]]
=== Decision: seat eligibility rules move to a rules table
Status:: Accepted (2026-08-20)
Context:: Eligibility checks such as infant-in-exit-row are coded per function.
Decision:: Express seat eligibility rules as rows in the modernised seat
service's rules table. Legacy C checks stay authoritative until cut-over.
Consequences:: Rules become data with owners and effective dates; every legacy
rule needs a one-to-one migration and parity test.

[[des-seat-eligibility-service]]
=== Design: seat eligibility evaluation
The seat service loads active rules for the flight, evaluates them per
passenger-seat pair and returns the first reject reason. Infant, exit-row and
cabin rules are evaluated before price rules.
```

### OKF concept written by the build

````markdown
---
type: Decision
title: Seat eligibility rules move to a rules table
description: Seat eligibility checks become rows in the modernised seat service's rules table; legacy
  C checks stay authoritative until cut-over.
tags:
- seat-eligibility
- modernisation
status: stable
generated:
  by: ekp-hld-adapter/0.2
  at: '2026-08-20T00:00:00Z'
verified:
- by: human:arch-review-board
  at: '2026-08-21T10:00:00Z'
sources:
- id: hld
  resource: https://git.example.com/arch-docs/blob/a77d01c/HLD-DCS-SEAT-002.adoc
  title: HLD-DCS-SEAT-002 Seat Assignment Modernisation
  author: team:dcs-architecture
extra:
  aspects:
    acme-ekp.us-central1.ekp-core:
      concept_id: hld-dcs-seat:decisions/HLD-DCS-SEAT-002/dec-seat-eligibility-rules-table
      concept_type: Decision
      lifecycle: stable
      domain: departure-control
      primary_system: system:dcs
      primary_component: component:dcs.seat-assignment
      primary_capability: capability:seat-eligibility
      source_kind: arch_doc
      source_system: git
      source_ref: hld:HLD-DCS-SEAT-002#dec-seat-eligibility-rules-table
      source_revision: a77d01c3e9f2
      source_url: https://git.example.com/arch-docs/blob/a77d01c/HLD-DCS-SEAT-002.adoc
      extraction: template
      trust_tier: human_reviewed
      valid_from: '2026-08-20T00:00:00Z'
      owner_team: team:dcs-architecture
      build_id: hld-dcs-seat-20261124T180000Z
      profile: arch-doc@1
      ontology_version: '1.1'
      anchors:
      - system:dcs
      - component:dcs.seat-assignment
      - capability:seat-eligibility
    acme-ekp.us-central1.ekp-decision:
      decision_status: accepted
      decided_on: '2026-08-20T00:00:00Z'
---

<!-- ekp:header v1 -->
> **Decision** · departure-control › system:dcs › component:dcs.seat-assignment
> **Source:** `hld:HLD-DCS-SEAT-002#dec-seat-eligibility-rules-table` @ `a77d01c3e9f2` · extraction: template
> **Trust:** human_reviewed · **Status:** stable · **Valid from:** 2026-08-20
> **Also about:** `capability:seat-eligibility`
<!-- /ekp:header -->

# Decision

Express seat eligibility rules as rows in the modernised seat service's rules
table. Legacy C checks stay authoritative until cut-over.[^hld]

# Context

Eligibility checks such as infant-in-exit-row are hard-coded per C function,
so every change needs a release.

# Consequences

Rules become data with owners and effective dates. Every legacy rule needs a
one-to-one migration and a parity test.

[^hld]: HLD-DCS-SEAT-002, section dec-seat-eligibility-rules-table
````

### Knowledge Catalog entry (kcmd's own converter, no GCP call)

`entryType`: `projects/dataplex-types/locations/global/entryTypes/document`  
`name`: `projects/acme-ekp/locations/us-central1/entryGroups/hld-dcs-seat/entries/decisions/HLD-DCS-SEAT-002/dec-seat-eligibility-rules-table`

```json
{
  "acme-ekp.us-central1.ekp-core": {
    "concept_id": "hld-dcs-seat:decisions/HLD-DCS-SEAT-002/dec-seat-eligibility-rules-table",
    "concept_type": "Decision",
    "lifecycle": "stable",
    "domain": "departure-control",
    "primary_system": "system:dcs",
    "primary_component": "component:dcs.seat-assignment",
    "primary_capability": "capability:seat-eligibility",
    "source_kind": "arch_doc",
    "source_system": "git",
    "source_ref": "hld:HLD-DCS-SEAT-002#dec-seat-eligibility-rules-table",
    "source_revision": "a77d01c3e9f2",
    "source_url": "https://git.example.com/arch-docs/blob/a77d01c/HLD-DCS-SEAT-002.adoc",
    "extraction": "template",
    "trust_tier": "human_reviewed",
    "valid_from": "2026-08-20T00:00:00Z",
    "owner_team": "team:dcs-architecture",
    "build_id": "hld-dcs-seat-20261124T180000Z",
    "profile": "arch-doc@1",
    "ontology_version": "1.1",
    "anchors": [
      "system:dcs",
      "component:dcs.seat-assignment",
      "capability:seat-eligibility"
    ]
  },
  "acme-ekp.us-central1.ekp-decision": {
    "decision_status": "accepted",
    "decided_on": "2026-08-20T00:00:00Z"
  },
  "dataplex-types.global.document": {
    "type": "decision"
  }
}
```

The body (`dataplex-types.global.overview`) carries the reader header, the markdown, and kcmd's trailing `## OKF Metadata` block.

### Gate verdict (steady state)

```
build hld-dcs-seat-20261124T180000Z  profile arch-doc@1  entry group hld-dcs-seat  concepts 2
  golden recall@3: 1.00 over 1 question(s)
  => PASS: 0 error(s), 0 warning(s)
```

### searchEntries predicate that finds it

```
aspect:acme-ekp.us-central1.ekp-core.concept_type="Decision"
aspect:acme-ekp.us-central1.ekp-core.primary_capability="capability:seat-eligibility"
aspect:acme-ekp.us-central1.ekp-core.trust_tier="human_reviewed"
aspect:acme-ekp.us-central1.ekp-decision.decision_status="accepted"
```

## 3. BRD

Profile `brd` → entry group `brd-seat` → concept `requirements/BRD-SEAT/BR-SEAT-014`

### Input

```
# BRD-SEAT: Seat Assignment (SYNTHETIC SAMPLE)

## 4. Functional requirements

| ID          | Requirement                                                                                          | Priority | Status      |
|-------------|------------------------------------------------------------------------------------------------------|----------|-------------|
| BR-SEAT-014 | The system shall not assign a seat in an exit row to a passenger travelling with an infant.          | Must     | Implemented |
```

### OKF concept written by the build

````markdown
---
type: Requirement
title: 'BR-SEAT-014: no exit-row seat for a passenger travelling with an infant'
description: The system shall not assign a seat in an exit row to a passenger travelling with an infant.
tags:
- seat-eligibility
- infant
- exit-row
status: stable
generated:
  by: ekp-brd-adapter/0.3
  at: '2026-03-02T00:00:00Z'
verified:
- by: human:ba-signoff
  at: '2026-03-05T09:00:00Z'
sources:
- id: brd
  resource: https://wiki.example.com/display/BRD/BRD-SEAT
  title: BRD-SEAT Seat Assignment
  author: team:dcs-product
extra:
  aspects:
    acme-ekp.us-central1.ekp-core:
      concept_id: brd-seat:requirements/BRD-SEAT/BR-SEAT-014
      concept_type: Requirement
      lifecycle: stable
      domain: departure-control
      primary_system: system:dcs
      primary_component: component:dcs.seat-assignment
      primary_capability: capability:seat-eligibility
      source_kind: brd
      source_system: confluence
      source_ref: brd:BRD-SEAT#BR-SEAT-014
      source_revision: v12
      source_url: https://wiki.example.com/display/BRD/BRD-SEAT
      extraction: template
      trust_tier: human_reviewed
      valid_from: '2026-03-02T00:00:00Z'
      owner_team: team:dcs-product
      build_id: brd-seat-20261124T180000Z
      profile: brd@1
      ontology_version: '1.1'
      anchors:
      - system:dcs
      - component:dcs.seat-assignment
      - capability:seat-eligibility
      - term:infant
      - term:exit-row
      relations:
      - rel: specifies
        target: brd-seat:rules/BRD-SEAT/BR-SEAT-014/eligibility-3ade07
    acme-ekp.us-central1.ekp-requirement:
      req_id: BR-SEAT-014
      req_kind: functional
      priority: must
      req_status: implemented
---

<!-- ekp:header v1 -->
> **Requirement** · departure-control › system:dcs › component:dcs.seat-assignment
> **Source:** `brd:BRD-SEAT#BR-SEAT-014` @ `v12` · extraction: template
> **Trust:** human_reviewed · **Status:** stable · **Valid from:** 2026-03-02
> **Also about:** `capability:seat-eligibility`, `term:infant`, `term:exit-row`
> **Relations:** specifies `brd-seat:rules/BRD-SEAT/BR-SEAT-014/eligibility-3ade07`
<!-- /ekp:header -->

# Requirement

The system shall not assign a seat in an exit row to a passenger travelling
with an infant.[^brd]

| Priority | Status |
|---|---|
| Must | Implemented |

[^brd]: BRD-SEAT section 4, row BR-SEAT-014
````

### Knowledge Catalog entry (kcmd's own converter, no GCP call)

`entryType`: `projects/dataplex-types/locations/global/entryTypes/document`  
`name`: `projects/acme-ekp/locations/us-central1/entryGroups/brd-seat/entries/requirements/BRD-SEAT/BR-SEAT-014`

```json
{
  "acme-ekp.us-central1.ekp-core": {
    "concept_id": "brd-seat:requirements/BRD-SEAT/BR-SEAT-014",
    "concept_type": "Requirement",
    "lifecycle": "stable",
    "domain": "departure-control",
    "primary_system": "system:dcs",
    "primary_component": "component:dcs.seat-assignment",
    "primary_capability": "capability:seat-eligibility",
    "source_kind": "brd",
    "source_system": "confluence",
    "source_ref": "brd:BRD-SEAT#BR-SEAT-014",
    "source_revision": "v12",
    "source_url": "https://wiki.example.com/display/BRD/BRD-SEAT",
    "extraction": "template",
    "trust_tier": "human_reviewed",
    "valid_from": "2026-03-02T00:00:00Z",
    "owner_team": "team:dcs-product",
    "build_id": "brd-seat-20261124T180000Z",
    "profile": "brd@1",
    "ontology_version": "1.1",
    "anchors": [
      "system:dcs",
      "component:dcs.seat-assignment",
      "capability:seat-eligibility",
      "term:infant",
      "term:exit-row"
    ],
    "relations": [
      {
        "rel": "specifies",
        "target": "brd-seat:rules/BRD-SEAT/BR-SEAT-014/eligibility-3ade07"
      }
    ]
  },
  "acme-ekp.us-central1.ekp-requirement": {
    "req_id": "BR-SEAT-014",
    "req_kind": "functional",
    "priority": "must",
    "req_status": "implemented"
  },
  "dataplex-types.global.document": {
    "type": "requirement"
  }
}
```

The body (`dataplex-types.global.overview`) carries the reader header, the markdown, and kcmd's trailing `## OKF Metadata` block.

### Gate verdict (steady state)

```
build brd-seat-20261124T180000Z  profile brd@1  entry group brd-seat  concepts 2
  golden recall@3: 1.00 over 1 question(s)
  => PASS: 0 error(s), 0 warning(s)
```

### searchEntries predicate that finds it

```
aspect:acme-ekp.us-central1.ekp-core.concept_type="Requirement"
aspect:acme-ekp.us-central1.ekp-core.domain="departure-control"
aspect:acme-ekp.us-central1.ekp-requirement.req_id="BR-SEAT-014"
```

## 4. Wiki (Confluence runbook)

Profile `wiki` → entry group `wiki-dcsops` → concept `procedures/DCSOPS/48213907`

### Input

```
Space: DCSOPS   Page ID: 48213907   Version: 7   Labels: runbook, seating
Title: Gate: passenger with infant holds an exit-row seat
(SYNTHETIC SAMPLE)

When the seat map shows a reject "INF EXIT" or a passenger with an infant is
found in an exit row at the gate:
1. Open the passenger in the seat map and pick a non-exit seat in the same cabin.
2. If none is free, offer a seat in another cabin per the downgrade/upgrade policy.
3. Re-issue the boarding pass. Do not override the exit-row block.
```

### OKF concept written by the build

````markdown
---
type: Procedure
title: 'Gate: passenger with infant holds an exit-row seat'
description: Gate agent steps to reseat a passenger travelling with an infant out of an exit row.
tags:
- runbook
- infant
- exit-row
status: stable
generated:
  by: ekp-confluence-adapter/0.2
  at: '2026-10-05T00:00:00Z'
verified:
- by: human:ops-lead
  at: '2026-10-06T08:00:00Z'
sources:
- id: page
  resource: https://wiki.example.com/pages/viewpage.action?pageId=48213907
  title: 'DCSOPS / Gate: passenger with infant holds an exit-row seat'
  author: team:airport-ops
  usage_count: 312
  last_modified: '2026-10-05T00:00:00Z'
extra:
  aspects:
    acme-ekp.us-central1.ekp-core:
      concept_id: wiki-dcsops:procedures/DCSOPS/48213907
      concept_type: Procedure
      lifecycle: stable
      domain: departure-control
      primary_system: system:dcs
      primary_component: component:dcs.seat-assignment
      source_kind: wiki
      source_system: confluence
      source_ref: confluence:DCSOPS:48213907
      source_revision: '7'
      source_url: https://wiki.example.com/pages/viewpage.action?pageId=48213907
      extraction: deterministic
      trust_tier: human_reviewed
      valid_from: '2026-10-05T00:00:00Z'
      owner_team: team:airport-ops
      build_id: wiki-dcsops-20261124T180000Z
      profile: wiki@1
      ontology_version: '1.1'
      anchors:
      - system:dcs
      - component:dcs.seat-assignment
      - term:infant
      - term:exit-row
      relations:
      - rel: describes
        target: code-dcs-seat:rules/seatalloc/infant_rules.c/check_exit_row_infant/eligibility-353743
---

<!-- ekp:header v1 -->
> **Procedure** · departure-control › system:dcs › component:dcs.seat-assignment
> **Source:** `confluence:DCSOPS:48213907` @ `7` · extraction: deterministic
> **Trust:** human_reviewed · **Status:** stable · **Valid from:** 2026-10-05
> **Also about:** `term:infant`, `term:exit-row`
> **Relations:** describes `code-dcs-seat:rules/seatalloc/infant_rules.c/check_exit_row_infant/eligibility-353743`
<!-- /ekp:header -->

# When to use

The seat map shows reject `INF EXIT`, or a passenger with an infant is found in
an exit row at the gate.

# Steps

1. Open the passenger in the seat map and pick a non-exit seat in the same cabin.
2. If none is free, offer a seat in another cabin per the downgrade/upgrade policy.
3. Re-issue the boarding pass. Do not override the exit-row block.
````

### Knowledge Catalog entry (kcmd's own converter, no GCP call)

`entryType`: `projects/dataplex-types/locations/global/entryTypes/document`  
`name`: `projects/acme-ekp/locations/us-central1/entryGroups/wiki-dcsops/entries/procedures/DCSOPS/48213907`

```json
{
  "acme-ekp.us-central1.ekp-core": {
    "concept_id": "wiki-dcsops:procedures/DCSOPS/48213907",
    "concept_type": "Procedure",
    "lifecycle": "stable",
    "domain": "departure-control",
    "primary_system": "system:dcs",
    "primary_component": "component:dcs.seat-assignment",
    "source_kind": "wiki",
    "source_system": "confluence",
    "source_ref": "confluence:DCSOPS:48213907",
    "source_revision": "7",
    "source_url": "https://wiki.example.com/pages/viewpage.action?pageId=48213907",
    "extraction": "deterministic",
    "trust_tier": "human_reviewed",
    "valid_from": "2026-10-05T00:00:00Z",
    "owner_team": "team:airport-ops",
    "build_id": "wiki-dcsops-20261124T180000Z",
    "profile": "wiki@1",
    "ontology_version": "1.1",
    "anchors": [
      "system:dcs",
      "component:dcs.seat-assignment",
      "term:infant",
      "term:exit-row"
    ],
    "relations": [
      {
        "rel": "describes",
        "target": "code-dcs-seat:rules/seatalloc/infant_rules.c/check_exit_row_infant/eligibility-353743"
      }
    ]
  },
  "dataplex-types.global.document": {
    "type": "procedure"
  }
}
```

The body (`dataplex-types.global.overview`) carries the reader header, the markdown, and kcmd's trailing `## OKF Metadata` block.

### Gate verdict (steady state)

```
build wiki-dcsops-20261124T180000Z  profile wiki@1  entry group wiki-dcsops  concepts 1
  golden recall@3: 1.00 over 1 question(s)
  => PASS: 0 error(s), 0 warning(s)
```

### searchEntries predicate that finds it

```
aspect:acme-ekp.us-central1.ekp-core.concept_type="Procedure"
aspect:acme-ekp.us-central1.ekp-core.primary_component="component:dcs.seat-assignment"
```

## 5. Jira (epic)

Profile `jira` → entry group `jira-seat` → concept `changes/SEAT-412`

### Input

```
{
  "_note": "SYNTHETIC SAMPLE",
  "key": "SEAT-412",
  "issuetype": "Epic",
  "project": "SEAT",
  "summary": "Re-check exit-row eligibility when an infant is added after seat assignment",
  "status": "Done",
  "fixVersions": ["2026.10"],
  "components": ["Seating"],
  "labels": ["seat-eligibility"],
  "updated": "2026-10-02T11:20:00Z",
  "children": [
    {"key": "SEAT-415", "issuetype": "Story", "summary": "Run exit-row infant check when an infant is added to a seated passenger"},
    {"key": "SEAT-419", "issuetype": "Bug",   "summary": "Exit-row infant check skipped on kiosk seat change"}
  ]
}
```

### OKF concept written by the build

````markdown
---
type: Change
title: 'SEAT-412: Re-check exit-row eligibility when an infant is added after seat assignment'
description: Exit-row infant check now re-runs when an infant is added to a seated passenger and on kiosk
  seat changes (release 2026.10).
tags:
- seat-eligibility
status: stable
generated:
  by: ekp-jira-adapter/0.3
  at: '2026-10-02T11:20:00Z'
sources:
- id: seat-412
  resource: https://jira.example.com/browse/SEAT-412
  title: SEAT-412
- id: seat-415
  resource: https://jira.example.com/browse/SEAT-415
  title: SEAT-415 Run exit-row infant check when an infant is added to a seated passenger
- id: seat-419
  resource: https://jira.example.com/browse/SEAT-419
  title: SEAT-419 Exit-row infant check skipped on kiosk seat change
extra:
  aspects:
    acme-ekp.us-central1.ekp-core:
      concept_id: jira-seat:changes/SEAT-412
      concept_type: Change
      lifecycle: stable
      domain: departure-control
      primary_system: system:dcs
      primary_component: component:dcs.seat-assignment
      primary_capability: capability:seat-eligibility
      source_kind: jira
      source_system: jira
      source_ref: jira:SEAT-412
      source_revision: '2026-10-02T11:20:00Z'
      source_url: https://jira.example.com/browse/SEAT-412
      extraction: deterministic
      trust_tier: unverified
      valid_from: '2026-10-02T11:20:00Z'
      owner_team: team:dcs-seating
      build_id: jira-seat-20261124T180000Z
      profile: jira@1
      ontology_version: '1.1'
      anchors:
      - system:dcs
      - component:dcs.seat-assignment
      - capability:seat-eligibility
      relations:
      - rel: changes
        target: code-dcs-seat:rules/seatalloc/infant_rules.c/check_exit_row_infant/eligibility-353743
    acme-ekp.us-central1.ekp-change:
      change_status: done
      release: '2026.10'
---

<!-- ekp:header v1 -->
> **Change** · departure-control › system:dcs › component:dcs.seat-assignment
> **Source:** `jira:SEAT-412` @ `2026-10-02T11:20:00Z` · extraction: deterministic
> **Trust:** unverified · **Status:** stable · **Valid from:** 2026-10-02
> **Also about:** `capability:seat-eligibility`
> **Relations:** changes `code-dcs-seat:rules/seatalloc/infant_rules.c/check_exit_row_infant/eligibility-353743`
<!-- /ekp:header -->

# Change

Exit-row infant check now re-runs when an infant is added to a seated passenger and on kiosk seat changes (release 2026.10).

# Work items

* SEAT-415 (Story): Run exit-row infant check when an infant is added to a seated passenger
* SEAT-419 (Bug): Exit-row infant check skipped on kiosk seat change
````

### Knowledge Catalog entry (kcmd's own converter, no GCP call)

`entryType`: `projects/dataplex-types/locations/global/entryTypes/document`  
`name`: `projects/acme-ekp/locations/us-central1/entryGroups/jira-seat/entries/changes/SEAT-412`

```json
{
  "acme-ekp.us-central1.ekp-core": {
    "concept_id": "jira-seat:changes/SEAT-412",
    "concept_type": "Change",
    "lifecycle": "stable",
    "domain": "departure-control",
    "primary_system": "system:dcs",
    "primary_component": "component:dcs.seat-assignment",
    "primary_capability": "capability:seat-eligibility",
    "source_kind": "jira",
    "source_system": "jira",
    "source_ref": "jira:SEAT-412",
    "source_revision": "2026-10-02T11:20:00Z",
    "source_url": "https://jira.example.com/browse/SEAT-412",
    "extraction": "deterministic",
    "trust_tier": "unverified",
    "valid_from": "2026-10-02T11:20:00Z",
    "owner_team": "team:dcs-seating",
    "build_id": "jira-seat-20261124T180000Z",
    "profile": "jira@1",
    "ontology_version": "1.1",
    "anchors": [
      "system:dcs",
      "component:dcs.seat-assignment",
      "capability:seat-eligibility"
    ],
    "relations": [
      {
        "rel": "changes",
        "target": "code-dcs-seat:rules/seatalloc/infant_rules.c/check_exit_row_infant/eligibility-353743"
      }
    ]
  },
  "acme-ekp.us-central1.ekp-change": {
    "change_status": "done",
    "release": "2026.10"
  },
  "dataplex-types.global.document": {
    "type": "change"
  }
}
```

The body (`dataplex-types.global.overview`) carries the reader header, the markdown, and kcmd's trailing `## OKF Metadata` block.

### Gate verdict (steady state)

```
build jira-seat-20261124T180000Z  profile jira@1  entry group jira-seat  concepts 2
  golden recall@3: 1.00 over 1 question(s)
  => PASS: 0 error(s), 0 warning(s)
```

### searchEntries predicate that finds it

```
aspect:acme-ekp.us-central1.ekp-core.concept_type="Change"
aspect:acme-ekp.us-central1.ekp-core.primary_capability="capability:seat-eligibility"
aspect:acme-ekp.us-central1.ekp-change.release="2026.10"
```

## 6. What the gate blocks: the next Jira run

`samples/builds/jira-seat-next-broken` is the same entry group one run later, with five planted defects: an alias used as an anchor, a vanished concept, a title-derived ID, an unverified LLM decision published as stable, and a hand-edited trust tier.

```
build jira-seat-20261125T060000Z  profile jira@1  entry group jira-seat  concepts 3
  changes/SEAT-401.md
    ERROR LIF001  concept vanished since build jira-seat-20261124T180000Z: kcmd push would DELETE its entry. Keep the file with status: deprecated, valid_to, and superseded_by if it moved or was replaced.
  changes/SEAT-412.md
    ERROR DER003  trust_tier 'human_reviewed' but current `verified` events (at >= generated.at, OKF v0.3 §5.3) give 'unverified'
    ERROR ANC001  anchor 'Seating' is an alias; use canonical 'component:dcs.seat-assignment'
    ERROR ANC003  primary_component 'Seating' must be a component: anchor
    ERROR HDR001  reader header out of sync with frontmatter (run header --fix)
    WARN  LIF004  content changed but source_revision did not: non-deterministic emitter?
  changes/kiosk-exit-row-recheck.md
    ERROR ID001  entry ID 'changes/kiosk-exit-row-recheck' does not match ^changes/(?P<key>[A-Z][A-Z0-9]+-\d+)$ (IDs derive from source identity, never from titles)
  decisions/SEAT-412/c88123.md
    ERROR TRU003  unverified llm-extracted concept must be status: draft until verified
  golden recall@3: 1.00 over 1 question(s)
  => FAIL: 7 error(s), 1 warning(s)
(exit 1 - non-zero blocks kcmd push)

== pass 4: next HLD run, decision text changed since its human review ==
build hld-dcs-seat-20261125T060000Z  profile arch-doc@1  entry group hld-dcs-seat  concepts 2
  decisions/HLD-DCS-SEAT-002/dec-seat-eligibility-rules-table.md
    WARN  TRU007  was human_reviewed; content changed since the review, so the review is no longer current (OKF v0.3 §5.3). Route to the owner for re-review.
  golden recall@3: 1.00 over 1 question(s)
  => PASS: 0 error(s), 1 warning(s)
(exit 0 - warnings do not block; the owner gets a re-review task)

== pass 5: next wiki run, two unlabelled pages through the LLM lane ==
[
  {
    "entry_id": "procedures/DCSOPS/48219911",
    "type": "Procedure",
    "model_type": "Procedure",
    "confidence": 0.86,
    "registry_candidates": [
      "self-service kiosk"
    ]
  },
  {
    "entry_id": "unclassified/DCSOPS/48220450",
    "type": "Unclassified",
    "model_type": "Procedure",
    "confidence": 0.41,
    "registry_candidates": [
      "kiosk vendor"
    ]
  }
]
build wiki-dcsops-20261125T010000Z  profile wiki@1  entry group wiki-dcsops  concepts 3
  golden recall@3: 1.00 over 1 question(s)
  => PASS: 0 error(s), 0 warning(s)
(exit 0)
```

## 7. OKF v0.3 trust: an edit voids an old review

The HLD decision's text changed after the architecture board reviewed it. The emitter sets `generated.at` to the change time and keeps the old `verified` event as history. Under OKF v0.3 §5.3 only events at or after `generated.at` count, so trust drops from human_reviewed to unverified. The unchanged Design concept keeps its original `generated.at` through carry-forward, so its standing is untouched.

```yaml
---
type: Decision
title: Seat eligibility rules move to a rules table
description: Seat eligibility checks become rows in the modernised seat service's rules table; legacy
  C checks are retired on 2027-03-31.
tags:
- seat-eligibility
- modernisation
status: stable
generated:
  by: ekp-hld-adapter/0.2
  at: '2026-11-25T05:40:00Z'
verified:
- by: human:arch-review-board
  at: '2026-08-21T10:00:00Z'
sources:
- id: hld
  resource: https://git.example.com/arch-docs/blob/b81f2e0/HLD-DCS-SEAT-002.adoc
  title: HLD-DCS-SEAT-002 Seat Assignment Modernisation
  author: team:dcs-architecture
```

```
build hld-dcs-seat-20261125T060000Z  profile arch-doc@1  entry group hld-dcs-seat  concepts 2
  decisions/HLD-DCS-SEAT-002/dec-seat-eligibility-rules-table.md
    WARN  TRU007  was human_reviewed; content changed since the review, so the review is no longer current (OKF v0.3 §5.3). Route to the owner for re-review.
  golden recall@3: 1.00 over 1 question(s)
  => PASS: 0 error(s), 1 warning(s)
(exit 0 - warnings do not block; the owner gets a re-review task)

== pass 5: next wiki run, two unlabelled pages through the LLM lane ==
[
  {
    "entry_id": "procedures/DCSOPS/48219911",
    "type": "Procedure",
    "model_type": "Procedure",
    "confidence": 0.86,
    "registry_candidates": [
      "self-service kiosk"
    ]
  },
  {
    "entry_id": "unclassified/DCSOPS/48220450",
    "type": "Unclassified",
    "model_type": "Procedure",
    "confidence": 0.41,
    "registry_candidates": [
      "kiosk vendor"
    ]
  }
]
build wiki-dcsops-20261125T010000Z  profile wiki@1  entry group wiki-dcsops  concepts 3
  golden recall@3: 1.00 over 1 question(s)
  => PASS: 0 error(s), 0 warning(s)
(exit 0)
```

## 8. LLM lane: unlabelled wiki pages

Two wiki pages have no label, so no deterministic rule classifies them. `pipeline/llm_lane.py` sends each to a model with the prompt in `.agents/skills/ekp-okf/references/classify.md` (the same text an Antigravity session follows) and the JSON schema from `ekp_okf.spec.model_schema()`. Code owns identity (entry ID, source_ref, owner, dates); the model owns meaning (type, text, anchors, confidence). The model outputs here are canned fixtures (`samples/llm_lane_fixtures.json`), not a live model call.

* Page 48219911: confidence 0.86, at or above the wiki minimum of 0.8, so it becomes a `Procedure`. As LLM output with no review, it is `draft`.
* Page 48220450: confidence 0.41, so policy overrides the model's `Procedure` and quarantines it as `Unclassified` (draft).
* Both report `unresolved_terms` (kiosk) as registry candidates instead of guessing an anchor.

````markdown
---
type: Procedure
title: 'Counter: passenger with infant gets INF EXIT at the kiosk'
description: Counter steps when a passenger travelling with a lap infant is refused an exit-row seat (INF
  EXIT) at the self-service kiosk.
tags:
- infant
- exit-row
- kiosk
status: draft
generated:
  by: ekp-llm-lane/0.1+fixture
  at: '2026-11-24T18:35:12Z'
sources:
- id: page
  resource: https://wiki.example.com/pages/viewpage.action?pageId=48219911
  title: DCSOPS page 48219911
  last_modified: '2026-11-12T09:30:00Z'
...
````

```
[
  {
    "entry_id": "procedures/DCSOPS/48219911",
    "type": "Procedure",
    "model_type": "Procedure",
    "confidence": 0.86,
    "registry_candidates": [
      "self-service kiosk"
    ]
  },
  {
    "entry_id": "unclassified/DCSOPS/48220450",
    "type": "Unclassified",
    "model_type": "Procedure",
    "confidence": 0.41,
    "registry_candidates": [
      "kiosk vendor"
    ]
  }
]
build wiki-dcsops-20261125T010000Z  profile wiki@1  entry group wiki-dcsops  concepts 3
  golden recall@3: 1.00 over 1 question(s)
  => PASS: 0 error(s), 0 warning(s)
(exit 0)
```
