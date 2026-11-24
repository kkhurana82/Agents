"""Golden-question recall gate.

BM25 here is a stand-in so the gate runs anywhere. In EKP, swap `rank()`
for a call to the real retrieval path (router + BM25/pgvector + graph), so the
gate measures what agents will actually get.
"""
from __future__ import annotations

import math
import re
from collections import Counter

_STOP = set("a an the of to in on for and or is are be by with at as from this that it its can may "
            "must not no do does which what who when how why".split())


def tokenize(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in _STOP and len(t) > 1]


class BM25:
    def __init__(self, docs: dict[str, str], k1: float = 1.2, b: float = 0.75):
        self.ids = list(docs)
        self.tf = [Counter(tokenize(docs[i])) for i in self.ids]
        self.len = [sum(c.values()) for c in self.tf]
        self.avg = (sum(self.len) / len(self.len)) if self.len else 0.0
        n = len(self.ids)
        df = Counter(t for c in self.tf for t in c)
        self.idf = {t: math.log(1 + (n - d + 0.5) / (d + 0.5)) for t, d in df.items()}
        self.k1, self.b = k1, b

    def rank(self, query: str, k: int) -> list[str]:
        q = tokenize(query)
        scores = []
        for i, tf in enumerate(self.tf):
            s = 0.0
            for t in q:
                if t in tf:
                    f = tf[t]
                    s += self.idf[t] * f * (self.k1 + 1) / (
                        f + self.k1 * (1 - self.b + self.b * self.len[i] / (self.avg or 1)))
            scores.append((s, self.ids[i]))
        scores.sort(key=lambda x: (-x[0], x[1]))
        return [cid for s, cid in scores[:k] if s > 0]


def recall_at_k(docs: dict[str, str], questions: list[dict], k: int) -> dict:
    """Only questions that expect at least one concept from THIS build count,
    and only their expectations that live in this build are scored."""
    engine = BM25(docs)
    rows = []
    for q in questions:
        local = [c for c in q.get("expect", []) if c in docs]
        if not local:
            continue
        got = engine.rank(q["q"], k)
        hit = [c for c in local if c in got]
        rows.append({"q": q["q"], "expected": local, "retrieved": got, "recall": len(hit) / len(local)})
    score = sum(r["recall"] for r in rows) / len(rows) if rows else None
    return {"k": k, "score": score, "questions": len(rows), "detail": rows}
