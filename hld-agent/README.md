# hld-agent

A LangGraph agent that writes a **High-Level Design in AsciiDoc**. It takes a requirement or story and drafts each section of your team's `.adoc` HLD template. It grounds the draft in your knowledge base: Stratum/EKG over MCP, plus local standards, ADRs and past HLDs. An architect stays in control at two checkpoints.

```
intake -> retrieve -> gap questions --(architect answers)--> propose decisions --(architect accepts/amends/rejects)-->
draft sections -> lint + critic --(blocker/major, max N rounds: redraft only failing sections)--> assemble .adoc + review
```

## Why it is shaped this way

| Choice | Reason |
|---|---|
| **Decisions before prose** | Correcting 3-8 decisions is cheap; correcting 20 pages is expensive. Sections are drafted only after the architect confirms decisions, and lint flags references to rejected or unknown decisions. |
| **Template is data** | Sections, sub-headings and guidance come from your `.adoc` template. A template change needs no code change. |
| **Grounding is enforced** | Every `<<EV-n>>` must resolve to retrieved evidence (L003). Sections about existing systems must cite evidence (L004). The critic checks that each citation supports its claim. The evidence appendix records each source's URI and commit. |
| **Deterministic before LLM** | Markdown slips (fences, `#` headings, links) are converted to AsciiDoc in code, not in a revision round. Structural rules are lint, not prompts. |
| **Targeted revision** | Only sections with blocker/major findings are redrafted, and rounds are capped. Whatever remains goes in the review report. Nothing is silently dropped. |

## Quick start (offline, no model keys)

```bash
pip install -e ".[dev]"
cp demo-config.yaml my.yaml   # llm.model: fake = scripted stand-in model, shows structure only
hld-agent run --config my.yaml --requirement examples/requirement_seat_concierge.md --story-id US-1234 --interactive
```

Without `--interactive`, the run stops at each checkpoint and writes `out/<thread>.pending.yaml`. Fill in its `response:` block, then continue:

```bash
hld-agent resume --config my.yaml --thread <thread> --response out/<thread>.pending.yaml
hld-agent status --config my.yaml --thread <thread>
```

Thread state is kept in SQLite, so the architect can answer hours later. A bot could also turn a ticket comment into the response YAML.

Outputs: `out/<title>-hld.adoc` (the draft) and `out/<title>-hld.review.yaml` (status, coverage, remaining findings, retrieval warnings). `examples/sample-output/` has the result of a scripted-model run. Look at it for structure, traceability and appendices; the prose is filler.

## Real model

```yaml
llm:
  model: google_vertexai:gemini-2.5-pro        # pip install -e ".[vertex]"
  task_models: {critic: anthropic:claude-sonnet-4-5}   # a different model family as reviewer catches more
```

Any `init_chat_model` string works. Each step asks for a Pydantic-validated structured output.

## Using your own AsciiDoc template

Point `template:` at your `.adoc` file. The parser keeps the document header and attributes, anchors (`[[id]]`, `[#id]`) and `[appendix]` lines. It turns each `==` section into one drafting unit. Its `===`/`====` headings become a required outline, and its body text and comments become guidance. Headings inside listing, literal and comment blocks are ignored.

Defaults are inferred from titles. "Revision history" and "Approvals" are kept verbatim. "Deployment" suggests a deployment diagram. "Non-functional" owns NFR coverage. To override, add optional comments, which are invisible when rendered:

```asciidoc
== Integration and Interfaces
// hld: diagram=sequence, min_citations=1
// hld-check: Each interface states protocol, direction, sync/async and error handling
Describe consumed and exposed interfaces...
```

Hints: `mode=manual|generate`, `diagram=context|container|sequence|deployment|none`, `min_citations=N`, `grounded=true|false`, `role=nfr|requirements|decisions|open_issues`, `evidence=adr|standard|code`.

Check what the parser sees before a run:

```bash
python -c "from hld_agent.template import parse_template as p; [print(s.id, s.mode, s.diagram, s.role, [x.title for x in s.subsections]) for s in p('your.adoc').sections]"
```

Diagrams: `agent.diagram_syntax: mermaid | plantuml`. To render them you need asciidoctor-diagram or Kroki in your pipeline.

## Connecting Stratum (MCP)

Configure `retrieval.providers[].type: mcp` with `transport: streamable_http` (or `stdio`), the tool name, the argument template and a `result:` mapping onto evidence fields (dot paths allowed). See `config.example.yaml`. `examples/stratum_stub_server.py` is a stand-in with the same contract. If a provider fails, the run continues, and the failure appears in `retrieval_warnings` in the review report.

## Tests

```bash
pytest -q
```

The tests cover template parsing (anchors, blocks, hints), lint rules, AsciiDoc normalisation, BM25 retrieval, a real stdio MCP session with the stub server, and an end-to-end run with both interrupts. One fault is injected on purpose: a hallucinated citation that must be caught and redrafted. The run also includes a provider outage, and its output is rendered with Asciidoctor using `--failure-level WARN`.

## Known limits

- **Quality depends on the model and the prompts** (`hld_agent/prompts.py`). Scripted-model runs prove the wiring, not design quality.
- The critic checks citations against the evidence snippets only. It cannot spot a wrong reading of real facts, so architect review stays mandatory.
- Sections are drafted one after another, so later sections stay consistent with earlier ones. Expect a few minutes per HLD with a large model.
- `MCPSearchProvider` opens one session per retrieval batch, and its sync wrapper uses `asyncio.run`. If you call it from inside an existing event loop, call `_search_many` instead.

## Next step: measure it

Pick 3-5 features that already have an approved HLD, run the agent on their original stories, and compare the drafts against the approved versions. Score decision agreement, how many invented components there are (should be zero), requirement coverage, and how long the architect takes to edit the draft into shape. Tune the prompts and template hints on those results before rolling it out.
