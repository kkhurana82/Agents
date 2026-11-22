import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

ADOC_JS = Path("/home/claude/tools/adoc/node_modules/.bin/asciidoctor")


@pytest.fixture
def root():
    return ROOT


def asciidoctor_bin():
    """Optional render check: Ruby asciidoctor or Asciidoctor.js (npm i asciidoctor). Set ASCIIDOCTOR to override."""
    if os.environ.get("ASCIIDOCTOR"):
        return os.environ["ASCIIDOCTOR"]
    if shutil.which("asciidoctor"):
        return shutil.which("asciidoctor")
    return str(ADOC_JS) if ADOC_JS.exists() else None


def render_adoc(path: Path) -> subprocess.CompletedProcess:
    """Render with Asciidoctor, failing on warnings (broken xrefs, unterminated blocks, bad levels)."""
    return subprocess.run([asciidoctor_bin(), "--failure-level", "WARN", "-o", "/dev/null", str(path)],
                          capture_output=True, text=True)
