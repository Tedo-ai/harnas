#!/usr/bin/env python3
"""Verify that provider-call fixture turns assert their projected request."""

from __future__ import annotations

import json
import pathlib
import sys
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parent
AGENTS = ROOT / "agents"


def main() -> int:
    missing: list[str] = []
    total = 0
    covered = 0

    for fixture in sorted(path for path in AGENTS.iterdir() if path.is_dir()):
        for script_name in ("provider-script.json", "provider-script-stream.json"):
            script_path = fixture / script_name
            if not script_path.exists():
                continue
            turns = json.loads(script_path.read_text(encoding="utf-8"))
            for index, turn in enumerate(turns):
                total += 1
                if has_expect_request(turn):
                    covered += 1
                else:
                    missing.append(f"{fixture.name}/{script_name}[{index}]")

    if missing:
        print(
            f"expect_request coverage: {covered}/{total} provider turns covered; "
            f"{len(missing)} missing"
        )
        for item in missing:
            print(f"missing {item}")
        return 1

    print(f"expect_request coverage: {covered}/{total} provider turns covered")
    return 0


def has_expect_request(turn: Any) -> bool:
    return isinstance(turn, dict) and "expect_request" in turn


if __name__ == "__main__":
    sys.exit(main())
