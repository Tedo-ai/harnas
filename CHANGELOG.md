# Changelog

All notable changes to Harnas — both the specification and the
reference implementation — are recorded here.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and Harnas adheres to [Semantic Versioning](https://semver.org/) on
the specification as a whole.

## [0.19.4] — 2026-06-03

### Added

- Added §21 Storage Adapters, defining the `EventDraft` → `EventRow`
  persistence seam and storage laws S1-S9 for persisted Session
  behavior and any adapter interface an implementation exposes.

### Changed

- Updated §19 JSONL Persistence to make Event-level `timestamp`
  normative, including preservation and legacy-row tolerance rules.
- Spec version is now `0.19.4`.
- Fixture version is now `0.19.4`.
- Agent conformance remains at 70 fixtures.

## [0.19.3] — 2026-06-01

### Added

- Added `with-session-isolation-repeat-gemini`, a production-shape
  conformance fixture that runs the same Gemini tool-call scenario twice
  in one process and requires both Sessions to match the canonical Log.
  This guards against process-global mutable state leaking across
  unrelated Sessions.

### Changed

- Spec version is now `0.19.3`.
- Fixture version is now `0.19.3`.
- Agent conformance now covers 70 fixtures.

## [0.19.2] — 2026-06-01

### Added

- Added provider-contract rule R7b requiring projections to preserve
  prior `:tool_use` Events in later provider requests.
- Added text-plus-tool conformance fixtures for Anthropic, OpenAI, and
  Gemini:
  `with-text-and-tool-anthropic`,
  `with-text-and-tool-openai`, and
  `with-text-and-tool-gemini`.

### Changed

- Strengthened `with-tool-call-gemini` so its second provider call now
  asserts that the prior Gemini `functionCall` projects back before the
  tool result.
- Spec version is now `0.19.2`.
- Fixture version is now `0.19.2`.
- Agent conformance now covers 69 fixtures.

## [0.19.1] — 2026-05-31

### Added

- Added provider-contract rule R7a requiring projections to preserve
  assistant text alongside co-occurring reasoning and `tool_use` blocks.
- Added the `with-reasoning-and-text-anthropic` conformance fixture,
  locking that Anthropic projections round-trip both thinking and text
  blocks on a later turn.

### Changed

- Spec version is now `0.19.1`.
- Fixture version is now `0.19.1`.
- Agent conformance now covers 66 fixtures.

## [0.19.0] — 2026-05-24

### Added

- Added canonical Event timestamps. New Events now carry UTC ISO 8601
  timestamps, and implementations preserve them across save/load.
- Added canonical assistant usage metadata with total/cache/reasoning
  token fields, raw provider usage, and provenance.
- Added provider/model identity on assistant provider-response events.
- Added optional `tool_result.payload.approval` metadata with decisions
  `accepted`, `rejected`, `auto_accepted`, `yolo`, and
  `edited_then_accepted`.
- Added `usage.json` and `event-tool-result.json` schemas.
- Added three conformance fixtures:
  `with-tool-result-approval-metadata`,
  `with-assistant-usage-identity`, and
  `streaming-with-usage-identity`.
- Mirrored AgentStaple downstream feedback into
  [`feedback/agentstaple-2026-05-16.md`](feedback/agentstaple-2026-05-16.md).

### Changed

- Promoted portability discipline from informative guidance to a
  normative conformance-process requirement.
- Fixture version is now `0.19.0`.
- Agent conformance now covers 65 fixtures.

## [0.18.2] — 2026-05-22

### Added

- Added `with-bash-session-shell-type`, locking that `bash_session`
  exposes an effective `shell_type` in its tool descriptor config on
  Unix conformance runners.
- Added a portability section to
  [`informative/bash_session.md`](informative/bash_session.md), separating
  cross-OS semantics from OS-specific shell and process cleanup behavior.
- Added cross-platform discipline guidance to
  [`informative/conformance-process.md`](informative/conformance-process.md).

### Changed

- Updated the manifest schema to allow `shell_type` in tool config with
  values `auto`, `posix`, `powershell`, or `cmd`.
- Credited the AgentStaple Windows packaging work that surfaced the
  `bash_session` portability gap.
- Fixture version is now `0.18.2`.
- Agent conformance now covers 62 fixtures.

## [0.18.1] — 2026-05-22

### Added

- Promoted the public docs drafts into `docs/` with foundational concept
  pages for logs, projections, strategies, sandboxes, skills, MCP,
  sessions, providers, and tools.
- Added `with-event-id-preservation-roundtrip`, locking the requirement
  that event identities survive Session save/load.
- Added `with-spawn-agent-reciprocity`, locking the optional
  `harnas.builtin.spawn_agent` guarantee that child Sessions reciprocate
  the parent `agent_spawn` edge.
- Added a "Conformance vs feature parity" section to
  [`informative/conformance-process.md`](informative/conformance-process.md).

### Changed

- Removed stale static version references from the conventions and
  overview docs in favor of the root `VERSION` file.
- Updated the overview's multi-agent framing to reflect v0.18.0's
  delegation substrate while keeping orchestration policy out of scope.
- Documented that implementations MUST preserve `event_id` across
  Session save/load cycles.
- Updated public roadmap/ecosystem docs for shipped v0.16-v0.18 work
  and AgentStaple CLI/chat approval flow.
- Audited capability manifest hashing across Go, Ruby, and Python using
  the v0.18.1 sample manifest. All three produce
  `cap_sha256_ca038c67460e90058675e7b0b9f1ac54323ebb77f903cdbddbb2919fefa90934`;
  explicit RFC 8785/JCS conformance is deferred to v0.19 if needed.
- Fixture version is now `0.18.1`.
- Agent conformance now covers 61 fixtures.

## [0.18.0] — 2026-05-21

### Added

- Added subagent delegation events: `agent_spawn`, `agent_status`, and
  `agent_result`.
- Added Session header metadata for delegation correlation:
  `parent_session_id`, `root_session_id`, `spawn_id`,
  `spawned_by_event_id`, and `delegation_chain`.
- Added capability manifest reference guidance for child Sessions.
- Added [`informative/subagents.md`](informative/subagents.md),
  documenting spawn receipts, parent/child Session edges, join policies,
  capability inheritance, and non-goals.
- Added five subagent conformance fixtures covering success, failure,
  parallel children, nested delegation, and orphan/open-child state.
- Added `expected-projections.jsonl` as a conformance fixture sidecar
  for cross-session projection assertions.

### Changed

- Updated [`informative/log-and-events.md`](informative/log-and-events.md)
  with the v0.18.0 delegation event vocabulary and Session metadata.
- Fixture version is now `0.18.0`.
- Agent conformance now covers 59 fixtures.

## [0.17.0] — 2026-05-21

### Added

- Added typed multimodal content blocks for `:user_message` and
  `:assistant_message`: text, image, and PDF document blocks with
  `base64`, `ref`, and `url` source kinds.
- Added AttachmentStore guidance and default store conventions for
  filesystem, memory, and inline attachment storage.
- Added capability mismatch policy for provider projections, including
  default `metadata_fallback` and opt-in strict `error` behavior.
- Added [`informative/multimodal.md`](informative/multimodal.md),
  documenting content blocks, source kinds, AttachmentStore, provider
  projections, and graceful capability fallback.
- Added eight multimodal conformance fixtures covering Anthropic,
  OpenAI, Gemini, reference-store resolution, metadata fallback, and
  strict capability errors.

### Changed

- Updated [`informative/log-and-events.md`](informative/log-and-events.md)
  with the v0.17.0 message payload shape and legacy `text` migration
  rule.
- Fixture version is now `0.17.0`.
- Agent conformance now covers 54 fixtures.

## [0.16.0] — 2026-05-21

### Added

- Added `credential/proxy`, a `:pre_tool_use` strategy that injects
  credentials into tool arguments immediately before execution without
  persisting credential values in the Log.
- Added the `with-credential-proxy-injection` conformance fixture,
  covering `fetch_url` header injection and credential redaction.
- Added [`informative/isolation.md`](informative/isolation.md),
  clarifying the difference between Harnas tool-boundary guards and
  OS-level isolation.

### Changed

- Fixture version is now `0.16.0`.
- Agent conformance now covers 46 fixtures.

## [0.14.1] — 2026-05-21

### Added

- Added `VERSION` with separate `harnas_version` and
  `fixtures_version` fields. Fixture version is now `0.14.1`.
- Added [`informative/conformance-process.md`](informative/conformance-process.md),
  documenting fixture versioning, spec-first PR flow, conformance
  verification, and packed-artifact testing.
- Added [`informative/provider-implementation.md`](informative/provider-implementation.md),
  recording that the current implementations use direct HTTP rather
  than provider SDKs.
- Added [`informative/log-and-projection.md`](informative/log-and-projection.md),
  clarifying the distinction between the durable Log and derived
  Projections.

### Changed

- Updated `informative/bash_session.md` with the sentinel format and
  explicit non-PTY guidance.

## [0.14.0] — 2026-05-21

### Added

- Added `sandbox/network`, a tool-boundary network strategy with exact
  host allow/deny enforcement for `fetch_url`, plus
  `with-network-sandbox-allow` and `with-network-sandbox-deny`
  conformance fixtures.
- Extended `harnas.builtin.bash_session` so the `run` action accepts an
  optional per-command `env` object. Environment variables apply only to
  that command and do not persist in the shell session. Covered by
  `with-bash-session-per-command-env`.

### Changed

- Updated `harnas.builtin.read_file` to accept `offset` and `limit`,
  return `cat -n` style line-numbered output, and reject binary files.
  Covered by `with-read-file-line-numbers`.
- Agent conformance now covers 45 fixtures.

## [0.13.0] — 2026-05-18

### Added

- Added `guard/health`, a pre-provider health-check strategy, plus the
  `with-health-guard-failure` conformance fixture.
- Extended `guard/repetition` to detect approval-denial loops via
  `tool_result.payload.approval.decision == "rejected"`, plus the
  `with-repetition-guard-rejections` conformance fixture.
- Added Ollama as an OpenAI-compatible local provider kind in the manifest
  schema.
- Added [`informative/worktree.md`](informative/worktree.md), documenting the
  worktree-per-agent convention for coding agents.
- Agent conformance now covers 41 fixtures.

## [0.12.0] — 2026-05-18

### Informative

- Added [`informative/exit-codes.md`](informative/exit-codes.md), a
  recommended CLI exit-code taxonomy for successful runs, agent
  failures, invocation errors, approval rejection, and sandbox
  violations.

### Conformance

- Added `sandbox/write`, a tool-boundary write strategy with allow/deny
  path enforcement for `write_file` and `edit_file`, plus fixtures for
  allowed writes, denied writes, and deny-wins overlap.
- Added `guard/repetition`, an anti-loop strategy for repeated failing
  tool calls, plus `with-repetition-guard`.
- Added `guard/timeout`, a wall-clock session timeout guard, plus
  `with-session-timeout`.
- Agent conformance now covers 39 fixtures.

## [0.11.0] — 2026-05-17

### Informative

- Added [`informative/bash_session.md`](informative/bash_session.md), a
  persistent shell-session tool convention for sandboxed coding agents.
  The document records the design constraints: tool outputs remain JSON
  encoded as strings, shell access is a broad permission surface, and
  command-local output is preferred for agent reasoning.
- Added [`informative/adopter-helpers.md`](informative/adopter-helpers.md),
  documenting the non-normative runtime assembly, transcript projection,
  and dynamic tool snapshot helper surfaces surfaced by AgentStaple
  integration.

### Conformance

- Promoted `harnas.builtin.bash_session` to the conformable surface with
  four new fixtures: `with-bash-session-basic`,
  `with-bash-session-state-persists`, `with-bash-session-timeout`, and
  `with-bash-session-truncation`.
- Agent conformance now covers 34 fixtures.

### Fixed

- Replaced stale pre-split `reference/` paths with the public
  `Tedo-ai/harnas-ruby` repository layout, and updated strategy examples
  to show session-scoped hook installation.
- Updated the informative `bash_session` convention with dogfood
  findings: command approval is the application boundary, `cwd` is not a
  sandbox, background jobs are shell-managed, and command-local output is
  preferred for agent reasoning.

## [0.10.0] — 2026-05-10

### Added

- Added `with-skills` and `with-skills-invalid-name` conformance
  fixtures for the `load_skill` built-in and skills-index prompt
  convention, bringing agent conformance to 30 fixtures.

### Informative

- Tightened [`informative/skills.md`](informative/skills.md) with the
  canonical `## Skills` index shape, the guard text that discourages
  listing-time `load_skill` calls, skill-name validation, optional
  index metadata, and empty-body behavior.
- Tightened [`informative/mcp.md`](informative/mcp.md) with MCP
  result-content flattening guidance, server-name validation, and
  degraded startup behavior for unavailable servers.

## [0.9.3] — 2026-05-10

### Informative

- Added [`informative/skills.md`](informative/skills.md), a
  non-normative convention for Claude Code-style Markdown skills loaded
  through an ordinary `load_skill` tool.
- Added [`informative/mcp.md`](informative/mcp.md), a non-normative
  mapping from MCP tools, resources, and prompts onto existing Harnas
  primitives.

No normative spec changes and no conformance fixture changes.

## [0.9.2] — 2026-05-08

### Conformance

- Hardened `with-tool-call-openai` to assert on the second projected
  request (via `expect_request`), proving the OpenAI projection folds
  `:tool_use` into the preceding assistant message's `tool_calls[]`,
  emits `:tool_result` as `role: "tool"` with `tool_call_id`, and
  normalizes `content` to `null` when `tool_calls[]` is present.
  Without this assertion an implementation could silently drop
  `:tool_use` / `:tool_result` events on outbound projection and still
  pass the suite (the case that surfaced this round in harnas-go).

No spec normative changes; informative test surface only.

## [0.9.1] — 2026-05-05

### Trust polish

- Updated public version and fixture-count language to match the
  current verified surface: 28/28 agent fixtures and 18/18
  cross-language round-trip pairs.
- Backfilled the missing v0.9.0 changelog entry.
- Renumbered §05's duplicate R7 versioning rule to R8.
- Aligned §20's production-embedding streaming guidance with §15's
  v0.8 rule that streaming transport events are Observation-only and
  not persisted in the durable Log.
- Removed stale "forthcoming" markers and roadmap claims from current
  normative docs.
- Softened cross-language Event id language: per-Session `seq` remains
  the canonical identity; secondary ids are implementation-local unless
  a future version specifies canonical serialization.

### v0.9.1

#### Added

- Added optional manifest tool `config` objects. Runtime
  implementations must preserve the opaque JSON value in the Session's
  manifest snapshot and make it available to the resolved handler.
- Added an informative recommended Session metadata envelope for
  trace, actor, workspace, and conversation identifiers.

## [0.9.0] — 2026-05-05

### Specification

#### Added

- Added manifest-declared `hooks` entries with implementation-defined
  handler resolution and `on_error` policy support.
- Added `:runtime_error` for harness-internal terminal failures,
  keeping provider failures distinct from hook/strategy failures.
- Added strategy Observation events (`:strategy_started` /
  `:strategy_completed`) with an effect taxonomy for strategy audit
  sidecars.
- Added an informative Observation-layer cost-tracking recipe.
- Added conformance fixtures for manifest hooks, fail-turn hook
  runtime errors, and strategy Observation sidecars, bringing agent
  conformance to 27 fixtures.

#### Clarified

- §18 now states that a Manifest is bound to a Session at creation time;
  later manifest source changes apply only to new Sessions.

## [0.8.0] — 2026-05-03

### Specification

#### Changed

- §15 now makes streaming transport Events Observation-only. Deltas,
  turn brackets, and streaming tool-use fragments are no longer
  durable Log Events; only consolidated semantic Events land in the
  Log.
- §13 adds normative `:stream_event` Observation semantics and an
  informative `Observation::DeltaLogger` sidecar recipe for adopters
  that need durable transport traces.
- §19 clarifies that new Session JSONL saves must be delta-free while
  legacy pre-v0.8 saves containing delta rows remain loadable.
- Streaming conformance expected Logs were regenerated without
  transport deltas.

#### Added

- Added `with-delta-logger-sidecar`, bringing agent conformance to
  24 fixtures and proving the opt-in sidecar pattern.

## [0.7.0] — 2026-05-02

### Specification

#### Added

- Added provider-contract rule R7 requiring Ingestors to capture
  provider reasoning content on
  `:assistant_message.payload.reasoning`, and requiring Projections to
  round-trip reasoning for providers that need it.
- Added `schemas/event-assistant-message.json`, including the optional
  `reasoning` block-list field.
- Added reasoning conformance fixtures for Anthropic, OpenAI, and
  OpenAI-compatible Kimi-shaped responses.
- Added `roundtrip-with-reasoning` to verify Session JSONL preservation
  and Anthropic projection round-trip across languages.

## [0.6.0] — 2026-05-02

### Specification

#### Clarified

- The implementation table now describes Python as a peer
  implementation with live providers, built-in tools, middleware,
  compaction, permissions, and CLI surface, matching Ruby and Go's
  public feature framing.

## [0.5.0] — 2026-05-02

### Specification

#### Added

- Added §19, a normative Session JSONL persistence format covering the
  session header, event rows, UTF-8/newline handling, dense seq order,
  and preservation requirements.
- Added §20, an informative production embedding guide covering
  per-conversation Session lifecycles, persistence boundaries,
  streaming, provider errors, fork/retry flows, memory composition, and
  explicit non-goals.

#### Clarified

- Round-trip conformance now encourages phase-2 `expect_request`
  assertions, and `roundtrip-minimal-chat` uses one to prove that
  cross-language load preserves projection behavior as well as final
  Log shape.
- The implementation table now describes the current Ruby, Python,
  and Go surfaces consistently, including the Go live-provider work
  and Python's next parity arc.

## [0.4.0] — 2026-04-29

### Specification

#### Added

- Agent conformance now includes provider error retry/fatal, tool
  failure, permission denial, streaming tool failure, streaming
  provider failure, strategy composition, revert chains, system
  prompts, Session fork/continue, and large/unicode argument fixtures,
  bringing the suite to 20 cross-language cases.
- Added `conformance/round-trips/roundtrip-minimal-chat`, the first
  cross-language Session persistence fixture. The coordinator now runs
  the Ruby/Python/Go 3x3 load/save matrix.
- §04 now requires `:tool_use` ids to be unique within a Session, with
  provider-specific synthetic ids when the wire format lacks one.
- §05 now requires compaction strategies to preserve tool-use/result
  pair integrity by dropping orphan halves from candidate sets.
- §15 now defines stream failure semantics: partial deltas remain,
  `:assistant_turn_failed` records the failure, successful
  consolidation is not emitted, and the runtime retries or terminates
  with a terminal `:provider_error`.

#### Clarified

- §01 now explicitly treats cross-Session persistent memory as out of
  scope. A Session Log remains single-conversation; adopters compose
  external memory back into each new Session.
- `conformance/README.md` now defines scripted provider error entries
  and canonical compact JSON for conformance stub tool arguments,
  including sorted keys and unescaped unicode.
- `conformance/README.md` now defines buffered `expect_request`
  assertions so fixtures can verify provider-specific projection wire
  shapes, not only final Logs.
- `conformance/README.md` now defines the `round-trips/` fixture
  shape and the Session JSONL persistence contract used by
  cross-language round-trip tests.

## [0.2.0] — 2026-04-28

### Specification

#### Added — normative

- §15 now makes explicit that streaming conformance fixtures capture
  every delta Event verbatim, in append order, followed by the
  consolidated Events that complete the stream.
- Two streaming agent fixtures were added:
  `streaming-minimal-chat` and `streaming-with-tool-call`.

## [0.1.0] — 2026-04-28

First substantively releasable version. The specification and the
Ruby reference implementation have been live-verified end-to-end
against three providers (Anthropic, OpenAI, Gemini) on a real
multi-turn tool-using agent workload.

### Specification

#### Added — normative

- §01 R1–R5: Append-only Log + Projections + Mutations as the
  substrate. The Log is sovereign; provider request bodies are
  pure functions of the Log.
- §01 R6–R8: **Annotative Events** category and the canonical
  `:annotation` Event type. Carries `{kind, data}` with dotted
  namespacing; projections MUST NOT include them in provider
  request bodies; compaction MAY shadow them.
- §01 R9–R11: **Provider error events**. The canonical
  `:provider_error` Event captures one failed `Provider.call`
  with `{provider, status, error_class, message, attempt,
  terminal}`. Non-terminal entries record retries; the terminal
  entry indicates the failure was final and the Session ends with
  reason `:provider_failed`.
- §01 explicit Scope and Out-of-Scope sections, including
  policy-level permissions, task-level evaluation, multi-agent
  orchestration, runtime environment integration, and cross-
  implementation telemetry export — all explicitly out of scope.
- §01 Adjacent specifications: explicit MCP positioning. Harnas
  composes with MCP, does not replace it.
- §18 (Agent Manifest) gained the optional top-level `system`
  field — a system prompt that projects into provider-specific
  slots (Anthropic top-level `system`, OpenAI `role: "system"`
  message, Gemini `systemInstruction.parts[]`).
- Sections 04 (Tools), 05 (Compaction), 06 (Benchmarks),
  07 (Permission), 13 (Observation), 14 (Hooks),
  15 (Streaming), 16 (Actions), 17 (Composition Rules),
  18 (Agent Manifest) all stable for 0.1.

#### Conformance

- Five canonical fixtures shipped under `spec/conformance/agents/`:
  `minimal-chat`, `with-marker-tail-compaction`, `with-tool-call`
  (Anthropic), `with-tool-call-openai`, `with-tool-call-gemini`.
  Any conformant implementation MUST reproduce these byte-for-byte.

### Reference implementation (Ruby)

#### Added

- `Harnas::Agent` façade — `Agent.from_manifest(path).chat(text)`.
  Wraps `Manifest.load` + `AgentLoop` for one-call ergonomics.
  Includes `use_provider` for test/demo overrides and `shutdown`
  for clean strategy uninstall.
- `Harnas::Log#save` / `Harnas::Log.load` — JSONL round-trip
  preserving seq, id, type, and payload (including re-symbolizing
  Symbol-valued payload fields).
- `Harnas::Session#save` / `Harnas::Session.load` — wraps the Log
  in a self-describing JSONL with a session header.
- `Harnas::Tools::Builtin` — eight canonical tool implementations:
  `read_file`, `write_file`, `edit_file`, `list_dir`, `glob`,
  `grep`, `run_shell`, `fetch_url`. Pasteable manifest descriptors;
  unsandboxed by design (compose with permission strategies for
  safety).
- `Harnas::Tools::Middleware` — composable wrappers: `Timed`,
  `Logged`, `Retried` (stateless per-wrap helpers), and
  `RateLimiter` (stateful, shared budget across wraps).
- `Harnas::Tools::Middleware::StaleReadGuard` — Log-sourced
  read-before-edit guard. State lives in `:annotation` events,
  so `Session.save` / `Session.load` round-trips guard state for
  free.
- `Harnas::Strategies::Compaction::ToolOutputCap` — canonical
  compaction strategy targeting oversized `:tool_result` payloads
  (the largest context-cost driver in production harnesses).
- `Harnas::Providers::RetryPolicy` — configurable retry / abort
  decisions for transient HTTP statuses (default 408, 429, 500,
  502, 503, 504) and network-style error classes, with
  exponential backoff. `AgentLoop` integrates it; failures land
  as `:provider_error` events in the Log.
- Live providers: Anthropic, OpenAI, Gemini — buffered and
  streaming variants. Tool-registry parity across all three
  (canonical Log → three wire shapes).
- `Harnas::Tools::Builtin` example agents:
  `examples/01-hello-world`, `02-tool-calling`, `03-provider-switch`,
  `04-builtin-tools`, `05-codebase-qa` (live).

#### Wire-format quirks absorbed into the Log substrate

- **Anthropic** — provider-issued `toolu_xxx` ids round-trip directly.
- **OpenAI** — provider-issued `call_xxx` ids round-trip directly.
- **Gemini** — function-name-as-id is replaced with a deterministic
  per-ingestor `gemini.<name>.<counter>` id, while wire-side
  `functionResponse.name` is recovered from the matching
  `:tool_use` in the Log. Thinking-mode `thoughtSignature` is
  round-tripped via `:annotation` events with kind
  `gemini.thought_signature`.

#### Tooling

- `bin/conformance.rb` — runs every fixture under
  `spec/conformance/agents/` against the reference and diffs the
  resulting Log.
- `bin/web.rb` — Puma-backed real-time browser inspector with
  five tabs (chat, context, timeline, runtime, config).
- `bin/chat.rb` — interactive REPL CLI.

### Numbers

- 539 RSpec examples, all passing
- 5/5 conformance fixtures, all passing
- RuboCop clean across 135 files
- 28 devlog entries
- 30 spec sections in `spec/`

## What's next: 0.3

Carryovers and deferred decisions, captured for posterity:

- **Production deployment safety.** Reference implementations should
  scope hook and observation buses per Session so concurrent agents
  in one process cannot inherit each other's strategies or subscribers.
- **MCP client.** Spec already positions MCP as composable; no
  reference implementation yet. Once landed, every existing MCP
  server becomes a Harnas tool source.
- **`:tool_output_truncate` mutation** for tool-chain-preserving
  truncation. `ToolOutputCap` collapses a tool pair into a
  user-role summary today; a future mutation type could preserve
  the tool-call structure while shrinking the result.
- **Composability mixin for Tool objects** (`Harnas::Tools::Composable`)
  for tools that want to register their own hook handlers at
  install time. Today middleware composition is pure Ruby
  wrapping, which covers most cases — the lifecycle mixin would
  be motivated by a concrete use case we haven't found yet.

[0.19.4]: https://github.com/Tedo-ai/harnas/releases/tag/v0.19.4
[0.19.3]: https://github.com/Tedo-ai/harnas/releases/tag/v0.19.3
[0.19.2]: https://github.com/Tedo-ai/harnas/releases/tag/v0.19.2
[0.19.1]: https://github.com/Tedo-ai/harnas/releases/tag/v0.19.1
[0.19.0]: https://github.com/Tedo-ai/harnas/releases/tag/v0.19.0
[0.18.2]: https://github.com/Tedo-ai/harnas/releases/tag/v0.18.2
[0.18.1]: https://github.com/Tedo-ai/harnas/releases/tag/v0.18.1
[0.18.0]: https://github.com/Tedo-ai/harnas/releases/tag/v0.18.0
[0.17.0]: https://github.com/Tedo-ai/harnas/releases/tag/v0.17.0
[0.16.0]: https://github.com/Tedo-ai/harnas/releases/tag/v0.16.0
[0.14.1]: https://github.com/Tedo-ai/harnas/releases/tag/v0.14.1
[0.14.0]: https://github.com/Tedo-ai/harnas/releases/tag/v0.14.0
[0.13.0]: https://github.com/Tedo-ai/harnas/releases/tag/v0.13.0
[0.12.0]: https://github.com/Tedo-ai/harnas/releases/tag/v0.12.0
[0.11.0]: https://github.com/Tedo-ai/harnas/releases/tag/v0.11.0
[0.10.0]: https://github.com/Tedo-ai/harnas/releases/tag/v0.10.0
[0.9.3]: https://github.com/Tedo-ai/harnas/releases/tag/v0.9.3
[0.9.2]: https://github.com/Tedo-ai/harnas/releases/tag/v0.9.2
[0.9.1]: https://github.com/Tedo-ai/harnas/releases/tag/v0.9.1
[0.9.0]: https://github.com/Tedo-ai/harnas/releases/tag/v0.9.0
[0.8.0]: https://github.com/Tedo-ai/harnas/releases/tag/v0.8.0
[0.7.0]: https://github.com/Tedo-ai/harnas/releases/tag/v0.7.0
[0.6.0]: https://github.com/Tedo-ai/harnas/releases/tag/v0.6.0
[0.5.0]: https://github.com/Tedo-ai/harnas/releases/tag/v0.5.0
[0.4.0]: https://github.com/Tedo-ai/harnas/releases/tag/v0.4.0
[0.2.0]: https://github.com/Tedo-ai/harnas/releases/tag/v0.2.0
[0.1.0]: https://github.com/Tedo-ai/harnas/releases/tag/v0.1.0
