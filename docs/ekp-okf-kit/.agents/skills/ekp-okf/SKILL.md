---
name: ekp-okf
description: Generate, update, repair or validate EKP knowledge bundles - OKF v0.3 concepts that follow the EKP contract (ontology types, canonical anchors, ekp-core aspects, IDs derived from source identity) - from any source - code repos of any kind, HLDs, BRDs, wiki pages, Jira. Use when asked to produce or fix OKF or knowledge for EKP, to classify a document into EKP concepts, or when an EKP build gate fails. For OKF bundles outside EKP, use okf-generate instead.
---

# EKP OKF

You produce knowledge for EKP. The contract lives in this repo, not in this file:

| What | Where |
|---|---|
| Concept types, facets, typed relations | `ontology/types.yaml` |
| ekp-core fields and vocabularies | `ontology/core.yaml`, `ontology/vocab.yaml` |
| Canonical anchors and their aliases | `anchors/registry.yaml` |
| What each source kind may emit, ID rules | `profiles/<profile>.yaml` |
| Spec format you write | `ekp_okf/spec.py` (docstring) |

**You never write frontmatter by hand.** You write concept specs. `ekp_okf.emit_cli`
turns specs into files (aspects, derived fields, reader header, trust tier).
`ekp_okf.validate` (the build gate) decides whether the result is acceptable.
The ingestion pipeline uses the same emitter and the same gate, so what you
produce here has exactly the shape the pipeline produces.

## Rules

1. **Write only what a source supports.** Never invent owners, IDs, numbers, dates, URLs or anchors. If a fact has no source, leave it out and report it.
2. **Types come from the ontology and the profile.** If you are not sure which type fits, use `Unclassified` with `status: draft`. Never invent a type.
3. **Entry IDs derive from source identity**: repo path + symbol (+ condition hash), HLD section ID, requirement ID, Confluence page ID, Jira key. Use the profile's `path` template or `path_regex`. Never use a title.
4. **Anchors are canonical IDs from the registry.** Map aliases to canonical IDs (`Seating` -> `component:dcs.seat-assignment`). If a name matches no anchor, do not create one: list it under "registry candidates" in your report.
5. **Record provenance.** Every concept lists its `sources`, and specific claims carry footnotes keyed to a source `id`.
6. **Record authorship honestly.** `generated.by` is `antigravity/<model>` (or your own tool and model), `core.extraction` is `llm`, `core.confidence` is your honest confidence, and `status` is `draft`.
7. **Never claim a verification.** Do not add `verified` events for content you produced. A `human:<id>` event is added only when that person confirmed the content in this session, asked you to record it, and stated their ID.
8. **`generated.at`** is now for a new concept or a change in meaning. Always pass `--previous <last published bundle>` so the emitter carries `generated` forward for unchanged concepts and keeps review history.
9. **Keep what you do not own.** Do not delete concept files. To retire one, set `status: deprecated`, `core.valid_to`, and `superseded_by` if it was replaced.

## Procedure

1. **Scope.** Identify the source kind and its profile. Read the profile, the types it may emit, and the registry. Tell the user which sources you cannot read.
2. **Plan.** List the concepts as (type, entry_id, primary anchors). If there are more than 10, show the plan before writing.
3. **Write specs** to `.ekp/specs/<source>.yaml` in the format in `ekp_okf/spec.py`.
4. **Emit:**
   ```bash
   python -m ekp_okf.emit_cli .ekp/specs/<source>.yaml --build-dir <build> --profile <profile> \
       --build-id <group>-<UTC yyyymmddThhmmssZ> --previous <last-bundle> \
       --bundle-title "<title>" --bundle-description "<when to use this bundle>"
   ```
5. **Gate:**
   ```bash
   python -m ekp_okf.validate <build> --profile <profile> --build-id <same id> \
       --previous <last manifest> --published <published manifests dir>
   ```
   Fix the **spec** and re-emit; never patch emitted files. Repeat until PASS.
6. **Report:** files written, concepts left as draft, concepts that need a (re)verification, registry candidates, facts you could not source, the gate result.

## When a CI gate fails

Read the findings JSON. If the same code repeats across many concepts, the adapter is wrong: fix the adapter code, not the data.

| Code | Usual fix |
|---|---|
| ANC001 | Map the alias to its canonical anchor in the adapter's alias lookup |
| ID001-005 | Derive the ID from source identity in the adapter |
| LIF001 | Keep the concept: `status: deprecated`, `valid_to`, `superseded_by` |
| TRU002-003 | Emit as `Unclassified` or `draft`; do not raise confidence to pass |
| DER*, HDR001 | Something edited emitted files; re-emit from specs |
| TRU007 | Not a defect: route the concept to its owner for re-review |

## Classifying one document

When you classify a single document (a wiki page, a Jira comment, a BRD section),
follow `references/classify.md`. The pipeline's LLM lane sends the same text
to the model, so you and the pipeline make the same decisions.
