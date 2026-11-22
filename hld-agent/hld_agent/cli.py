"""hld-agent CLI.

  hld-agent run    --config config.yaml --requirement req.md [--story-id ID] [--thread T] [--interactive]
  hld-agent resume --config config.yaml --thread T --response out/T.pending.yaml
  hld-agent status --config config.yaml --thread T

Non-interactive runs stop at each architect checkpoint and write <output_dir>/<thread>.pending.yaml.
Fill in the `response:` block and run `resume`. The thread state lives in the SQLite checkpoint DB, so the
architect can answer hours later, from another machine, or via a ticket comment that a bot turns into YAML.
"""
from __future__ import annotations

import argparse
import logging
import os
import re
import sys
import uuid
from pathlib import Path

import yaml
from langgraph.types import Command

from .graph import Settings, build_graph
from .llm import build_llm
from .retrieval import build_providers
from .template import parse_template

log = logging.getLogger("hld_agent")


def _expand(obj):
    if isinstance(obj, str):
        return os.path.expandvars(obj)
    if isinstance(obj, list):
        return [_expand(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _expand(v) for k, v in obj.items()}
    return obj


def load_config(path: str) -> tuple[dict, Path]:
    p = Path(path).resolve()
    return _expand(yaml.safe_load(p.read_text())), p.parent


def _runtime(cfg: dict, base: Path, checkpointer):
    template = parse_template(base / cfg["template"])
    providers = build_providers(cfg.get("retrieval", {}).get("providers", []), str(base))
    graph = build_graph(llm=build_llm(cfg.get("llm", {})), template=template, providers=providers,
                        settings=Settings.from_dict(cfg.get("agent")), checkpointer=checkpointer)
    return graph, template


def _pending_doc(thread: str, payload: dict) -> dict:
    if payload["type"] == "questions":
        return {"type": "questions", "thread": thread,
                "instructions": "Answer under response.answers. Leave blank to accept the default assumption.",
                "questions": [{k: q[k] for k in ("id", "question", "why_it_matters", "default_assumption", "blocking")}
                              for q in payload["questions"]],
                "response": {"answers": {q["id"]: "" for q in payload["questions"]}}}
    return {"type": "decisions", "thread": thread,
            "instructions": "Per decision: accept | reject | {choice: ..., rationale: ...} to amend. "
                            "Or set approve_all: true.",
            "decisions": [{k: d[k] for k in ("id", "title", "options", "choice", "rationale", "evidence_ids")}
                          for d in payload["decisions"]],
            "response": {"approve_all": False, "decisions": {d["id"]: "accept" for d in payload["decisions"]}}}


def _to_resume(pending_type: str, response: dict):
    response = response or {}
    if pending_type == "questions":
        return {"answers": {k: (v or "") for k, v in (response.get("answers") or {}).items()}}
    return {"approve_all": bool(response.get("approve_all")), "decisions": response.get("decisions") or {}}


def _ask_interactive(payload: dict):
    print()
    if payload["type"] == "questions":
        print("== Architect questions (Enter = accept default) ==")
        answers = {}
        for q in payload["questions"]:
            print(f"\n{q['id']}: {q['question']}\n   why: {q['why_it_matters']}\n   default: {q['default_assumption']}")
            answers[q["id"]] = input("   answer> ").strip()
        return {"answers": answers}
    print("== Proposed design decisions ==")
    per = {}
    for d in payload["decisions"]:
        print(f"\n{d['id']}: {d['title']}\n   options: {' | '.join(d['options'])}\n   choice: {d['choice']}"
              f"\n   rationale: {d['rationale']}")
        a = input("   [a]ccept / [r]eject / [e]dit choice (default a)> ").strip().lower()
        if a.startswith("r"):
            per[d["id"]] = "reject"
        elif a.startswith("e"):
            per[d["id"]] = {"choice": input("   new choice> ").strip(), "rationale": input("   rationale> ").strip()}
        else:
            per[d["id"]] = "accept"
    return {"decisions": per}


def _drive(graph, config: dict, first_input, cfg: dict, base: Path, thread: str, interactive: bool) -> int:
    out_dir = base / cfg.get("output_dir", "out")
    out_dir.mkdir(parents=True, exist_ok=True)
    inp = first_input
    while True:
        result = graph.invoke(inp, config)
        intr = result.get("__interrupt__")
        if not intr:
            break
        payload = intr[0].value
        if interactive:
            inp = Command(resume=_ask_interactive(payload))
            continue
        pending = out_dir / f"{thread}.pending.yaml"
        pending.write_text(yaml.safe_dump(_pending_doc(thread, payload), sort_keys=False, allow_unicode=True, width=110))
        print(f"Paused for architect input ({payload['type']}). Edit {pending} then run:\n"
              f"  hld-agent resume --config <config> --thread {thread} --response {pending}")
        return 3

    state = graph.get_state(config).values
    slug = re.sub(r"[^a-z0-9]+", "-", state["brief"]["title"].lower()).strip("-")[:60]
    adoc = out_dir / f"{slug}-hld.adoc"
    adoc.write_text(state["document"], encoding="utf-8")
    rev = out_dir / f"{slug}-hld.review.yaml"
    rev.write_text(yaml.safe_dump(state["review"], sort_keys=False, allow_unicode=True, width=110))
    r = state["review"]
    print(f"\nHLD draft: {adoc}\nReview:    {rev}\nStatus: {r['status']} | requirements covered {r['requirements_covered']}"
          f" | evidence cited {r['evidence_cited']}/{r['evidence_retrieved']} | revision rounds {r['revision_rounds']}"
          f" | open findings {len(r['findings'])}")
    for w in r.get("retrieval_warnings", []):
        print(f"WARNING: {w}")
    (out_dir / f"{thread}.pending.yaml").unlink(missing_ok=True)
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="hld-agent", description="Author an HLD (AsciiDoc) from a requirement.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--config", required=True)
    r.add_argument("--requirement", required=True, help="Requirement/story text file (.md/.txt/.adoc)")
    r.add_argument("--story-id")
    r.add_argument("--thread", help="Thread id for resume (default: random)")
    r.add_argument("--interactive", action="store_true", help="Answer checkpoints in the terminal")
    s = sub.add_parser("resume")
    s.add_argument("--config", required=True)
    s.add_argument("--thread", required=True)
    s.add_argument("--response", required=True, help="Filled-in pending YAML")
    s.add_argument("--interactive", action="store_true")
    st = sub.add_parser("status")
    st.add_argument("--config", required=True)
    st.add_argument("--thread", required=True)
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING, format="%(levelname)s %(name)s: %(message)s")

    cfg, base = load_config(args.config)
    db = base / cfg.get("checkpoint_db", "out/hld-threads.sqlite")
    db.parent.mkdir(parents=True, exist_ok=True)
    from langgraph.checkpoint.sqlite import SqliteSaver
    with SqliteSaver.from_conn_string(str(db)) as cp:
        graph, _ = _runtime(cfg, base, cp)
        if args.cmd == "run":
            thread = args.thread or f"hld-{uuid.uuid4().hex[:8]}"
            print(f"thread: {thread}")
            req = Path(args.requirement).read_text(encoding="utf-8")
            return _drive(graph, {"configurable": {"thread_id": thread}},
                          {"requirement": req, "story_id": args.story_id or ""}, cfg, base, thread, args.interactive)
        config = {"configurable": {"thread_id": args.thread}}
        snap = graph.get_state(config)
        if args.cmd == "status":
            pend = [i.value for t in snap.tasks for i in t.interrupts]
            print(f"next: {list(snap.next) or 'done'}")
            if pend:
                print(yaml.safe_dump(_pending_doc(args.thread, pend[0]), sort_keys=False, width=110))
            return 0
        pend = [i.value for t in snap.tasks for i in t.interrupts]
        if not pend:
            print("Nothing pending for this thread.", file=sys.stderr)
            return 2
        doc = yaml.safe_load(Path(args.response).read_text())
        if doc.get("type") != pend[0]["type"]:
            print(f"Response type {doc.get('type')!r} does not match pending {pend[0]['type']!r}.", file=sys.stderr)
            return 2
        return _drive(graph, config, Command(resume=_to_resume(doc["type"], doc.get("response"))),
                      cfg, base, args.thread, args.interactive)


if __name__ == "__main__":
    sys.exit(main())
