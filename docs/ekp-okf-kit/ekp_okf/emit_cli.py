"""Write concept specs to an EKP OKF build workspace.

    python -m ekp_okf.emit_cli specs.yaml --build-dir build/ --profile wiki \
        --build-id wiki-dcsops-20261125T010000Z [--previous last-bundle/] \
        [--bundle-title ... --bundle-description ...] [--validate]

The build dir must already hold catalog.yaml (scope + layout: okf). Existing
concept files that are not in the specs are left alone, so an agent can add or
fix a few concepts in a checked-out bundle. --validate runs the build gate.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from .emit import emit_concept, write_index
from .kit import load_kit, parse_scope


def emit_specs(kit, build_dir: Path, profile: str, build_id: str, specs: list,
               previous: Path | None = None) -> list[Path]:
    project, location, group = parse_scope(build_dir / "catalog.yaml")
    out = []
    for s in specs:
        core = {**s["core"], "build_id": build_id}
        out.append(emit_concept(
            kit, build_dir, project=project, location=location, entry_group=group, profile=profile,
            entry_id=s["entry_id"], ctype=s["type"], title=s["title"], description=s["description"],
            body=s["body"], core=core, facet=s.get("facet"), sources=s["sources"],
            generated=s["generated"], verified=s.get("verified"), status=s.get("status", "stable"),
            tags=s.get("tags"), resource=s.get("resource"), superseded_by=s.get("superseded_by"),
            previous_bundle=previous))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("specs", type=Path)
    ap.add_argument("--build-dir", type=Path, required=True)
    ap.add_argument("--profile", required=True)
    ap.add_argument("--build-id", required=True)
    ap.add_argument("--previous", type=Path, help="last published bundle dir, for carry-forward")
    ap.add_argument("--bundle-title")
    ap.add_argument("--bundle-description")
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--published", type=Path)
    ap.add_argument("--previous-manifest", type=Path)
    a = ap.parse_args(argv)

    kit = load_kit()
    text = a.specs.read_text()
    specs = json.loads(text) if a.specs.suffix == ".json" else yaml.safe_load(text)
    specs = specs if isinstance(specs, list) else specs.get("concepts", [])
    for p in emit_specs(kit, a.build_dir, a.profile, a.build_id, specs, a.previous):
        print(f"wrote {p}")
    if a.bundle_title and a.bundle_description:
        write_index(a.build_dir, a.bundle_title, a.bundle_description)
    if a.validate:
        from .validate import main as gate
        args = [str(a.build_dir), "--profile", a.profile, "--build-id", a.build_id]
        if a.published:
            args += ["--published", str(a.published)]
        if a.previous_manifest:
            args += ["--previous", str(a.previous_manifest)]
        return gate(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
