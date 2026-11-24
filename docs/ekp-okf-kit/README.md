# EKP OKF build kit

One contract that every EKP ingestion build must meet before `kcmd push`:
any code repo in the enterprise (any language, legacy, API specs, schemas, rule
tables, Terraform/Helm), architecture docs and HLDs, BRDs, wiki and Jira. Sources
change how you extract. They never change the shape of what comes out.

Targets **OKF v0.3** (canonical spec: `open-knowledge-format/open-knowledge-format`)
and **kcmd's native OKF layout** (`GoogleCloudPlatform/knowledge-catalog`,
`toolbox/mdcode`, `kcmd init --format okf`), not the older `demo/okf` wrapper.

Worked examples, one per source kind, are in [samples/EXAMPLES.md](samples/EXAMPLES.md).
All sample data is synthetic.

```
ontology/types.yaml      concept types (anchor + knowledge), per-type facets, typed relations
ontology/core.yaml       ekp-core aspect fields: the uniform filter surface
ontology/vocab.yaml      controlled vocabularies the gate enforces
anchors/registry.yaml    canonical anchor IDs + aliases (the join keys across sources)
profiles/*.yaml          one per source kind: what it may emit, ID rules, trust policy
                         (code-repo covers every repo kind through a list of extractors)
ekp_okf/emit.py      the one function every adapter calls to write a concept
ekp_okf/header.py    reader header rendered into the body (+ --fix)
ekp_okf/validate.py  the build gate (run before kcmd push)
ekp_okf/recall.py    golden-question recall gate (BM25 stand-in for your retriever)
ekp_okf/spec.py      concept spec format + JSON schema for model output
ekp_okf/emit_cli.py  specs -> OKF files (used by agents and the LLM lane)
pipeline/llm_lane.py LLM lane for documents with no deterministic signal
.agents/skills/ekp-okf/  the skill (Antigravity workspace path; portable)
catalog/gen_aspects.py   aspect-type JSON generated from the ontology
catalog/setup_aspects.sh registers the aspect types with gcloud
catalog/kcmd_preview/    runs Google's kcmd converter locally to show the catalog Entry
samples/                 synthetic inputs, 10 builds, demo run (5 passes), EXAMPLES.md
```

Requirements: Python 3.10+ with PyYAML and jsonschema. The preview needs bun and a
checkout of `GoogleCloudPlatform/knowledge-catalog`.

Quick start, from this folder:

```bash
pip install pyyaml jsonschema
./samples/run_demo.sh            # 5 passes: first builds, steady state, defects, re-review, LLM lane
less samples/EXAMPLES.md         # one worked example per source kind
```

## The contract

1. **Organise by knowledge type, not source.** `ontology/types.yaml` is a closed
   set. A business rule is a `BusinessRule` whether it came from TPF C, a BRD or a
   Jira comment.
2. **Every concept resolves anchors** from `anchors/registry.yaml`. Only the
   registry build creates anchors. Adapters map aliases (Jira components,
   Confluence spaces, repo names) to canonical IDs. Writing an alias is an error.
3. **IDs derive from source identity**, never from titles: repo path + symbol +
   condition hash, HLD section ID, requirement ID, Confluence page ID, Jira key.
   Each profile pins this with `path_regex` + `source_ref_regex`. Named groups
   must agree.
4. **Aspects are for filtering; the body is for reading.** `ekp-core` and the
   per-type facet carry flat scalars for `searchEntries`. The reader header
   repeats what an agent needs, because LookupContext returns the body, not
   custom aspects.
5. **Trust is derived, never typed.** `trust_tier` comes from the *current* OKF
   `verified` events: those at or after `generated.at` (OKF v0.3 §5.3). Content
   extracted by an LLM must stay `draft` until something verifies it.
6. **`generated.at` is the last meaningful change, not the build time.** For
   deterministic/template extraction pass the source's change time; for LLM
   extraction pass the generation time. Give `emit_concept()` the last published
   bundle (`previous_bundle=`) and it carries `generated` forward when nothing
   meaningful changed, keeps old reviews as history, and lets trust drop when the
   content really changed. Stamp the build time instead and every rebuild voids
   every human review.
7. **Nothing disappears.** Removed knowledge stays as `status: deprecated` with
   `valid_to`, plus `superseded_by` (OKF v0.3 §5.4) when it moved or was replaced.
   That is your temporal history.
8. **Every bundle describes itself.** The bundle-root `index.md` carries
   `okf_version`, `title` and a `description` saying when to use the bundle
   (OKF v0.3 §8.1). kcmd publishes it as the group's root entry, so an agent facing
   many EKP bundles can pick the right one.

## One profile per source kind, one extractor per repo kind

`profiles/code-repo.yaml` serves every code repo. A repo runs every extractor
whose `detect` matches: app code (tree-sitter per language), legacy code (TPF C,
HLASM, COBOL), API specs (OpenAPI, proto, AsyncAPI, GraphQL), data schemas (DDL,
dbt, Avro), rule tables, Terraform, Helm/Kubernetes. They all emit the same
ontology types, so a rules-table row in a Java service and a check in TPF C are
both `BusinessRule`, linked by `same_as` (see `samples/builds/code-seat-service`).
Architecture docs that live in a code repo run as a separate `arch-doc` build.

## How a build runs in CI

```bash
adapter --out build/                         # calls ekp_okf.emit.emit_concept(...)
python -m ekp_okf.header --fix build/    # only if anything edited bodies after emit
python -m ekp_okf.validate build/ --profile jira --build-id "$BUILD_ID" \
    --previous published/jira-seat.manifest.json --published published/ --golden golden/ \
    --write-manifest published/jira-seat.manifest.json
(cd build && kcmd push --validate-only)      # review creates/updates/DELETES
(cd build && kcmd push)
```

`build/` is a kcmd OKF workspace: `catalog.yaml` (`scope: entryGroup.<project>.<location>.<group>`,
`layout: okf`) plus `bundle/`. Run `samples/run_demo.sh` to see all three passes.

## Knowledge Catalog behaviour this kit is built around

These were checked against the kcmd source (`toolbox/mdcode`, commit `0003e7f`,
2026-11-23), not only the August 2026 blog post. Several differ from that post.

* **kcmd push in the native OKF layout is a full sync.** It upserts every local
  concept and **deletes remote entries that are not in the local bundle**. So:
  * one entry group per build (shared groups delete each other's entries), and
  * the gate's `LIF001` blocks a concept from vanishing; deprecate it instead.
* **Concepts become `dataplex-types.global.document` entries.** The OKF `type` is
  slugged into the `document` aspect (`Business Rule` → `business-rule`). OKF
  signal fields (`status`, `verified`, `sources`) go into a trailing `## OKF Metadata`
  block in the body, **not into a filterable aspect**. That is why `ekp-core`
  mirrors `lifecycle` and `trust_tier`.
* **`extra.aspects` in frontmatter becomes real aspects** on the entry. That is how
  `ekp-core` and the facets get pushed. See `samples/catalog_preview/`.
* **A `publishing:` block in catalog.yaml filters aspects.** If you add one, list
  every `ekp-*` aspect in it, or kcmd silently drops them.
* **Array fields are not filterable server-side.** Hence `primary_system`,
  `primary_component` and `primary_capability` as scalars, with the full list in
  `anchors`.
* **Aspect templates are append-only.** `gen_aspects.py` keeps field indexes
  stable and refuses to remove fields.

Search predicate shape (from Google's published example):
`aspect:<project>.<location>.ekp-core.concept_type="BusinessRule"`.
[Likely] Values that contain `:` (anchor IDs) need the quotes. Confirm this
with one `gcloud dataplex entries search` on the first real push. If quoting
fails, switch the anchor separator before any bundles exist.

## Gate checks

| Code | Severity | Catches |
|---|---|---|
| GRP001 | error | Entry group not matching the profile (one group per build) |
| OKF001-003 | error/warn | Missing or unparseable frontmatter, missing `type`, index.md misuse |
| ONT001-002 | error | Type not in the ontology, or not allowed for this profile |
| FM001-004 | error | Missing title/description/generated/sources, invalid status |
| ASP001-004 | error | Missing or misplaced ekp aspects, wrong project/location |
| CORE001-003, FAC001-004 | error | Unknown fields (typos), missing required fields, wrong types or enums |
| VOC001-006 | error | Vocabulary, pattern, source kind/system, build_id, profile, ontology version |
| DER001-004 | error | Derived fields (type, lifecycle, trust tier, concept_id) hand-edited or wrong |
| ID001-005 | error | Title-derived IDs, path/source_ref disagreement, duplicate source units |
| TRU002-006 | error | LLM confidence below minimum, unverified LLM content not draft, extraction not allowed, malformed verified event |
| TRU007 | warn | A human review stopped being current because the content changed: route for re-review |
| ANC001-005 | error | Alias or unknown anchors, primary_* inconsistent, domain/system mismatch |
| REL001-004, 007 | error | Unknown relation, wrong source/target types, missing in-build target, anchor used as target |
| REL005-006 | warn | Cross-build target not published yet, or deprecated |
| HDR001 | error | Reader header missing or stale |
| LNK001 | warn | Bundle-relative link that does not resolve |
| LIF001-005 | error/warn | Vanished concept, deprecation without valid_to, ID reused, non-deterministic emitter, bad superseded_by |
| OKF004 | warn | Bundle-root index.md without okf_version/title/description |
| RCL001-002 | error/warn | Golden recall dropped vs last build, or a question below 1.0 |

## Antigravity and the pipeline: one contract, two runtimes

Antigravity is where people and agents *author and fix* EKP knowledge. The
ingestion pipeline is where it is *produced at scale*. They share the contract,
not the runtime:

| | Antigravity (IDE or `agy` CLI) | Ingestion pipeline |
|---|---|---|
| Skill / prompt | `.agents/skills/ekp-okf/` | same `references/classify.md` as the LLM lane prompt |
| Output | concept specs → `ekp_okf.emit_cli` | adapters → `emit_concept()`; LLM lane → specs → `emit_specs()` |
| Model output shape | free, then the gate | `ekp_okf.spec.model_schema()` as structured output |
| Referee | `ekp_okf.validate` | `ekp_okf.validate` before `kcmd push` |

* **Antigravity:** open `docs/ekp-okf-kit/` (plus a checked-out bundle) as the
  workspace. Antigravity reads skills from `<workspace-root>/.agents/skills/`, so
  if you open the repo root instead, copy or symlink `.agents/skills/ekp-okf`
  there. The `ekp-okf` skill loads when you ask for EKP knowledge.
  Use it to write and debug extractors against sample repos, to bootstrap
  sources with no adapter yet, and to fix failed CI gates from the findings JSON.
  Claude Code or Codex can use the same skill; symlink it into `.claude/skills/`.
  Google's own `okf-generate` and `okf-consume` skills can sit alongside it. For EKP
  bundles, `ekp-okf` takes precedence.
* **Pipeline:** deterministic adapters for everything that has a reliable
  signal. `pipeline/llm_lane.py` only handles documents with no signal (unlabelled
  wiki pages, Jira comments, BRD prose). Code assigns identity, the model assigns
  meaning, policy quarantines low confidence, and the gate decides. Use Vertex AI
  Gemini (`--model gemini-...`) for scale. `--model agy` (headless `agy -p
  --json-schema`) suits small scheduled runs under your own login. It has not been run here.

## Repos to know

* `open-knowledge-format/open-knowledge-format`: canonical OKF spec (v0.3), Google's
  reference producer, sample bundles, `okf-generate` / `okf-consume` agent skills,
  and `connectors/gcp-knowledge-catalog.md`.
* `GoogleCloudPlatform/knowledge-catalog`: kcmd (`toolbox/mdcode`), enrichment agent,
  catalog samples. Its `okf/` folder is a frozen old copy; do not build against it.
* `GoogleCloudPlatform/open-knowledge-format`: deprecated intermediate home.

## Not included (your side)

* **The real adapters.** `samples/make_samples.py` hand-specifies what each adapter
  would decide. Your tree-sitter extractor, HLD parser and Jira/Confluence
  readers call `emit_concept()`.
* **Reconciliation.** The BRD rule's `same_as` edge to the code rule is a candidate.
  A small job should confirm or reject these candidates using source refs, conditions and anchors.
* **Neo4j projection.** Build it from `ekp-core.relations` plus anchors, read
  from the bundles or the published manifests. kcmd can also push frontmatter
  `links` as catalog EntryLinks, but LookupContext does not traverse them, so
  Neo4j stays the traversal engine.
* **The recall gate's retriever.** Swap `recall.BM25` for your router +
  BM25/pgvector + graph, so the gate measures what agents actually get.
