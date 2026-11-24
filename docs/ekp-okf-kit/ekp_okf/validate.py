"""Build gate: run after a build writes its bundle, before `kcmd push`.

    python -m ekp_okf.validate <build-dir> --profile jira --build-id jira-dcs-20261124T120000Z \
        [--previous last.manifest.json] [--published published/] [--golden golden/] \
        [--write-manifest out.manifest.json] [--json report.json]

<build-dir> is a kcmd OKF workspace: catalog.yaml (scope + layout: okf) and bundle/.
Exit code 1 if any error. Every check has a code so CI output can be grepped
and individual codes waived per profile if you must.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from pathlib import Path

import yaml

from . import okf
from .emit import trust_tier
from .header import current_header, render_header, strip_header
from .kit import CORE_ASPECT, load_kit, parse_scope
from .recall import recall_at_k

ERROR, WARN = "error", "warn"


@dataclass
class Finding:
    code: str
    severity: str
    file: str
    msg: str


def _is_dt(v) -> bool:
    """OKF v0.3: date-time with offset, or a date only. A date-time without offset is invalid."""
    if isinstance(v, datetime):
        return v.tzinfo is not None
    if isinstance(v, date):
        return True
    if isinstance(v, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
        return True
    if isinstance(v, str):
        try:
            d = datetime.fromisoformat(v.replace("Z", "+00:00"))
            return d.tzinfo is not None
        except ValueError:
            return False
    return False


def _norm(v):
    """Make YAML-loaded values JSON-stable (datetimes -> ISO strings)."""
    if isinstance(v, datetime):
        return v.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if isinstance(v, date):
        return v.isoformat()
    if isinstance(v, dict):
        return {k: _norm(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_norm(x) for x in v]
    return v


class Validator:
    def __init__(self, kit, build_dir: Path, profile: str, build_id: str,
                 previous: dict | None, published: dict, golden: list, k: int, tolerance: float):
        self.kit, self.dir = kit, build_dir
        self.prof = kit.profiles[profile]
        self.build_id = build_id
        self.previous, self.published, self.golden = previous, published, golden
        self.k, self.tolerance = k, tolerance
        self.project, self.location, self.group = parse_scope(build_dir / "catalog.yaml")
        self.bundle = build_dir / "bundle"
        self.findings: list[Finding] = []
        self.concepts: dict[str, dict] = {}   # entry_id -> parsed info

    # ------------------------------------------------------------------ utils
    def add(self, code, sev, file, msg):
        self.findings.append(Finding(code, sev, file, msg))

    def core_key(self):
        return f"{self.project}.{self.location}.{CORE_ASPECT}"

    # ------------------------------------------------------------------ run
    def run(self):
        if not re.fullmatch(self.prof.entry_group_regex, self.group):
            self.add("GRP001", ERROR, "catalog.yaml",
                     f"entry group '{self.group}' does not match profile {self.prof.ref} "
                     f"pattern {self.prof.entry_group_regex} (one entry group per build)")
        for p in okf.reserved_files(self.bundle):
            self.check_reserved(p)
        for entry_id, path in okf.concept_files(self.bundle):
            self.check_concept(entry_id, path)
        self.check_build_level()
        return self

    def check_reserved(self, p: Path):
        meta, _ = okf.split(p.read_text(encoding="utf-8"))
        rel = p.relative_to(self.bundle).as_posix()
        if p.name == "index.md" and meta is not None:
            ok_keys = {"okf_version", "title", "description", "license"}
            allowed = rel == "index.md" and all(k in ok_keys or k.startswith("x-") for k in meta)
            if not allowed:
                self.add("OKF003", WARN, rel, "only the bundle-root index.md may carry frontmatter "
                         "(okf_version, title, description, license, x-* keys; OKF v0.3 §8.1)")
        if p.name == "log.md" and meta is not None:
            self.add("OKF003", WARN, rel, "log.md has no frontmatter (OKF v0.3 §9)")
        if p.name == "index.md" and rel == "index.md":
            if not meta or not meta.get("description"):
                self.add("OKF004", WARN, rel, "bundle-root index.md should declare okf_version, title and a "
                         "description: agents choosing among EKP bundles read it")

    # ------------------------------------------------------------------ concept
    def check_concept(self, entry_id: str, path: Path):
        f = path.relative_to(self.bundle).as_posix()
        text = path.read_text(encoding="utf-8")
        try:
            meta, body = okf.split(text)
        except yaml.YAMLError as e:
            self.add("OKF001", ERROR, f, f"frontmatter does not parse: {e}")
            return
        if meta is None:
            self.add("OKF001", ERROR, f, "concept file has no frontmatter block")
            return
        label = meta.get("type")
        if not label:
            self.add("OKF002", ERROR, f, "missing OKF `type`")
            return
        ctype = self.kit.type_from_label(label)
        if not ctype:
            self.add("ONT001", ERROR, f, f"type '{label}' is not in the ontology; use one of: "
                     + ", ".join(sorted(v['label'] for v in self.kit.all_types().values())))
            return
        if ctype not in self.prof.emits:
            self.add("ONT002", ERROR, f, f"profile {self.prof.ref} may not emit {ctype} "
                     f"(allowed: {', '.join(self.prof.emits)})")
            return
        is_anchor = self.kit.is_anchor_type(ctype)

        self.check_okf_fields(f, meta)
        aspects = (meta.get("extra") or {}).get("aspects") or {}
        core = self.check_aspect_keys(f, ctype, aspects)
        if core is None:
            return
        core = _norm(core)
        self.check_core(f, ctype, is_anchor, meta, core, entry_id)
        self.check_ids(f, ctype, entry_id, core, aspects)
        self.check_trust(f, ctype, meta, core)
        if is_anchor:
            self.check_registry_anchor(f, ctype, entry_id)
        else:
            self.check_anchors(f, core)
        self.check_header(f, meta, body)
        self.check_links(f, body)

        h = hashlib.sha256(json.dumps(self._hashable(meta, body), sort_keys=True, default=str)
                           .encode()).hexdigest()[:16]
        self.concepts[entry_id] = {
            "file": f, "type": ctype, "core": core, "meta": meta,
            "text": " ".join([str(meta.get("title", "")), str(meta.get("description", "")),
                              " ".join(meta.get("tags") or []), strip_header(body)]),
            "hash": h,
        }

    def _hashable(self, meta, body):
        m = _norm(json.loads(json.dumps(meta, default=str)))
        m.get("generated", {}).pop("at", None)
        for k, v in ((m.get("extra") or {}).get("aspects") or {}).items():
            if k.endswith("." + CORE_ASPECT):
                v.pop("build_id", None)
        return {"meta": m, "body": strip_header(body).strip()}

    def check_okf_fields(self, f, meta):
        for k in ("title", "description"):
            if not str(meta.get(k) or "").strip():
                self.add("FM001", ERROR, f, f"`{k}` is required by the EKP contract (search snippets and index.md use it)")
        d = str(meta.get("description") or "")
        if "\n" in d.strip() or len(d) > 300:
            self.add("FM001", WARN, f, "description should be one sentence (<300 chars)")
        g = meta.get("generated") or {}
        if not g.get("by") or not _is_dt(g.get("at")):
            self.add("FM002", ERROR, f, "`generated.by` and an ISO-8601 `generated.at` with offset are required")
        srcs = meta.get("sources") or []
        if not srcs or any(not (s or {}).get("resource") for s in srcs):
            self.add("FM003", ERROR, f, "at least one `sources` entry with `resource` is required")
        if meta.get("status", "stable") not in self.kit.vocab["lifecycle"]:
            self.add("FM004", ERROR, f, f"status '{meta.get('status')}' not in {self.kit.vocab['lifecycle']}")

    def check_aspect_keys(self, f, ctype, aspects):
        core = None
        for key, val in aspects.items():
            parts = key.split(".")
            if len(parts) != 3 or not parts[2].startswith("ekp-"):
                continue
            if f"{parts[0]}.{parts[1]}" != f"{self.project}.{self.location}":
                self.add("ASP002", ERROR, f, f"aspect key '{key}' is not in {self.project}.{self.location} "
                         "(catalog.yaml scope)")
            if parts[2] == CORE_ASPECT:
                core = val or {}
        if core is None:
            self.add("ASP001", ERROR, f, f"missing ekp-core aspect under extra.aspects['{self.core_key()}']")
            return None
        facet = self.kit.facet_of(ctype)
        wanted = f"{self.project}.{self.location}.ekp-{facet}" if facet else None
        for key in aspects:
            if key.endswith(tuple(f".ekp-{x}" for x in self.kit.facets)) and key != wanted:
                self.add("ASP004", ERROR, f, f"aspect '{key}' does not belong to type {ctype}")
        if facet:
            if wanted not in aspects:
                self.add("ASP003", ERROR, f, f"{ctype} requires facet aspect '{wanted}'")
            else:
                self.check_facet(f, facet, _norm(aspects[wanted] or {}))
        return core

    def check_facet(self, f, facet, data):
        spec = self.kit.facets[facet]
        for k in data:
            if k not in spec:
                self.add("FAC001", ERROR, f, f"ekp-{facet}: unknown field '{k}' (typo?)")
        for k, s in spec.items():
            v = data.get(k)
            if v in (None, ""):
                if s.get("required"):
                    self.add("FAC002", ERROR, f, f"ekp-{facet}.{k} is required")
                continue
            allowed = s.get("enum") or (self.kit.vocab.get(s["vocab"]) if s.get("vocab") else None)
            if allowed and v not in allowed:
                self.add("FAC003", ERROR, f, f"ekp-{facet}.{k}='{v}' not in {s.get('vocab') or 'enum'}: {allowed}")
            if s["type"] == "datetime" and not _is_dt(v):
                self.add("FAC004", ERROR, f, f"ekp-{facet}.{k} must be ISO-8601 with offset")

    def check_core(self, f, ctype, is_anchor, meta, core, entry_id):
        spec, vocab = self.kit.core_fields, self.kit.vocab
        for k in core:
            if k not in spec:
                self.add("CORE001", ERROR, f, f"ekp-core: unknown field '{k}' (typo?)")
        for k, s in spec.items():
            req = s.get("required")
            needed = req is True or (req == "knowledge" and not is_anchor)
            v = core.get(k)
            if v in (None, "", []):
                if needed:
                    self.add("CORE002", ERROR, f, f"ekp-core.{k} is required")
                continue
            t = s["type"]
            ok = {"string": isinstance(v, str), "double": isinstance(v, (int, float)),
                  "datetime": _is_dt(v), "string_array": isinstance(v, list) and all(isinstance(x, str) for x in v),
                  "relation_array": isinstance(v, list) and all(isinstance(x, dict) and {"rel", "target"} <= set(x) for x in v),
                  }[t]
            if not ok:
                self.add("CORE003", ERROR, f, f"ekp-core.{k} must be {t}")
            voc = s.get("vocab")
            if voc:
                allowed = list(vocab[voc]) if isinstance(vocab[voc], dict) else vocab[voc]
                if v not in allowed:
                    self.add("VOC001", ERROR, f, f"ekp-core.{k}='{v}' not in vocab '{voc}': {allowed}")
            pat = s.get("pattern")
            if pat and isinstance(v, str) and not re.fullmatch(vocab["patterns"][pat], v):
                self.add("VOC002", ERROR, f, f"ekp-core.{k}='{v}' does not match {vocab['patterns'][pat]}")

        sk, ss = core.get("source_kind"), core.get("source_system")
        if sk != self.prof.source_kind:
            self.add("VOC004", ERROR, f, f"source_kind '{sk}' but profile {self.prof.ref} is '{self.prof.source_kind}'")
        if ss not in self.prof.source_systems or ss not in (vocab["source_kinds"].get(sk) or []):
            self.add("VOC003", ERROR, f, f"source_system '{ss}' not allowed for {sk} / {self.prof.ref}")
        if core.get("profile") != self.prof.ref:
            self.add("VOC006", ERROR, f, f"profile '{core.get('profile')}' != {self.prof.ref}")
        if str(core.get("ontology_version")) != self.kit.ontology_version:
            self.add("VOC006", ERROR, f, f"ontology_version '{core.get('ontology_version')}' != {self.kit.ontology_version}")

        # derived fields: recomputed here, a mismatch means hand-editing or a buggy emitter
        if core.get("concept_type") != ctype:
            self.add("DER001", ERROR, f, f"concept_type '{core.get('concept_type')}' but OKF type maps to {ctype}")
        status = meta.get("status", "stable")
        if core.get("lifecycle") != status:
            self.add("DER002", ERROR, f, f"lifecycle '{core.get('lifecycle')}' != OKF status '{status}'")
        tt = trust_tier(meta.get("verified"), (meta.get("generated") or {}).get("at"))
        if core.get("trust_tier") != tt:
            self.add("DER003", ERROR, f, f"trust_tier '{core.get('trust_tier')}' but current `verified` events "
                     f"(at >= generated.at, OKF v0.3 §5.3) give '{tt}'")
        want_id = f"{self.group}:{entry_id}"
        if core.get("concept_id") != want_id:
            self.add("DER004", ERROR, f, f"concept_id '{core.get('concept_id')}' != '{want_id}'")

        if status == "deprecated" and not core.get("valid_to"):
            self.add("LIF002", ERROR, f, "deprecated concept needs ekp-core.valid_to (closes its temporal interval)")
        if status != "deprecated" and core.get("valid_to"):
            self.add("LIF002", ERROR, f, "valid_to is set but the concept is not deprecated")
        sup = meta.get("superseded_by")
        if sup is not None:
            if status != "deprecated":
                self.add("LIF005", ERROR, f, "superseded_by only has meaning with status: deprecated (OKF v0.3 §5.4)")
            elif not re.match(r"^[a-z]+:", str(sup)) and not self._resolve(f, str(sup)):
                self.add("LIF005", ERROR, f, f"superseded_by '{sup}' does not resolve to a concept in this bundle")

    def check_ids(self, f, ctype, entry_id, core, aspects):
        rule = self.prof.emits[ctype]
        pm = re.fullmatch(rule["path_regex"], entry_id)
        if not pm:
            self.add("ID001", ERROR, f, f"entry ID '{entry_id}' does not match {rule['path_regex']} "
                     "(IDs derive from source identity, never from titles)")
        sm = re.fullmatch(rule["source_ref_regex"], str(core.get("source_ref", "")))
        if not sm:
            self.add("ID002", ERROR, f, f"source_ref '{core.get('source_ref')}' does not match {rule['source_ref_regex']}")
        if pm and sm:
            for g in set(pm.groupdict()) & set(sm.groupdict()):
                if pm.group(g) != sm.group(g):
                    self.add("ID003", ERROR, f, f"path {g}='{pm.group(g)}' but source_ref {g}='{sm.group(g)}'")
            facet = self.kit.facet_of(ctype)
            fdata = _norm((aspects.get(f"{self.project}.{self.location}.ekp-{facet}") or {})) if facet else {}
            for g, target in (rule.get("agree") or {}).items():
                scope, field = target.split(".", 1)
                val = (fdata if scope == "facet" else core).get(field)
                if pm.group(g) != val:
                    self.add("ID004", ERROR, f, f"path {g}='{pm.group(g)}' disagrees with {target}='{val}'")
        ext = core.get("extraction")
        if ext and ext not in rule.get("extraction", []):
            self.add("TRU005", ERROR, f, f"extraction '{ext}' not allowed for {ctype} in {self.prof.ref} "
                     f"(allowed: {rule.get('extraction')})")

    def check_trust(self, f, ctype, meta, core):
        status = meta.get("status", "stable")
        ev = meta.get("verified")
        for e in (ev if isinstance(ev, list) else ([ev] if ev else [])):
            if not (isinstance(e, dict) and e.get("by") and _is_dt(e.get("at"))):
                self.add("TRU006", ERROR, f, f"verified event needs both `by` and a valid `at`: {e}")
        minc = (self.prof.policy or {}).get("min_confidence")
        if core.get("extraction") == "llm":
            c = core.get("confidence")
            if not isinstance(c, (int, float)):
                self.add("TRU002", ERROR, f, "llm extraction needs ekp-core.confidence")
            elif minc is not None and c < minc and ctype != "Unclassified":
                self.add("TRU002", ERROR, f, f"confidence {c} < profile minimum {minc}: emit as Unclassified (draft) instead")
            if core.get("trust_tier") == "unverified" and status not in ("draft", "deprecated"):
                self.add("TRU003", ERROR, f, "unverified llm-extracted concept must be status: draft until verified")
        if ctype == "Unclassified" and status != "draft":
            self.add("TRU004", ERROR, f, "Unclassified concepts must be status: draft")

    def check_anchors(self, f, core):
        anchors = core.get("anchors") or []
        if not anchors:
            self.add("ANC002", ERROR, f, "knowledge concepts must resolve at least one anchor")
        for a in anchors:
            if a in self.kit.anchors:
                continue
            canon = self.kit.alias_index.get(str(a).lower())
            if canon:
                self.add("ANC001", ERROR, f, f"anchor '{a}' is an alias; use canonical '{canon}'")
            else:
                self.add("ANC001", ERROR, f, f"anchor '{a}' is not in the registry (send it to the registry review queue)")
        for field, kind in (("primary_system", "system"), ("primary_component", "component"),
                            ("primary_capability", "capability")):
            v = core.get(field)
            if not v:
                continue
            if v not in anchors:
                self.add("ANC003", ERROR, f, f"{field} '{v}' must also appear in anchors")
            if not str(v).startswith(kind + ":"):
                self.add("ANC003", ERROR, f, f"{field} '{v}' must be a {kind}: anchor")
        ps = self.kit.anchors.get(core.get("primary_system") or "")
        if ps and ps.get("domain") and f"domain:{core.get('domain')}" != ps["domain"]:
            self.add("ANC004", ERROR, f, f"domain '{core.get('domain')}' but {ps['id']} belongs to {ps['domain']}")
        pc = self.kit.anchors.get(core.get("primary_component") or "")
        if pc and pc.get("system") and core.get("primary_system") and pc["system"] != core["primary_system"]:
            self.add("ANC004", ERROR, f, f"{pc['id']} belongs to {pc['system']}, not {core['primary_system']}")

    def check_registry_anchor(self, f, ctype, entry_id):
        prefix = self.kit.anchor_types[ctype]["prefix"]
        aid = f"{prefix}:{entry_id.rsplit('/', 1)[-1]}"
        if aid not in self.kit.anchors:
            self.add("ANC005", ERROR, f, f"anchor concept {aid} is not in anchors/registry.yaml")

    def check_header(self, f, meta, body):
        cur = current_header(body)
        want = render_header(_norm(json.loads(json.dumps(meta, default=str))), self.kit)
        if cur is None:
            self.add("HDR001", ERROR, f, "reader header missing (run: python -m ekp_okf.header --fix <build-dir>)")
        elif cur != want.strip():
            self.add("HDR001", ERROR, f, "reader header out of sync with frontmatter (run header --fix)")

    def _resolve(self, f, target) -> bool:
        """OKF v0.3 §6: '/x' from the bundle root, anything else from the file's directory."""
        base = self.bundle if target.startswith("/") else (self.bundle / f).parent
        t = (base / target.lstrip("/")).resolve()
        try:
            t.relative_to(self.bundle.resolve())
        except ValueError:
            return False
        return t.is_file() or Path(str(t) + ".md").is_file()

    def check_links(self, f, body):
        for target in re.findall(r"\]\(([^)#\s]+)", body):
            if re.match(r"^[a-z][a-z0-9+.-]*:", target):
                continue                      # absolute URL
            if not self._resolve(f, target):
                self.add("LNK001", WARN, f, f"bundle link {target} does not resolve")

    # ------------------------------------------------------------------ build level
    def check_build_level(self):
        # build_id: emitted by this build, or carried over byte-for-byte unchanged
        # (an agent may re-emit only the concepts it touched in a checked-out bundle)
        prev_concepts = (self.previous or {}).get("concepts", {})
        for eid, c in self.concepts.items():
            bid = c["core"].get("build_id")
            if bid != self.build_id:
                pc = prev_concepts.get(eid)
                if not (pc and pc.get("hash") == c["hash"]):
                    self.add("VOC005", ERROR, c["file"], f"build_id '{bid}' is not this build ('{self.build_id}') "
                             "and the concept is not an unchanged carry-over from the previous manifest")
        by_ref = {}
        for eid, c in self.concepts.items():
            ref = c["core"].get("source_ref")
            if ref in by_ref:
                self.add("ID005", ERROR, c["file"], f"source_ref '{ref}' also claimed by {by_ref[ref]}")
            by_ref[ref] = c["file"]

        self.check_relations()

        if self.previous:
            prev = self.previous.get("concepts", {})
            for eid, pc in prev.items():
                if eid not in self.concepts:
                    self.add("LIF001", ERROR, f"{eid}.md",
                             f"concept vanished since build {self.previous.get('build_id')}: kcmd push would DELETE "
                             "its entry. Keep the file with status: deprecated, valid_to, and superseded_by if "
                             "it moved or was replaced.")
                    continue
                cur = self.concepts[eid]
                if (pc.get("trust_tier") == "human_reviewed"
                        and cur["core"].get("trust_tier") != "human_reviewed"):
                    self.add("TRU007", WARN, cur["file"], "was human_reviewed; content changed since the review, "
                             "so the review is no longer current (OKF v0.3 §5.3). Route to the owner for re-review.")
                if pc.get("source_ref") != cur["core"].get("source_ref"):
                    self.add("LIF003", ERROR, cur["file"], f"entry ID reused for a different source_ref "
                             f"('{pc.get('source_ref')}' -> '{cur['core'].get('source_ref')}')")
                elif (pc.get("hash") != cur["hash"]
                      and pc.get("source_revision") == cur["core"].get("source_revision")):
                    self.add("LIF004", WARN, cur["file"], "content changed but source_revision did not: "
                             "non-deterministic emitter?")

        self.recall = None
        if self.golden:
            docs = {c["core"]["concept_id"]: c["text"] for c in self.concepts.values()
                    if c["core"].get("lifecycle") != "deprecated"}
            self.recall = recall_at_k(docs, self.golden, self.k)
            prev_score = ((self.previous or {}).get("recall") or {}).get("score")
            if self.recall["score"] is not None:
                for row in self.recall["detail"]:
                    if row["recall"] < 1.0:
                        self.add("RCL002", WARN, "golden", f"recall@{self.k}={row['recall']:.2f} for: {row['q']}")
                if prev_score is not None and self.recall["score"] < prev_score - self.tolerance:
                    self.add("RCL001", ERROR, "golden", f"recall@{self.k} dropped {prev_score:.2f} -> "
                             f"{self.recall['score']:.2f} (tolerance {self.tolerance})")

    def check_relations(self):
        local = {c["core"]["concept_id"]: c for c in self.concepts.values()}
        for c in self.concepts.values():
            src_t = c["type"]
            for r in c["core"].get("relations") or []:
                rel, tgt = r.get("rel"), str(r.get("target"))
                spec = self.kit.relations.get(rel)
                if not spec:
                    self.add("REL001", ERROR, c["file"], f"unknown relation '{rel}' (known: {', '.join(self.kit.relations)})")
                    continue
                if src_t not in spec["from"]:
                    self.add("REL002", ERROR, c["file"], f"{src_t} cannot be the source of '{rel}' (allowed: {spec['from']})")
                if tgt.split(":", 1)[0] in {a["prefix"] for a in self.kit.anchor_types.values()}:
                    self.add("REL007", ERROR, c["file"], f"relation target '{tgt}' is an anchor; anchors go in `anchors`")
                    continue
                allowed_to = [src_t] if spec["to"] == "same" else spec["to"]
                if tgt.startswith(self.group + ":"):
                    if tgt not in local:
                        self.add("REL003", ERROR, c["file"], f"'{rel}' target {tgt} is not in this build")
                        continue
                    tt, tl = local[tgt]["type"], local[tgt]["core"].get("lifecycle")
                else:
                    g = self.published.get(tgt)
                    if not g:
                        self.add("REL005", WARN, c["file"], f"'{rel}' target {tgt} not found in published manifests "
                                 "(other build not run yet, or a typo)")
                        continue
                    tt, tl = g["type"], g.get("lifecycle")
                if tt not in allowed_to:
                    self.add("REL004", ERROR, c["file"], f"'{rel}' cannot target a {tt} (allowed: {allowed_to})")
                if tl == "deprecated":
                    self.add("REL006", WARN, c["file"], f"'{rel}' target {tgt} is deprecated")

    # ------------------------------------------------------------------ outputs
    def manifest(self) -> dict:
        return {
            "entry_group": self.group, "project": self.project, "location": self.location,
            "profile": self.prof.ref, "build_id": self.build_id,
            "ontology_version": self.kit.ontology_version,
            "concepts": {eid: {"concept_id": c["core"].get("concept_id"), "type": c["type"],
                               "lifecycle": c["core"].get("lifecycle"),
                               "trust_tier": c["core"].get("trust_tier"),
                               "source_ref": c["core"].get("source_ref"),
                               "source_revision": c["core"].get("source_revision"),
                               "hash": c["hash"]}
                         for eid, c in sorted(self.concepts.items())},
            "recall": ({k: v for k, v in self.recall.items() if k != "detail"} if self.recall else None),
        }

    def errors(self):
        return [x for x in self.findings if x.severity == ERROR]


def load_published(d: Path | None) -> dict:
    out = {}
    if d and d.exists():
        for p in sorted(d.glob("*.manifest.json")):
            m = json.loads(p.read_text())
            for c in m.get("concepts", {}).values():
                out[c["concept_id"]] = c
    return out


def load_golden(d: Path | None) -> list:
    qs = []
    if d and d.exists():
        for p in sorted(d.glob("*.yaml")):
            qs.extend((yaml.safe_load(p.read_text()) or {}).get("questions", []))
    return qs


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("build_dir", type=Path)
    ap.add_argument("--profile", required=True)
    ap.add_argument("--build-id", required=True)
    ap.add_argument("--previous", type=Path, help="this build's last published manifest")
    ap.add_argument("--published", type=Path, help="dir of *.manifest.json from all builds (global index)")
    ap.add_argument("--golden", type=Path, help="dir of golden question YAML files")
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--recall-tolerance", type=float, default=0.05)
    ap.add_argument("--write-manifest", type=Path)
    ap.add_argument("--json", type=Path, help="write findings as JSON")
    a = ap.parse_args(argv)

    kit = load_kit()
    prev = json.loads(a.previous.read_text()) if a.previous and a.previous.exists() else None
    v = Validator(kit, a.build_dir, a.profile, a.build_id, prev, load_published(a.published),
                  load_golden(a.golden), a.k, a.recall_tolerance).run()

    by_file = {}
    for x in v.findings:
        by_file.setdefault(x.file, []).append(x)
    print(f"build {a.build_id}  profile {v.prof.ref}  entry group {v.group}  concepts {len(v.concepts)}")
    for file in sorted(by_file):
        print(f"  {file}")
        for x in by_file[file]:
            print(f"    {x.severity.upper():5} {x.code}  {x.msg}")
    if v.recall and v.recall["score"] is not None:
        print(f"  golden recall@{v.recall['k']}: {v.recall['score']:.2f} over {v.recall['questions']} question(s)")
    errs = len(v.errors())
    print(f"  => {'FAIL' if errs else 'PASS'}: {errs} error(s), {len(v.findings) - errs} warning(s)")

    if a.json:
        a.json.write_text(json.dumps([asdict(x) for x in v.findings], indent=2))
    if a.write_manifest and not errs:
        a.write_manifest.parent.mkdir(parents=True, exist_ok=True)
        a.write_manifest.write_text(json.dumps(v.manifest(), indent=2))
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
