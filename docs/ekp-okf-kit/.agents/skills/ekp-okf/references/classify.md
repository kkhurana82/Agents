# Classify one source document into an EKP concept

This file is used twice: by an agent session (Antigravity, Claude Code, Codex)
following the ekp-okf skill, and verbatim as the prompt template of the
pipeline's LLM lane (`pipeline/llm_lane.py`). Placeholders in `{braces}` are
filled by the lane.

---

You classify one source document for the EKP knowledge platform. Code has
already decided the document's identity (source reference, entry ID template,
system and owner). You decide only what the document means.

Return JSON that matches the schema you were given. Rules:

1. `type`: one of the allowed types below. Choose `Unclassified` when the
   document does not clearly fit one type, or when it mixes several.
2. `title`: what the concept is, in plain words. Not the page title if that
   title is vague.
3. `description`: one sentence a search snippet can show.
4. `body`: Markdown. Keep only what the document states. Use the conventional
   headings for the type (`# Steps` for a Procedure, `# Decision` /
   `# Context` / `# Consequences` for a Decision, `# Design` for a Design).
   Do not add advice, owners, dates or numbers the document does not contain.
5. `anchors`: canonical IDs from the anchor list below, for every system,
   component, capability and term the document is clearly about. Match aliases
   to their canonical ID. Never output an alias.
6. `primary_component` / `primary_capability`: the main one, or "" if none.
7. `facet`: only fields that belong to the chosen type.
8. `confidence`: your confidence in the type and anchors, 0 to 1. Be honest;
   below {min_confidence} the concept is quarantined as Unclassified, which is
   the correct outcome for an unclear document.
9. `unresolved_terms`: names that look like systems or components but match
   no anchor. Do not guess an anchor for them.

## Profile classification rules

{profile_rules}

## Allowed types

{types}

## Anchors (canonical ID: title; aliases)

{anchors}

## Document

{document}
