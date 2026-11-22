"""Stand-in for the Stratum/EKG MCP server, for local runs and tests (stdio transport).

Exposes `search(query, k, domain)` returning {"results": [{title, uri, text, artifact_type, score, provenance{commit}}]}.
Point the real config at Stratum instead and adjust `result:` mapping to its actual shape.
"""
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("stratum-stub")

CORPUS = [
    {"title": "SeatAssignmentService.assignSeat", "uri": "repo://dcs-seat/src/main/java/com/dcs/seat/SeatAssignmentService.java#L40",
     "text": "public SeatAssignment assignSeat(FlightId flightId, PassengerRef pax, SeatNumber seat, IdempotencyKey key) "
             "- validates carrier seat rules via SeatRuleEngine, then persists and publishes SeatAssigned.",
     "artifact_type": "code", "commit": "9f3c2ab"},
    {"title": "seat-assignment-api.yaml POST /flights/{flightId}/seat-assignments",
     "uri": "repo://dcs-seat/api/seat-assignment-api.yaml#/paths/~1flights~1{flightId}~1seat-assignments",
     "text": "OpenAPI: request {passengerId, seatNumber}; header Idempotency-Key required; 409 when seat taken; "
             "422 when a carrier seat rule rejects the seat.",
     "artifact_type": "interface", "commit": "9f3c2ab"},
    {"title": "SeatMapView (read model) table seat_map_view",
     "uri": "repo://dcs-seat/db/migrations/V12__seat_map_view.sql",
     "text": "CREATE TABLE seat_map_view (flight_id, seat_number, cabin, status, characteristics JSON, updated_at) "
             "- fed by SeatAssigned/SeatReleased consumers.",
     "artifact_type": "datastore", "commit": "41aa0de"},
    {"title": "PNR party lookup - PnrQueryClient.findPartyMembers",
     "uri": "repo://dcs-pnr/src/main/java/com/dcs/pnr/PnrQueryClient.java#L88",
     "text": "Returns passengers sharing a PNR record locator with their check-in status; cached 60 s.",
     "artifact_type": "code", "commit": "c07d11e"},
]


def _score(q: str, doc: dict) -> float:
    terms = {t for t in q.lower().replace("/", " ").split() if len(t) > 2}
    hay = (doc["title"] + " " + doc["text"]).lower()
    return sum(1 for t in terms if t in hay) / max(1, len(terms))


@mcp.tool()
def search(query: str, k: int = 5, domain: str = "dcs") -> dict:
    """Hybrid search over code, interfaces and data stores (stub: keyword overlap)."""
    ranked = sorted(CORPUS, key=lambda d: -_score(query, d))
    hits = [d for d in ranked if _score(query, d) > 0][:k]
    return {"results": [{"title": d["title"], "uri": d["uri"], "text": d["text"], "artifact_type": d["artifact_type"],
                         "score": round(_score(query, d), 3), "provenance": {"commit": d["commit"]}} for d in hits]}


if __name__ == "__main__":
    mcp.run()
