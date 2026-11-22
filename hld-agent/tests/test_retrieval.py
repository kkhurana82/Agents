import sys

from hld_agent.models import Evidence
from hld_agent.retrieval.base import EvidencePool
from hld_agent.retrieval.local_docs import LocalDocsProvider, tokenize
from hld_agent.retrieval.mcp_provider import MCPSearchProvider


def test_tokenize_splits_identifiers():
    assert tokenize("SeatAssignmentService seat_map_view") == ["seat", "assignment", "service", "seat", "map", "view"]


def test_local_bm25_finds_adr_and_kind(root):
    p = LocalDocsProvider("local-kb", [root / "examples/kb"])
    [hits] = p.search_many(["seat availability read model"], 3)
    assert hits and hits[0].kind == "adr" and "adr-0007" in hits[0].uri
    [none] = p.search_many(["zzzz qqqq"], 3)
    assert none == []


def test_pool_dedupes_and_keeps_stable_ids():
    pool = EvidencePool()
    e = Evidence(source="s", title="t", uri="u", snippet="x", score=0.2)
    assert pool.add(e) == "EV-1"
    assert pool.add(e.model_copy(update={"score": 0.9})) == "EV-1"
    assert pool.items["EV-1"]["score"] == 0.9
    assert pool.add(Evidence(source="s", title="t2", uri="u2", snippet="y")) == "EV-2"
    restored = EvidencePool(pool.items)
    assert restored.add(e) == "EV-1"           # survives a checkpoint round-trip


def test_mcp_provider_stdio_roundtrip(root):
    """Real MCP session over stdio against the stub Stratum server."""
    prov = MCPSearchProvider(
        "stratum", "stdio", command=sys.executable, cmd_args=[str(root / "examples/stratum_stub_server.py")],
        tool="search", args={"query": "{query}", "k": "{k}", "domain": "dcs"},
        result={"items": "results", "snippet": "text", "kind": "artifact_type", "revision": "provenance.commit"},
        timeout_s=60)
    res = prov.search_many(["seat assignment idempotency", "party members PNR"], 2)
    assert len(res) == 2
    top = res[0][0]
    assert top.source == "stratum" and top.kind in ("code", "interface") and top.revision == "9f3c2ab"
    assert any("PnrQueryClient" in e.uri for e in res[1])


def test_mcp_provider_reports_missing_tool(root):
    prov = MCPSearchProvider("stratum", "stdio", command=sys.executable,
                             cmd_args=[str(root / "examples/stratum_stub_server.py")], tool="nope", timeout_s=60)
    try:
        prov.search_many(["x"], 1)
        raise AssertionError("expected failure")
    except RuntimeError as exc:
        assert "has no tool 'nope'" in str(exc)
