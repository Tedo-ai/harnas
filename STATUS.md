# Harnas — current state (handoff)

Last verified: 2026-06-24, spec **v0.20.1**. This page tells a new developer
what exists, what's been verified, how to re-verify it yourself, and the rules
that keep the guarantees true. Everything below was confirmed by execution, not
assertion — and you should re-run it rather than trust this file.

## What this is

A spec plus four conforming implementations, with two product-layer adapters
and one downstream product:

| Repo | What it is | State |
|---|---|---|
| `harnas` (this repo) | The spec + the normative fixture corpus | v0.20.1 |
| `harnas-go` | Go implementation | conforming, 75/75 |
| `harnas-ruby` | Ruby implementation (reference) | conforming, 75/75 |
| `harnas-python` | Python implementation | conforming, 75/75 |
| `harnas-typescript` | TypeScript implementation | conforming, 75/75 |
| `harnas-rails` | Rails engine: ActiveRecord storage adapter, generators | depends on `harnas-ruby ~> 0.20` |
| (in `harnas-go`) `SQLStorageAdapter` | DB-backed session storage for Go consumers | passes the shared storage laws |

"Conforming" means the implementation reproduces the normative fixture corpus
byte-for-byte under strict diffing — not approximately, exactly.

## What's verified

- **Agent conformance**: all four implementations pass the 75-fixture suite at
  v0.20.1 (strict diffing — full payloads compared, no key-filtering).
- **Durability**: the `harnas-jcs-v1` canonicalizer, per-event `content_hash`,
  the §21 storage-adapter seam (laws S1–S8), and the OCC conditional-append
  fence are implemented in all four and produce **byte-identical** output
  across implementations (oracle corpus). This is what makes a session written
  by one implementation loadable and verifiable by any other.
- **Provider carriers (§22)**: all four pass the carrier corpus
  (anthropic / gemini / openai) — provider-native reasoning/signature data
  round-trips losslessly back to the provider.
- **DB-backed storage**: `harnas-rails` and the Go `SQLStorageAdapter` both
  pass the same storage laws + OCC fence + DB→JSONL→DB round-trip as the
  file/memory adapters. A database session exports to portable JSONL and back.

## How to re-verify (don't trust this file — run it)

With all repos checked out as siblings (`harnas`, `harnas-go`, …):

```sh
# Four-impl agent conformance (run in each impl repo, with the spec on HARNAS_SPEC)
HARNAS_SPEC=../harnas  bin/conformance            # harnas-go
HARNAS_SPEC=../harnas  bundle exec bin/conformance.rb   # harnas-ruby
HARNAS_SPEC=../harnas  python bin/conformance.py        # harnas-python
HARNAS_SPEC=../harnas  npm run test:conformance:node:all # harnas-typescript

# Cross-impl divergence — proves the corpus itself is correct, not just that
# each impl matches it. Catches a buggy fixture that a conforming impl passes.
python3 bin/check-fixture-divergence.py --all \
  --impl-root go=../harnas-go --impl-root ruby=../harnas-ruby \
  --impl-root python=../harnas-python --impl-root typescript=../harnas-typescript
```

CI runs both on every change (`.github/workflows/conformance.yml`, which
includes the drift check and the fixture-divergence gate).

## The rules that keep this true (do not break these)

1. **The fixtures are the measure, never the target.** A red suite honestly
   reported is progress; a green suite obtained by making the runner (or the
   implementation) recognize fixture-specific values is a defect. See the
   conformance-runner contract (`23-conformance-runner.md`, laws C1–C7 + C5):
   no fixture-name branches, no fixture-literal recognition, strict diffing.
2. **Corpus changes go through the divergence gate.** A new or changed fixture
   is trusted only after all four implementations agree on it. This is the one
   check per-impl conformance cannot do for itself.
3. **The corpus and assertions are tamper-pinned** in `conformance/corpus-manifest.json`.
   Changing a fixture without updating the manifest fails the drift check, by design.
4. **Canonicalization is RFC 8785 (`harnas-jcs-v1`) with two stated deviations**:
   big integers are preserved exact (not I-JSON double-range — tool arguments
   carry 64-bit IDs); Unicode is NOT normalized (the hash attests stored bytes).
   Both are pinned by oracle vectors. Don't add a second normalization.
5. **Claims about other implementations get executed, not relayed.** This whole
   codebase became trustworthy because every cross-impl claim was re-run by a
   second party. Keep that.

## Where things stand

- **Substrate: complete.** Nothing substrate-side is open.
- **Product integration: not started.** Bidvise + AI Brief embed `harnas-rails`;
  Tedo OS chat embeds `harnas-go` + `SQLStorageAdapter`. The one risk to watch:
  an integration that hand-rolls persistence instead of using the adapter
  silently loses portability — no fixture catches that, so each integration
  should be checked for it.

## Known follow-ups (optional, non-blocking)

- **Per-impl README version check.** Impl README version strings have drifted
  before (they track the spec version by hand). A small check in each impl's CI
  asserting "Tracks spec X" matches the spec `VERSION` would stop it recurring.
- **AgentStaple polish**: esbuild asset pipeline (`wip/esbuild-spike` branch),
  surface focus (archive dormant TUI experiments).
