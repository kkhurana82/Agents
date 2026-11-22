"""BM25 over a local folder of standards, ADRs and past HLDs (.adoc / .md / .txt).

Good enough for a team's reference corpus (hundreds of docs). Code, interfaces and data stores
should come from the knowledge graph via MCP, not from here.
"""
from __future__ import annotations

import re
from pathlib import Path

from rank_bm25 import BM25Okapi

from ..models import Evidence

HEADING = re.compile(r"^(?:={1,6}|#{1,6})\s+(.+)$")
STOP = set("a an and are as at be by for from has in is it of on or that the this to was were will with".split())
KIND_BY_DIR = {"adr": "adr", "adrs": "adr", "decisions": "adr", "standards": "standard", "standard": "standard",
               "guidelines": "standard", "hld": "hld", "hlds": "hld", "designs": "hld"}


def tokenize(text: str) -> list[str]:
    """Identifier-aware: splits camelCase / snake_case / kebab so 'seatMapService' matches 'seat map'."""
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)
    toks = re.findall(r"[A-Za-z0-9]+", text.lower())
    return [t for t in toks if t not in STOP and len(t) > 1]


class LocalDocsProvider:
    def __init__(self, name: str, paths: list[Path], chunk_chars: int = 1200):
        self.name = name
        self.chunks: list[Evidence] = []
        for root in paths:
            files = [root] if root.is_file() else sorted(
                p for p in root.rglob("*") if p.suffix.lower() in {".adoc", ".asciidoc", ".md", ".txt"})
            for f in files:
                self.chunks.extend(self._chunk_file(f, root, chunk_chars))
        self._bm25 = BM25Okapi([tokenize(c.title + " " + c.snippet) for c in self.chunks]) if self.chunks else None

    @classmethod
    def from_config(cls, cfg: dict, base_dir: str) -> "LocalDocsProvider":
        paths = [(Path(base_dir) / p).resolve() for p in cfg.get("paths", [])]
        missing = [str(p) for p in paths if not p.exists()]
        if missing:
            raise FileNotFoundError(f"local KB path(s) not found: {missing}")
        return cls(cfg.get("name", "local-kb"), paths, cfg.get("chunk_chars", 1200))

    def _chunk_file(self, f: Path, root: Path, limit: int) -> list[Evidence]:
        rel = f.relative_to(root.parent if root.is_dir() else f.parent).as_posix()
        kind = next((KIND_BY_DIR[p.lower()] for p in f.parts if p.lower() in KIND_BY_DIR), "doc")
        doc_title, heading, buf, out = f.stem, f.stem, [], []

        def flush():
            body = "\n".join(buf).strip()
            if not body:
                return
            for n, start in enumerate(range(0, len(body), limit)):
                part = body[start:start + limit]
                out.append(Evidence(source=self.name, kind=kind, title=f"{doc_title} › {heading}",
                                    uri=f"{rel}#{re.sub(r'[^a-z0-9]+', '-', heading.lower()).strip('-')}"
                                        + (f"-{n + 1}" if n else ""),
                                    snippet=part))

        for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
            if m := HEADING.match(line):
                if line.startswith(("= ", "# ")) and doc_title == f.stem:
                    doc_title = m.group(1).strip()
                flush()
                buf, heading = [], m.group(1).strip()
            else:
                buf.append(line)
        flush()
        return out

    def search_many(self, queries: list[str], k: int) -> list[list[Evidence]]:
        if not self._bm25:
            return [[] for _ in queries]
        results = []
        for q in queries:
            scores = self._bm25.get_scores(tokenize(q))
            top = max(scores) if len(scores) else 0
            ranked = sorted(range(len(scores)), key=lambda i: -scores[i])[:k]
            results.append([self.chunks[i].model_copy(update={"score": round(float(scores[i] / top), 3)})
                            for i in ranked if top > 0 and scores[i] > 0])
        return results
