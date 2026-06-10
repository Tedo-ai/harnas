# Conformance Process

[informative]

Harnas currently has four reference implementations: `harnas-go`,
`harnas-ruby`, `harnas-python`, and `harnas-typescript`. The process is
designed for all reference implementations to pass the same conformance
suite against a specific fixtures version. Spec changes must propagate
through a deterministic process to prevent drift.

## Versions

The spec repo carries two versions in `VERSION`:

- `harnas_version` is the protocol/spec release version.
- `fixtures_version` is the conformance fixture artifact version.

The versions usually move together for releases, but they are distinct.
A fixture-only correction can bump `fixtures_version` without changing
the protocol. Each implementation's conformance runner reports the
fixture version it ran against, and each implementation CHANGELOG should
name the fixture version used for the release.

New or changed fixtures SHOULD include `fixture_version_added` in their
`manifest.json` so the introduction point is traceable. Older fixtures
may omit the field.

The spec repo also carries `conformance/corpus-manifest.json`. That file
binds each `fixtures_version` to the sorted agent fixture corpus and the
SHA-256 hash of every fixture's `expected-log.jsonl`. Any fixture addition,
removal, or expected-log change MUST update the corpus manifest and bump
`fixtures_version` in the same change. Drift checks in the spec and
reference implementations fail when the live corpus no longer matches the
manifest entry for the declared fixture version.

## When The Spec Changes

For a new strategy, event, tool, or behavior change:

1. Open a PR against `Tedo-ai/harnas` that updates the spec prose,
   informative docs, or JSON schema; adds or modifies conformance
   fixtures; and bumps `fixtures_version`. Do not bump
   `harnas_version` until implementations pass.
2. Open companion PRs against each implementation. Each PR implements
   the change against the new fixture version, passes the conformance
   suite locally, and references the spec PR.
3. Merge order: the spec PR merges first, with all companion PRs
   reviewed and ready. Companion PRs merge within hours of the spec PR.
4. Once all implementations have merged and passed CI, bump
   `harnas_version` on the spec repo and lockstep-tag the spec and
   implementations.

## When An Implementation Finds A Bug

If an implementation reveals a spec ambiguity or fixture gap, fix the
spec repo first with a failing fixture that demonstrates the issue.
Then propagate the fix to all implementations before tagging.

Do not fix the bug in one implementation alone when the behavior is
conformable. That creates de facto spec drift.

## Conformance Verification

Each implementation's CI runs the conformance suite against a pinned
fixtures version. CI failure on conformance blocks the release. Release
notes should include both the fixture count and fixture version.

## Conformance Vs Feature Parity

Conformance has three distinct axes:

**Fixture conformance.** All conformance fixtures pass byte-identically
against the implementation. This is the load-bearing claim. An
implementation is "conformant at v0.X.Y" when all v0.X.Y fixtures pass.
Some fixtures exercise production-shaped execution, such as running
multiple independent Sessions in one long-lived process, so conformance
guards both the event vocabulary and the process-safety assumptions
needed by embedded hosts.

**Live provider compatibility.** Smoke tests against real Anthropic,
OpenAI, Gemini, and Ollama endpoints. These are recommended for every
implementation but are NOT required for the conformance claim. A new
implementation may pass fixture conformance well before all live
providers are validated.

**Surface parity.** Optional implementation surfaces include operator
CLI commands (`inspect`, `fork`, `diff`, `project`), the full set of
AttachmentStore implementations beyond filesystem, and optional helper
built-ins such as `spawn_agent`. These are useful but do not gate the
conformance claim. A new implementation can ship "conformant at
v0.18.0" with 59/59 fixtures even if its CLI lacks `inspect`.

When announcing a new implementation, the claim "conformant at v0.X.Y"
specifically means fixtures pass. Live provider readiness and surface
parity should be reported separately.

## Packed Artifact Testing

Each implementation also tests the packed or built artifact, not just
the source tree:

- `harnas-go`: build the binary, run conformance through the binary.
- `harnas-ruby`: `gem build`, install the gem in a fresh bundle, run
  conformance from the installed gem path.
- `harnas-python`: build the wheel, install it in a fresh virtualenv,
  run conformance from the installed package.
- `harnas-typescript`: `npm pack`, install the tarball in a throwaway project,
  run conformance from the installed package.

This catches packaging bugs such as missing bundled schemas, missing
exports, and incomplete package data that source-only tests can miss.

## Cross-Platform Discipline

Each implementation's CI MUST compile-check on its target platforms.
The default target platforms for reference implementations are:

- `harnas-go`: linux/amd64, linux/arm64, darwin/amd64, darwin/arm64,
  windows/amd64. Compile-only is acceptable for Windows until a runtime
  conformance suite exists there.
- `harnas-ruby`: any platform with Ruby 3.1 or newer.
- `harnas-python`: any platform with Python 3.10 or newer.
- `harnas-typescript`: Node 20+, Bun, and Deno.

When a built-in tool or strategy uses platform-specific APIs such as
process groups, signals, or filesystem semantics, the implementation
MUST isolate the OS-specific code: build tags in Go, platform checks in
Ruby and Python, and runtime adapters in TypeScript. Platform-specific
behavior MUST be surfaced in the tool's `config` so agents can adapt.

When the spec mandates behavior that is not portable across OSes, the
spec doc MUST mark which parts are normative cross-OS and which are
OS-specific.

Reference implementations MUST compile and pass core fixtures on Linux,
macOS, and Windows. Until a Windows runtime conformance suite exists,
compile-only Windows CI is acceptable only for fixtures that require
Unix-specific shell or filesystem behavior.

Fixtures that rely on Unix-only behavior SHOULD declare `platform:
unix` in their manifest. Cross-platform fixtures SHOULD use `platform:
any` or omit the field. A fixture's platform marker is conformance
metadata; it does not weaken the underlying spec requirement for
portable implementation surfaces.
