"""The reader header: the few ekp-core facts a reading agent needs, rendered
into the body. LookupContext returns the body but not custom aspects, so
anything the reader must see goes here too. Aspects are for filtering; the
body is what the agent reads.

    python -m ekp_okf.header --fix <build-dir>    # re-render every header
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from . import okf
from .kit import CORE_ASPECT, load_kit

OPEN = "<!-- ekp:header v1 -->"
CLOSE = "<!-- /ekp:header -->"
_BLOCK = re.compile(re.escape(OPEN) + r".*?" + re.escape(CLOSE) + r"\n*", re.S)


def core_of(meta: dict) -> dict:
    aspects = ((meta.get("extra") or {}).get("aspects") or {})
    for k, v in aspects.items():
        if k.endswith("." + CORE_ASPECT):
            return v or {}
    return {}


def render_header(meta: dict, kit) -> str:
    c = core_of(meta)
    ctype = c.get("concept_type", "?")
    label = kit.all_types().get(ctype, {}).get("label", ctype)
    where = " › ".join(x for x in [c.get("domain"), c.get("primary_system"),
                                     c.get("primary_component")] if x)
    rev = str(c.get("source_revision", ""))
    if re.fullmatch(r"[0-9a-f]{13,}", rev):   # shorten git SHAs only
        rev = rev[:12]
    lines = [
        OPEN,
        f"> **{label}** · {where}" if where else f"> **{label}**",
        f"> **Source:** `{c.get('source_ref', '?')}` @ `{rev}` · extraction: {c.get('extraction', '?')}"
        + (f" ({c['confidence']:.2f})" if isinstance(c.get("confidence"), (int, float)) else ""),
        f"> **Trust:** {c.get('trust_tier', '?')} · **Status:** {c.get('lifecycle', '?')}"
        f" · **Valid from:** {str(c.get('valid_from', '?'))[:10]}"
        + (f" · **Valid to:** {str(c['valid_to'])[:10]}" if c.get("valid_to") else ""),
    ]
    other = [a for a in c.get("anchors") or [] if a not in
             (c.get("primary_system"), c.get("primary_component"))]
    if other:
        lines.append("> **Also about:** " + ", ".join(f"`{a}`" for a in other))
    rels = c.get("relations") or []
    if rels:
        lines.append("> **Relations:** " + "; ".join(
            f"{r['rel'].replace('_', ' ')} `{r['target']}`" for r in rels))
    lines.append(CLOSE)
    return "\n".join(lines)


def strip_header(body: str) -> str:
    return _BLOCK.sub("", body.lstrip("\n"), count=1)


def with_header(meta: dict, body: str, kit) -> str:
    return render_header(meta, kit) + "\n\n" + strip_header(body).lstrip("\n")


def current_header(body: str) -> str | None:
    m = _BLOCK.search(body)
    return m.group(0).strip() if m else None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fix", required=True, help="build dir containing catalog.yaml and bundle/")
    args = ap.parse_args(argv)
    kit = load_kit()
    bundle = Path(args.fix) / "bundle"
    n = 0
    for _, p in okf.concept_files(bundle):
        meta, body = okf.split(p.read_text(encoding="utf-8"))
        if meta is None:
            continue
        new = okf.render(meta, with_header(meta, body, kit))
        if new != p.read_text(encoding="utf-8"):
            p.write_text(new, encoding="utf-8")
            n += 1
    print(f"re-rendered {n} header(s)")


if __name__ == "__main__":
    sys.exit(main())
