"""Provider contract and the evidence pool that gives every retrieved item a stable citation ID."""
from __future__ import annotations

import hashlib
import logging
from typing import Protocol

from ..models import Evidence

log = logging.getLogger(__name__)


class ContextProvider(Protocol):
    name: str

    def search_many(self, queries: list[str], k: int) -> list[list[Evidence]]:
        """One result list per query, best first. Must not raise for 'no hits'."""
        ...


class EvidencePool:
    """Deduplicates evidence across providers/queries and assigns EV-n IDs in first-seen order.

    IDs are stable for the life of a thread (pool is persisted in graph state), so citations
    written in an early draft remain valid across revision rounds.
    """

    def __init__(self, items: dict[str, dict] | None = None):
        self.items: dict[str, dict] = dict(items or {})
        self._by_key = {v["key"]: k for k, v in self.items.items()}

    def add(self, ev: Evidence) -> str:
        key = ev.key or hashlib.sha1(f"{ev.source}|{ev.uri}|{ev.snippet[:300]}".encode()).hexdigest()[:16]
        if key in self._by_key:
            eid = self._by_key[key]
            if ev.score > self.items[eid].get("score", 0):
                self.items[eid]["score"] = ev.score
            return eid
        eid = f"EV-{len(self.items) + 1}"
        self.items[eid] = ev.model_copy(update={"id": eid, "key": key}).model_dump()
        self._by_key[key] = eid
        return eid

    def get(self, eid: str) -> dict | None:
        return self.items.get(eid)


def build_providers(cfg: list[dict], base_dir: str = ".") -> list[ContextProvider]:
    providers: list[ContextProvider] = []
    for p in cfg or []:
        ptype = p.get("type")
        if ptype == "local":
            from .local_docs import LocalDocsProvider
            providers.append(LocalDocsProvider.from_config(p, base_dir))
        elif ptype == "mcp":
            from .mcp_provider import MCPSearchProvider
            providers.append(MCPSearchProvider.from_config(p, base_dir))
        else:
            raise ValueError(f"unknown retrieval provider type: {ptype!r}")
    return providers
