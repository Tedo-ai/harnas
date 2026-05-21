# Conformance Process

[informative]

Harnas currently has three reference implementations: `harnas-go`,
`harnas-ruby`, and `harnas-python`. The process is designed for those
implementations and for the forthcoming `harnas-ts` implementation to
pass the same conformance suite against a specific fixtures version.
Spec changes must propagate through a deterministic process to prevent
drift.

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

## Packed Artifact Testing

Each implementation also tests the packed or built artifact, not just
the source tree:

- `harnas-go`: build the binary, run conformance through the binary.
- `harnas-ruby`: `gem build`, install the gem in a fresh bundle, run
  conformance from the installed gem path.
- `harnas-python`: build the wheel, install it in a fresh virtualenv,
  run conformance from the installed package.
- `harnas-ts`: `npm pack`, install the tarball in a throwaway project,
  run conformance from the installed package.

This catches packaging bugs such as missing bundled schemas, missing
exports, and incomplete package data that source-only tests can miss.
