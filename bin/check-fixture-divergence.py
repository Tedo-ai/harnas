#!/usr/bin/env python3
"""Run changed fixture corpora against all reference implementations.

This is a fixture-sanity gate, not a replacement for per-implementation
conformance. A newly changed fixture is trusted only after Go, Ruby, Python,
and TypeScript all agree with the same strict corpus artifacts.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IMPLEMENTATIONS = ("go", "ruby", "python", "typescript")


@dataclass(frozen=True)
class CommandResult:
    impl: str
    label: str
    cmd: list[str]
    cwd: Path
    returncode: int
    stdout: str
    stderr: str

    @property
    def passed(self) -> bool:
        return self.returncode == 0

    @property
    def bucket(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        digest = hashlib.sha256((self.stdout + "\n" + self.stderr).encode("utf-8")).hexdigest()[:12]
        return f"{status}:{digest}"


@dataclass
class ChangedCorpora:
    agent_fixtures: set[str]
    provider_carriers: bool = False
    oracle_corpus: bool = False
    storage_laws: bool = False

    def empty(self) -> bool:
        return (
            not self.agent_fixtures
            and not self.provider_carriers
            and not self.oracle_corpus
            and not self.storage_laws
        )


def run(cmd: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> CommandResult:
    impl = env.pop("_HARNAS_IMPL") if env and "_HARNAS_IMPL" in env else "spec"
    label = env.pop("_HARNAS_LABEL") if env and "_HARNAS_LABEL" in env else "check"
    proc = subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return CommandResult(
        impl=impl,
        label=label,
        cmd=cmd,
        cwd=cwd,
        returncode=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
    )


def git_lines(args: list[str], *, cwd: Path) -> list[str]:
    proc = subprocess.run(
        ["git", *args],
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"git {' '.join(args)} failed")
    return [line for line in proc.stdout.splitlines() if line.strip()]


def working_tree_paths(spec_root: Path) -> list[str]:
    paths: list[str] = []
    for line in git_lines(["status", "--porcelain", "--untracked-files=all"], cwd=spec_root):
        if len(line) < 4:
            continue
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        paths.append(path)
    return paths


def changed_paths(spec_root: Path, base_ref: str | None, include_all: bool) -> list[str]:
    if include_all:
        return ["conformance/agents", "conformance/provider-carriers", "conformance/oracle-corpus", "conformance/storage-laws"]

    paths: set[str] = set(working_tree_paths(spec_root))
    candidates: list[str] = []
    if base_ref:
        candidates.append(base_ref)
    elif os.environ.get("GITHUB_BASE_REF"):
        candidates.append(f"origin/{os.environ['GITHUB_BASE_REF']}")
    candidates.extend(["origin/main", "HEAD~1"])

    seen: set[str] = set()
    errors: list[str] = []
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        try:
            paths.update(git_lines(
                ["diff", "--name-only", "--diff-filter=ACMRT", f"{candidate}...HEAD"],
                cwd=spec_root,
            ))
            return sorted(paths)
        except RuntimeError as error:
            errors.append(f"{candidate}: {error}")
    raise SystemExit("could not determine changed fixture paths:\n" + "\n".join(errors))


def classify(paths: list[str]) -> ChangedCorpora:
    changed = ChangedCorpora(agent_fixtures=set())
    for raw in paths:
        parts = Path(raw).parts
        if len(parts) >= 2 and parts[0] == "conformance" and parts[1] == "agents":
            if len(parts) >= 3:
                changed.agent_fixtures.add(parts[2])
            else:
                changed.agent_fixtures.add("*")
        elif len(parts) >= 2 and parts[0] == "conformance" and parts[1] == "provider-carriers":
            changed.provider_carriers = True
        elif len(parts) >= 2 and parts[0] == "conformance" and parts[1] == "oracle-corpus":
            changed.oracle_corpus = True
        elif len(parts) >= 2 and parts[0] == "conformance" and parts[1] == "storage-laws":
            changed.storage_laws = True
    return changed


def parse_impl_roots(values: list[str], spec_root: Path) -> dict[str, Path]:
    roots = {
        "go": spec_root.parent / "harnas-go",
        "ruby": spec_root.parent / "harnas-ruby",
        "python": spec_root.parent / "harnas-python",
        "typescript": spec_root.parent / "harnas-typescript",
    }
    for value in values:
        if "=" not in value:
            raise SystemExit(f"--impl-root must be NAME=PATH, got {value!r}")
        name, path = value.split("=", 1)
        if name not in roots:
            raise SystemExit(f"unknown implementation {name!r}; expected one of {', '.join(IMPLEMENTATIONS)}")
        roots[name] = Path(path).resolve()
    missing = [name for name, root in roots.items() if not root.exists()]
    if missing:
        detail = ", ".join(f"{name}={roots[name]}" for name in missing)
        raise SystemExit(f"missing implementation checkout(s): {detail}")
    return roots


def env_for(impl: str, label: str, spec_root: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["HARNAS_SPEC"] = str(spec_root)
    env["_HARNAS_IMPL"] = impl
    env["_HARNAS_LABEL"] = label
    return env


def agent_commands(roots: dict[str, Path], spec_root: Path, fixture: str) -> list[tuple[str, list[str], Path]]:
    python = os.environ.get("HARNAS_PYTHON", "python3")
    if fixture == "*":
        return [
            ("go", ["go", "run", "./cmd/conformance", "--fixtures-from", str(spec_root)], roots["go"]),
            ("ruby", ["bundle", "exec", "bin/conformance.rb", "--fixtures-from", str(spec_root)], roots["ruby"]),
            ("python", [python, "bin/conformance.py", "--fixtures-from", str(spec_root)], roots["python"]),
            ("typescript", ["npx", "tsx", "src/testing/cli.ts", "--all"], roots["typescript"]),
        ]
    return [
        ("go", ["go", "run", "./cmd/conformance", "--fixtures-from", str(spec_root), "--fixture", fixture], roots["go"]),
        ("ruby", ["bundle", "exec", "bin/conformance.rb", "--fixtures-from", str(spec_root), fixture], roots["ruby"]),
        ("python", [python, "bin/conformance.py", "--fixtures-from", str(spec_root), fixture], roots["python"]),
        ("typescript", ["npx", "tsx", "src/testing/cli.ts", fixture], roots["typescript"]),
    ]


def corpus_commands(kind: str, roots: dict[str, Path]) -> list[tuple[str, list[str], Path]]:
    python = os.environ.get("HARNAS_PYTHON", "python3")
    if kind == "provider-carriers":
        return [
            ("go", ["go", "test", "./conformance", "-run", "TestProviderCarrierFixtures", "-count=1"], roots["go"]),
            ("ruby", ["bundle", "exec", "rspec", "spec/harnas/provider_carriers_spec.rb"], roots["ruby"]),
            ("python", [python, "-m", "pytest", "tests/test_provider_carriers.py", "-q"], roots["python"]),
            ("typescript", ["npx", "vitest", "run", "tests/unit/provider-carriers.test.ts"], roots["typescript"]),
        ]
    if kind == "oracle-corpus":
        return [
            ("go", ["go", "test", ".", "-run", "Test(JCSV1OracleVectors|EventRowContentHashOracle)", "-count=1"], roots["go"]),
            ("ruby", ["bundle", "exec", "rspec", "spec/harnas/jcs_spec.rb"], roots["ruby"]),
            ("python", [python, "-m", "pytest", "tests/test_jcs.py", "-q"], roots["python"]),
            ("typescript", ["npx", "vitest", "run", "tests/unit/jcs.test.ts"], roots["typescript"]),
        ]
    if kind == "storage-laws":
        return [
            ("go", ["go", "test", ".", "-run", "Test(StorageAdapterOCCLawFixture|FileStorageAdapterLawsS1ThroughS8)", "-count=1"], roots["go"]),
            ("ruby", ["bundle", "exec", "rspec", "spec/harnas/storage_spec.rb"], roots["ruby"]),
            ("python", [python, "-m", "pytest", "tests/test_storage.py", "-q"], roots["python"]),
            ("typescript", ["npx", "vitest", "run", "tests/unit/storage-adapter.test.ts"], roots["typescript"]),
        ]
    raise AssertionError(kind)


def run_group(label: str, commands: list[tuple[str, list[str], Path]], spec_root: Path) -> bool:
    print(f"\n== {label} ==")
    results: list[CommandResult] = []
    for impl, cmd, cwd in commands:
        print(f"$ ({impl}) {' '.join(cmd)}")
        result = run(cmd, cwd=cwd, env=env_for(impl, label, spec_root))
        results.append(result)
        print(f"{impl}: {'PASS' if result.passed else 'FAIL'} ({result.bucket})")

    failed = [result for result in results if not result.passed]
    if failed:
        buckets: dict[str, list[str]] = {}
        for result in results:
            buckets.setdefault(result.bucket, []).append(result.impl)
        if len(buckets) > 1:
            print("divergence buckets:")
            for bucket, impls in sorted(buckets.items()):
                print(f"  {bucket}: {', '.join(sorted(impls))}")
        for result in failed:
            print(f"\n--- {result.impl} {result.label} stdout ---")
            print(result.stdout.rstrip() or "<empty>")
            print(f"--- {result.impl} {result.label} stderr ---")
            print(result.stderr.rstrip() or "<empty>")
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec-root", default=str(ROOT))
    parser.add_argument("--base-ref", help="git base ref for changed fixture detection")
    parser.add_argument("--all", action="store_true", help="run all fixture corpus gates")
    parser.add_argument("--impl-root", action="append", default=[], help="implementation checkout as NAME=PATH")
    args = parser.parse_args()

    spec_root = Path(args.spec_root).resolve()
    roots = parse_impl_roots(args.impl_root, spec_root)
    paths = changed_paths(spec_root, args.base_ref, args.all)
    changed = classify(paths)

    drift = run([sys.executable, "bin/check-drift.py"], cwd=spec_root, env=env_for("spec", "drift", spec_root))
    print(drift.stdout.rstrip())
    if not drift.passed:
        print(drift.stderr, file=sys.stderr)
        return 1

    if changed.empty():
        print("fixture divergence: no changed fixture corpora")
        return 0

    ok = True
    for fixture in sorted(changed.agent_fixtures):
        ok = run_group(
            f"agent fixture {fixture}",
            agent_commands(roots, spec_root, fixture),
            spec_root,
        ) and ok
    if changed.provider_carriers:
        ok = run_group("provider carrier corpus", corpus_commands("provider-carriers", roots), spec_root) and ok
    if changed.oracle_corpus:
        ok = run_group("oracle corpus", corpus_commands("oracle-corpus", roots), spec_root) and ok
    if changed.storage_laws:
        ok = run_group("storage law corpus", corpus_commands("storage-laws", roots), spec_root) and ok

    if ok:
        print("\nfixture divergence ok: changed fixture corpora agree across go, ruby, python, typescript")
        return 0
    print("\nfixture divergence failed: at least one implementation disagrees with the changed corpus")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
