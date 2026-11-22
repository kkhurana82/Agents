import re
import sys

import pytest
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from hld_agent.graph import Settings, build_graph
from hld_agent.retrieval.local_docs import LocalDocsProvider
from hld_agent.retrieval.mcp_provider import MCPSearchProvider
from hld_agent.template import parse_template
from hld_agent.testing.fake_llm import ScriptedLLM

from .conftest import asciidoctor_bin, render_adoc


class BrokenProvider:
    name = "broken"

    def search_many(self, queries, k):
        raise ConnectionError("server down")


@pytest.fixture
def setup(root):
    template = parse_template(root / "templates/sample_hld_template.adoc")
    providers = [
        LocalDocsProvider("local-kb", [root / "examples/kb"]),
        MCPSearchProvider("stratum", "stdio", command=sys.executable,
                          cmd_args=[str(root / "examples/stratum_stub_server.py")],
                          args={"query": "{query}", "k": "{k}"},
                          result={"items": "results", "snippet": "text", "kind": "artifact_type",
                                  "revision": "provenance.commit"}, timeout_s=60),
        BrokenProvider(),
    ]
    llm = ScriptedLLM()
    graph = build_graph(llm=llm, template=template, providers=providers,
                        settings=Settings(max_revisions=2), checkpointer=InMemorySaver())
    req = (root / "examples/requirement_seat_concierge.md").read_text()
    return graph, template, llm, req


def test_end_to_end_with_interrupts(setup, tmp_path):
    graph, template, llm, req = setup
    cfg = {"configurable": {"thread_id": "t1"}}

    r = graph.invoke({"requirement": req, "story_id": "US-1234"}, cfg)
    assert r["__interrupt__"][0].value["type"] == "questions"
    assert "draft" not in llm.calls                                   # nothing drafted before the architect answers

    r = graph.invoke(Command(resume={"answers": {"Q-1": "Cached read model is fine for display.", "Q-2": ""}}), cfg)
    payload = r["__interrupt__"][0].value
    assert payload["type"] == "decisions" and [d["id"] for d in payload["decisions"]] == ["DEC-1", "DEC-2", "DEC-3"]

    r = graph.invoke(Command(resume={"decisions": {
        "DEC-1": "accept",
        "DEC-2": {"choice": "CQRS read model via ADR-0007 SeatMapView", "rationale": "Already accepted pattern."},
        "DEC-3": "reject"}}), cfg)
    assert "__interrupt__" not in r

    st = graph.get_state(cfg).values
    doc, review = st["document"], st["review"]

    # clarifications: architect answer + default
    clar = {c["id"]: c for c in st["clarifications"]}
    assert clar["Q-1"]["source"] == "architect" and clar["Q-2"]["source"] == "default"

    # decisions honoured
    assert {d["id"]: d["status"] for d in st["decisions"]} == {"DEC-1": "accepted", "DEC-2": "amended", "DEC-3": "rejected"}
    assert "CQRS read model via ADR-0007 SeatMapView" in doc
    assert "DEC-3" not in doc and "New broker" not in doc

    # revise loop: hallucinated <<EV-99>> caught by lint, only that section redrafted, then clean
    assert st["revision"] == 1
    assert llm.calls.count("draft") == len(template.generate_sections) + 1
    assert "EV-99" not in doc
    assert not [f for f in review["findings"] if f["severity"] in ("blocker", "major")]

    # template fidelity: every section in order, manual sections verbatim, header attributes kept
    positions = [doc.index(s.heading_line) for s in template.sections]
    assert positions == sorted(positions)
    assert "|0.1 | | |Initial draft" in doc
    assert ":sectnums:" in doc and ":hld-status: DRAFT" in doc and ":hld-story: US-1234" in doc
    assert "```" not in doc                                             # markdown fences normalised away

    # grounding: every citation resolves to an anchor in the evidence appendix
    cited = set(re.findall(r"<<(EV-\d+)>>", doc))
    anchors = set(re.findall(r"\[\[(EV-\d+),", doc))
    assert cited and cited <= anchors
    assert any(st["evidence"][e]["source"] == "stratum" for e in cited)
    assert review["requirements_covered"] == f"{len(st['brief']['requirements'])}/{len(st['brief']['requirements'])}"

    # failed provider degrades but is reported
    assert any("broken" in w for w in review["retrieval_warnings"])

    out = tmp_path / "hld.adoc"
    out.write_text(doc)
    if asciidoctor_bin():
        res = render_adoc(out)
        assert res.returncode == 0, res.stderr


def test_auto_approve_and_no_questions(root):
    template = parse_template(root / "templates/sample_hld_template.adoc")
    graph = build_graph(llm=ScriptedLLM(), template=template, providers=[],
                        settings=Settings(auto_approve_decisions=True, ask_questions=False, max_revisions=1),
                        checkpointer=InMemorySaver())
    req = (root / "examples/requirement_seat_concierge.md").read_text()
    r = graph.invoke({"requirement": req}, {"configurable": {"thread_id": "t2"}})
    assert "__interrupt__" not in r and r["document"]
    # with no evidence at all, sections that demand citations must be flagged, not silently pass
    assert any(f["rule"] == "L004" for f in r["review"]["findings"])
    assert r["review"]["status"] == "needs_attention"
