"""Generate Knowledge Catalog aspect-type templates from the ontology, so the
catalog schema and the build gate can never drift apart.

    python catalog/gen_aspects.py            # writes catalog/generated/*.json

Then register them once per project/location with catalog/setup_aspects.sh.

Template rules (same as Google's okf-aspect.json):
  * Field `index` values are append-only. Dataplex rejects backwards-incompatible
    template changes, so never renumber or retype a published field; add new
    fields at the end. This script keeps indexes stable by reading the
    previously generated file and appending new fields only.
  * Vocab/enums are enforced by the build gate, not as Dataplex enum types, so
    a new domain or enum value never needs a template change.
  * Catalog-side `required` is only set for core fields that are required for
    every concept, anchors included.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ekp_okf.kit import load_kit  # noqa: E402

OUT = Path(__file__).resolve().parent / "generated"
TYPE_MAP = {"string": "string", "double": "double", "datetime": "datetime", "int": "int", "bool": "bool"}


def field(index, name, spec):
    ann = {"displayName": name.replace("_", " ").title(), "description": spec.get("doc", name)}
    if spec.get("filter"):
        ann["search"] = {"retrievable": True}   # mirrors Google's okf template for filterable scalars
    t = spec["type"]
    if t == "string_array":
        f = {"index": index, "name": name, "type": "array", "arrayItems": {"name": "item", "type": "string"}}
    elif t == "relation_array":
        f = {"index": index, "name": name, "type": "array", "arrayItems": {
            "name": "relation", "type": "record", "recordFields": [
                {"index": 1, "name": "rel", "type": "string", "constraints": {"required": True},
                 "annotations": {"displayName": "Relation", "description": "Relation kind from ontology/types.yaml"}},
                {"index": 2, "name": "target", "type": "string", "constraints": {"required": True},
                 "annotations": {"displayName": "Target", "description": "Target concept_id"}},
            ]}}
    else:
        f = {"index": index, "name": name, "type": TYPE_MAP[t]}
    if spec.get("required") is True:
        f["constraints"] = {"required": True}
    f["annotations"] = ann
    return f


def build(name, display, description, fields: dict):
    prev_path = OUT / f"{name}.json"
    prev = {}
    if prev_path.exists():
        for f in json.loads(prev_path.read_text())["recordFields"]:
            prev[f["name"]] = f["index"]
    next_index = max(prev.values(), default=0) + 1
    out = []
    for fname, spec in fields.items():
        if fname in prev:
            idx = prev[fname]
        else:
            idx, next_index = next_index, next_index + 1
        out.append(field(idx, fname, spec))
    removed = set(prev) - set(fields)
    if removed:
        raise SystemExit(f"{name}: fields {sorted(removed)} were removed; that is a breaking catalog change. "
                         "Keep them (unused) or create a new aspect type.")
    out.sort(key=lambda f: f["index"])
    return {"name": name, "type": "record", "recordFields": out,
            "annotations": {"displayName": display, "description": description}}


def main():
    kit = load_kit()
    OUT.mkdir(exist_ok=True)
    docs = {"ekp-core": build("ekp-core", "EKP Core",
                                  f"Uniform filter surface for every EKP concept (ontology {kit.ontology_version}).",
                                  kit.core_fields)}
    for facet, spec in kit.facets.items():
        fields = {k: {**v, "filter": True, "required": False} for k, v in spec.items()}
        docs[f"ekp-{facet}"] = build(f"ekp-{facet}", f"EKP {facet.title()}",
                                         f"Filterable fields for {facet} concepts.", fields)
    for name, doc in docs.items():
        (OUT / f"{name}.json").write_text(json.dumps(doc, indent=2) + "\n")
        print(f"wrote catalog/generated/{name}.json ({len(doc['recordFields'])} fields)")


if __name__ == "__main__":
    main()
