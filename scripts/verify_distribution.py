#!/usr/bin/env python3
"""Static checks for the authored Hermes Profile Distribution."""
from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = ["distribution.yaml", "SOUL.md", "config.yaml", "mcp.json", "skills/sauron-recon/SKILL.md", "knowledge/00-index.md"]
FORBIDDEN = re.compile(r"(?:sk-[A-Za-z0-9]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|-----BEGIN (?:RSA|OPENSSH|EC) PRIVATE KEY-----)")


def main() -> int:
    missing = [path for path in REQUIRED if not (ROOT / path).is_file()]
    if missing:
        raise SystemExit(f"missing distribution files: {missing}")
    manifest = yaml.safe_load((ROOT / "distribution.yaml").read_text())
    if manifest.get("name") != "sauron-recon" or not manifest.get("version"):
        raise SystemExit("invalid distribution manifest")
    json.loads((ROOT / "mcp.json").read_text())
    empty = [str(path.relative_to(ROOT)) for path in ROOT.glob("**/*") if path.is_file() and path.stat().st_size == 0]
    if empty:
        raise SystemExit(f"empty files: {empty}")
    scanned = [ROOT / path for path in REQUIRED] + [ROOT / "README.md", ROOT / "PLAN.md"]
    leaks = [str(path.relative_to(ROOT)) for path in scanned if FORBIDDEN.search(path.read_text(errors="replace"))]
    if leaks:
        raise SystemExit(f"possible secret patterns: {leaks}")
    print(f"distribution verification passed: {len(REQUIRED)} required files, YAML/JSON parsed, no empty required files or obvious secret patterns")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
