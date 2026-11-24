"""Loads the contract: ontology, core aspect fields, vocab, anchor registry, profiles."""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

KIT_ROOT = Path(__file__).resolve().parent.parent
CORE_ASPECT = "ekp-core"


def _load(path: Path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


@dataclass
class Profile:
    name: str
    version: int
    source_kind: str
    source_systems: list
    entry_group_regex: str
    emits: dict
    policy: dict = field(default_factory=dict)

    @property
    def ref(self) -> str:
        return f"{self.name}@{self.version}"


@dataclass
class Kit:
    root: Path
    ontology_version: str
    anchor_types: dict
    knowledge_types: dict
    facets: dict
    relations: dict
    core_fields: dict
    vocab: dict
    anchors: dict            # canonical id -> anchor record
    alias_index: dict        # lower-cased alias -> canonical id
    profiles: dict

    # ---- type helpers -------------------------------------------------
    def all_types(self) -> dict:
        return {**self.anchor_types, **self.knowledge_types}

    def is_anchor_type(self, t: str) -> bool:
        return t in self.anchor_types

    def label_of(self, t: str) -> str:
        return self.all_types()[t]["label"]

    def type_from_label(self, label: str) -> str | None:
        for name, spec in self.all_types().items():
            if spec["label"] == label:
                return name
        return None

    def facet_of(self, t: str) -> str | None:
        return self.knowledge_types.get(t, {}).get("facet")

    def anchor_kind(self, anchor_id: str) -> str:
        return anchor_id.split(":", 1)[0]

    def anchor_type_for_prefix(self, prefix: str) -> str | None:
        for name, spec in self.anchor_types.items():
            if spec["prefix"] == prefix:
                return name
        return None


def load_kit(root: str | os.PathLike | None = None) -> Kit:
    root = Path(root) if root else KIT_ROOT
    types = _load(root / "ontology" / "types.yaml")
    core = _load(root / "ontology" / "core.yaml")
    vocab = _load(root / "ontology" / "vocab.yaml")
    reg = _load(root / "anchors" / "registry.yaml")

    anchors, alias_index = {}, {}
    for a in reg["anchors"]:
        anchors[a["id"]] = a
        alias_index[a["id"].lower()] = a["id"]
        for al in a.get("aliases", []):
            alias_index[str(al).lower()] = a["id"]
        alias_index[a["id"].split(":", 1)[1].lower()] = a["id"]

    profiles = {}
    for p in sorted((root / "profiles").glob("*.yaml")):
        d = _load(p)
        profiles[d["profile"]] = Profile(
            name=d["profile"], version=d["version"], source_kind=d["source_kind"],
            source_systems=d["source_systems"], entry_group_regex=d["entry_group_regex"],
            emits=d["emits"], policy=d.get("policy") or {},
        )

    return Kit(
        root=root, ontology_version=str(types["ontology_version"]),
        anchor_types=types["anchor_types"], knowledge_types=types["knowledge_types"],
        facets=types["facets"], relations=types["relations"],
        core_fields=core["core_fields"], vocab=vocab, anchors=anchors,
        alias_index=alias_index, profiles=profiles,
    )


def parse_scope(catalog_yaml: Path) -> tuple[str, str, str]:
    """catalog.yaml `scope: entryGroup.<project>.<location>.<group>` -> (project, location, group)."""
    scope = _load(catalog_yaml).get("scope", "")
    m = re.fullmatch(r"entryGroup\.([a-z][a-z0-9-]+)\.([a-z0-9-]+)\.([a-z][a-z0-9_-]*)", str(scope))
    if not m:
        raise ValueError(f"{catalog_yaml}: scope must be entryGroup.<project>.<location>.<group>, got {scope!r}")
    return m.group(1), m.group(2), m.group(3)


def aspect_key(project: str, location: str, aspect_type: str) -> str:
    return f"{project}.{location}.{aspect_type}"
