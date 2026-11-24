"""Minimal OKF v0.2 file handling: split/render frontmatter, walk a bundle."""
from __future__ import annotations

from pathlib import Path

import yaml

RESERVED = {"index.md", "log.md"}


class _Dumper(yaml.SafeDumper):
    pass


def _str_presenter(dumper, data):
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


_Dumper.add_representer(str, _str_presenter)


def split(text: str) -> tuple[dict | None, str]:
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return None, text
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        return None, text
    meta = yaml.safe_load("\n".join(lines[1:end])) or {}
    return meta, "\n".join(lines[end + 1:])


def render(meta: dict, body: str) -> str:
    fm = yaml.dump(meta, Dumper=_Dumper, sort_keys=False, allow_unicode=True, width=100).rstrip()
    return f"---\n{fm}\n---\n\n{body.strip()}\n"


def concept_files(bundle: Path):
    """Yields (entry_id, path) for every concept document in the bundle."""
    for p in sorted(bundle.rglob("*.md")):
        if p.name in RESERVED:
            continue
        rel = p.relative_to(bundle).as_posix()
        yield rel[:-3], p


def reserved_files(bundle: Path):
    for p in sorted(bundle.rglob("*.md")):
        if p.name in RESERVED:
            yield p
