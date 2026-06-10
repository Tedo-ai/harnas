#!/usr/bin/env python3
"""Check current public docs against the spec VERSION and fixture corpus."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def fail(message: str) -> None:
    print(f"drift check failed: {message}", file=sys.stderr)
    raise SystemExit(1)


def version_fields() -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in (ROOT / "VERSION").read_text(encoding="utf-8").splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip()
    return fields


def fixture_count() -> int:
    agents = ROOT / "conformance" / "agents"
    return sum(1 for path in agents.iterdir() if path.is_dir() and (path / "manifest.json").exists())


def require_contains(path: Path, needle: str) -> None:
    text = path.read_text(encoding="utf-8")
    if needle not in text:
        fail(f"{path.relative_to(ROOT)} does not contain {needle!r}")


def require_absent(path: Path, patterns: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    for pattern in patterns:
        if re.search(pattern, text):
            fail(f"{path.relative_to(ROOT)} contains stale pattern {pattern!r}")


def main() -> None:
    fields = version_fields()
    spec_version = fields.get("harnas_version") or fail("VERSION has no harnas_version")
    fixtures_version = fields.get("fixtures_version") or fail("VERSION has no fixtures_version")
    count = fixture_count()

    readme = ROOT / "README.md"
    require_contains(readme, f"Version {spec_version}")
    for language in ("Ruby", "Python", "Go", "TypeScript"):
        require_contains(readme, f"| {language}")
    require_contains(readme, f"{count}/{count} agent conformance fixtures")
    require_contains(readme, "Ruby, Python, Go, and TypeScript")
    require_contains(readme, "Disclosed v1.0 footnotes")

    stale_patterns = [
        r"\b71/71\b",
        r"\b70/70\b",
        r"\b65-fixture\b",
        r"\b70-fixture\b",
        r"\b0\.19\.3\b",
        r"TS \(in dev\)",
        r"harnas-typescript \(in development\)",
        r"TypeScript implementation is in development",
        r"and \(soon\)\s+TypeScript",
        r"Ruby, Python, Go, and TypeScript\s+implementations are the existence proof",
        r"4 impls, same fixtures",
        r"Ruby, Python, and Go\s+implementations are the current fully conforming reference set",
        r"fixture-aware implementations for MarkerTail",
        r"fixture-aware shims",
    ]
    for relative in (
        "README.md",
        "docs/roadmap.md",
        "docs/comparison.md",
        "docs/ecosystem.md",
        "docs/philosophy.md",
    ):
        require_absent(ROOT / relative, stale_patterns)

    print(f"drift ok: spec {spec_version}, fixtures v{fixtures_version}, {count} agent fixtures")


if __name__ == "__main__":
    main()
