# Agents

Architecture agents that draft and check BRDs, research reports and HLDs, grounded in evidence with human approval at each step. Strategy and designs: [docs/strategy.md](docs/strategy.md).

| Agent | What it does |
|---|---|
| [hld-agent](hld-agent/) | Drafts a High-Level Design in AsciiDoc from a requirement, following the team's `.adoc` template and grounded in knowledge-base evidence (local docs + Stratum over MCP). LangGraph, with architect checkpoints. |
| research-agent | Planned: multi-document research with verified quotes. See [design](docs/strategy.md#4-research-agent). |
| brd-agent | Planned: BRD from stakeholder input with traced, quality-checked requirements. See [design](docs/strategy.md#5-brd-agent). |
