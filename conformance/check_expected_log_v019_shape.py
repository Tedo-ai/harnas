#!/usr/bin/env python3
"""Verify that agent expected logs use the v0.19 event artifact shape."""

from __future__ import annotations

import json
import pathlib
import sys
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parent
AGENTS = ROOT / "agents"
USAGE_KEYS = {
    "input_tokens",
    "output_tokens",
    "total_tokens",
    "cache_read_input_tokens",
    "cache_write_input_tokens",
    "reasoning_tokens",
    "provider_raw",
    "provenance",
}


def main() -> int:
    failures: list[str] = []

    for expected_path in sorted(AGENTS.glob("*/expected-log.jsonl")):
        for line_number, event in enumerate(read_jsonl(expected_path), start=1):
            rel = expected_path.relative_to(ROOT)
            if "timestamp" not in event:
                failures.append(f"{rel}:{line_number}: missing timestamp")

            payload = event.get("payload")
            if not isinstance(payload, dict) or event.get("type") != "assistant_message":
                continue

            usage = payload.get("usage")
            if isinstance(usage, dict) and set(usage) != USAGE_KEYS:
                failures.append(f"{rel}:{line_number}: assistant usage is not v0.19 canonical shape")
            if "provider" not in payload:
                failures.append(f"{rel}:{line_number}: assistant message missing provider")
            if "model" not in payload:
                failures.append(f"{rel}:{line_number}: assistant message missing model")

    if failures:
        print(f"expected-log v0.19 shape: {len(failures)} violations")
        for failure in failures:
            print(failure)
        return 1

    print("expected-log v0.19 shape: ok")
    return 0


def read_jsonl(path: pathlib.Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


if __name__ == "__main__":
    sys.exit(main())
