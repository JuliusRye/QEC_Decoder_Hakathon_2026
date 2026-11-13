"""Check project documentation links and frozen-source hashes without network access."""

from hashlib import sha256
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
errors = []
sources = ROOT / "docs/sources"
manifest = json.loads((sources / "sha256.json").read_text())
for name, expected in manifest.items():
    path = sources / name
    if not path.is_file() or sha256(path.read_bytes()).hexdigest() != expected:
        errors.append(f"Source hash mismatch: {name}")
# Frozen third-party pages retain their original relative links, with a source URL.
paths = [ROOT / p for p in ("README.md", "AGENTS.md", "CONTRIBUTING.md")]
paths += [p for p in (ROOT / "docs").rglob("*.md") if sources not in p.parents]
for path in paths:
    for target in re.findall(r"\]\(([^)]+)\)", path.read_text()):
        if "://" in target or target.startswith("#"):
            continue
        target = target.split("#")[0]
        if target and not (path.parent / target).exists():
            errors.append(f"Broken local link: {path.relative_to(ROOT)} -> {target}")
if errors:
    print("\n".join(errors), file=sys.stderr)
    raise SystemExit(1)
print(f"Context checks passed: {len(paths)} documents, {len(manifest)} source hashes.")
