"""Concept specs: the one input format shared by every producer.

An Antigravity session, a deterministic adapter and the pipeline's LLM lane all
produce the same thing, a list of concept specs, and emit_cli turns specs into
OKF files. Nobody hand-writes frontmatter.

Spec shape (YAML or JSON), one entry per concept:

    - entry_id: procedures/DCSOPS/48219911
      type: Procedure                      # ontology type name (not the label)
      title: ...
      description: ...                     # one sentence
      body: |                              # markdown, with [^id] footnotes
        ...
      tags: [...]
      status: draft                        # draft | stable | deprecated
      superseded_by: null
      core: {domain, primary_system, primary_component, primary_capability,
             source_system, source_ref, source_revision, source_url, extraction,
             confidence, valid_from, valid_to, owner_team, anchors, relations}
      facet: {...}                         # per-type facet fields, if the type has one
      sources: [{id, resource, title, author, last_modified}]
      generated: {by, at}
      verified: [{by, at}]                 # only events that really happened

`model_schema()` gives the JSON Schema for the part a model may decide, built from
the ontology, the profile and the registry. Used as structured output for Gemini
(`response_json_schema`) or `agy -p --json-schema`, it makes unknown types,
alias anchors and invalid enum values impossible to generate.
"""
from __future__ import annotations

from .kit import Kit


def model_schema(kit: Kit, profile: str) -> dict:
    prof = kit.profiles[profile]
    types = [t for t in prof.emits if not kit.is_anchor_type(t)]
    anchors = sorted(kit.anchors)
    facet_props: dict = {}
    for t in types:
        f = kit.facet_of(t)
        for name, spec in (kit.facets.get(f) or {}).items():
            allowed = spec.get("enum") or (kit.vocab.get(spec["vocab"]) if spec.get("vocab") else None)
            facet_props[name] = {"type": "string", **({"enum": list(allowed)} if allowed else {})}
    return {
        "type": "object",
        "properties": {
            "type": {"type": "string", "enum": types,
                     "description": "Ontology type. Use Unclassified when unsure."},
            "title": {"type": "string"},
            "description": {"type": "string", "description": "One sentence."},
            "body": {"type": "string", "description": "Markdown body. Only facts the source states."},
            "tags": {"type": "array", "items": {"type": "string"}},
            "anchors": {"type": "array", "items": {"type": "string", "enum": anchors},
                        "description": "Canonical anchor IDs only."},
            "primary_component": {"type": "string", "enum": [""] + [a for a in anchors if a.startswith("component:")]},
            "primary_capability": {"type": "string", "enum": [""] + [a for a in anchors if a.startswith("capability:")]},
            "facet": {"type": "object", "properties": facet_props},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1,
                           "description": "Confidence in the type and anchors."},
            "unresolved_terms": {"type": "array", "items": {"type": "string"},
                                 "description": "Names that look like systems/components but match no anchor."},
        },
        "required": ["type", "title", "description", "body", "anchors", "confidence"],
    }


def path_for(kit: Kit, profile: str, ctype: str, **ids) -> str:
    """Entry ID from the profile's path template: code computes IDs, models never do."""
    tmpl = kit.profiles[profile].emits[ctype].get("path")
    if not tmpl:
        raise ValueError(f"profile {profile} has no path template for {ctype}")
    return tmpl.format(**ids)
