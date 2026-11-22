"""Retrieval over an MCP server (e.g. Stratum / EKG) exposing a search tool.

Talks to the server with the official `mcp` SDK (stdio or streamable HTTP). The tool name,
argument names and result shape are configuration, so no code change is needed to point
it at Stratum's real contract.

Example config (config.yaml -> retrieval.providers[]):
  - type: mcp
    name: stratum
    transport: streamable_http          # or stdio
    url: http://localhost:8000/mcp
    headers: {Authorization: "Bearer ${STRATUM_TOKEN}"}
    tool: search
    args: {query: "{query}", k: "{k}", domain: dcs}
    result:
      items: results                    # key holding the hit list ("" = top-level list)
      title: title
      uri: uri
      snippet: text
      kind: artifact_type
      score: score
      revision: provenance.commit       # dot paths allowed
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import Any

from ..models import Evidence

log = logging.getLogger(__name__)

DEFAULT_RESULT_MAP = {"items": "results", "title": "title", "uri": "uri", "snippet": "text",
                      "kind": "kind", "score": "score", "revision": "revision"}


def _dig(obj: Any, path: str | None) -> Any:
    if not path:
        return obj
    for part in path.split("."):
        if isinstance(obj, dict):
            obj = obj.get(part)
        else:
            return None
    return obj


class MCPSearchProvider:
    def __init__(self, name: str, transport: str, *, url: str | None = None, headers: dict | None = None,
                 command: str | None = None, cmd_args: list[str] | None = None, env: dict | None = None,
                 cwd: str | None = None, tool: str = "search", args: dict | None = None,
                 result: dict | None = None, timeout_s: float = 30.0):
        if transport not in ("stdio", "streamable_http"):
            raise ValueError("transport must be 'stdio' or 'streamable_http'")
        self.name, self.transport = name, transport
        self.url, self.headers = url, headers or {}
        self.command, self.cmd_args, self.env, self.cwd = command, cmd_args or [], env, cwd
        self.tool = tool
        self.args_tpl = args or {"query": "{query}", "k": "{k}"}
        self.result_map = {**DEFAULT_RESULT_MAP, **(result or {})}
        self.timeout_s = timeout_s

    @classmethod
    def from_config(cls, cfg: dict, base_dir: str) -> "MCPSearchProvider":
        return cls(
            cfg.get("name", "mcp"), cfg.get("transport", "streamable_http"),
            url=cfg.get("url"), headers=cfg.get("headers"),
            command=cfg.get("command"), cmd_args=cfg.get("args_cmd") or cfg.get("command_args"),
            env=cfg.get("env"), cwd=cfg.get("cwd") or base_dir,
            tool=cfg.get("tool", "search"), args=cfg.get("args"), result=cfg.get("result"),
            timeout_s=float(cfg.get("timeout_s", 30)),
        )

    # ---------- public ----------
    def search_many(self, queries: list[str], k: int) -> list[list[Evidence]]:
        """Sync wrapper (graph nodes are sync). One MCP session for the whole batch."""
        try:
            return asyncio.run(asyncio.wait_for(self._search_many(queries, k), self.timeout_s * max(1, len(queries))))
        except BaseExceptionGroup as eg:      # anyio task groups wrap the real cause; surface it
            leaf = eg
            while isinstance(leaf, BaseExceptionGroup) and leaf.exceptions:
                leaf = leaf.exceptions[0]
            raise leaf from eg

    # ---------- internals ----------
    @asynccontextmanager
    async def _session(self):
        from mcp import ClientSession, StdioServerParameters
        if self.transport == "stdio":
            from mcp.client.stdio import stdio_client
            cmd = sys.executable if self.command in ("python", "python3") else self.command
            params = StdioServerParameters(command=cmd, args=self.cmd_args,
                                           env={**os.environ, **(self.env or {})}, cwd=self.cwd)
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    yield session
        else:
            from mcp.client.streamable_http import streamablehttp_client
            async with streamablehttp_client(self.url, headers=self.headers) as (read, write, _sid):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    yield session

    def _render_args(self, query: str, k: int) -> dict:
        out = {}
        for key, val in self.args_tpl.items():
            if val == "{query}":
                out[key] = query
            elif val == "{k}":
                out[key] = k
            elif isinstance(val, str):
                out[key] = val.replace("{query}", query)
            else:
                out[key] = val
        return out

    async def _search_many(self, queries: list[str], k: int) -> list[list[Evidence]]:
        out: list[list[Evidence]] = []
        async with self._session() as session:
            tools = {t.name for t in (await session.list_tools()).tools}
            if self.tool not in tools:
                raise RuntimeError(f"MCP server '{self.name}' has no tool '{self.tool}' (has: {sorted(tools)})")
            for q in queries:
                res = await session.call_tool(self.tool, self._render_args(q, k))
                if res.isError:
                    log.warning("MCP %s.%s error for %r: %s", self.name, self.tool, q, res.content)
                    out.append([])
                    continue
                out.append(self._normalize(res)[:k])
        return out

    def _normalize(self, res) -> list[Evidence]:
        data: Any = res.structuredContent
        if data is None:
            text = "".join(getattr(c, "text", "") for c in res.content)
            try:
                data = json.loads(text)
            except (json.JSONDecodeError, TypeError):
                log.warning("MCP %s returned non-JSON content; ignored", self.name)
                return []
        m = self.result_map
        if isinstance(data, dict) and set(data) == {"result"} and m["items"] != "result":
            data = data["result"]          # FastMCP wraps non-object returns as {"result": ...}
        items = _dig(data, m["items"]) if isinstance(data, dict) else data
        evs: list[Evidence] = []
        for it in items or []:
            if not isinstance(it, dict):
                continue
            snippet = _dig(it, m["snippet"]) or ""
            uri = _dig(it, m["uri"]) or ""
            if not (snippet or uri):
                continue
            evs.append(Evidence(
                source=self.name,
                kind=str(_dig(it, m["kind"]) or "doc"),
                title=str(_dig(it, m["title"]) or uri),
                uri=str(uri),
                snippet=str(snippet)[:2000],
                score=float(_dig(it, m["score"]) or 0.0),
                revision=(str(r) if (r := _dig(it, m["revision"])) else None),
            ))
        return evs
