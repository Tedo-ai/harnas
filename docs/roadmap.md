# Roadmap

What's in flight, what's queued, and what we've explicitly deferred. This
page is updated when priorities shift; it's not a fixed calendar.

## Recently shipped

- **v0.19.0 — approval, usage, and portability hardening** — canonical
  timestamps, per-message provider/model identity, cross-provider usage
  shape, approval metadata on `tool_result`, and portability discipline.
- **v0.18.0 — subagent events and cross-session projections** —
  `agent_spawn`, `agent_status`, and `agent_result` events, reciprocal
  parent/child Session metadata, and delegation projections for operator
  views.
- **v0.17.0 — multimodal content blocks** — text, image, and PDF document
  content blocks, AttachmentStore helpers, and graceful provider capability
  mismatch fallback.
- **v0.16.0 — `credential/proxy` strategy** — `pre_tool_use` strategy that
  injects credentials into tool calls without persisting values in the Log.
  Shipped with `informative/isolation.md` documenting OS-level guards.
- **AgentStaple interactive TUI approval prompt** — the CLI/chat approval
  flow for human-reviewed edits shipped alongside the existing web UI and
  approval rules.
- **v0.15.0 — MCP adapter parity** — Go and Python gained the MCP adapter
  surface that Ruby had since v0.11.0.
- **v0.14.0 — sandbox/network, read_file enhancements, bash_session env** —
  library primitives needed for any serious sandboxing or file reading work.

## In flight

- **harnas-typescript reference implementation** — TypeScript port targeting
  v0.19.0 conformance. The development runner covers the 65-fixture suite;
  v1.0.0 waits on cross-language round-trip verification and release review.

## Queued

### Substrate (Harnas spec + reference implementations)

- **`propose_edit` promotion to a built-in tool.** Currently lives in
  AgentStaple. Once the TUI approval prompt lands and the diff-first editing
  pattern is proven in production, it gets lifted to `harnas.builtin.propose_edit`.
- **Parallel tool execution.** Allow the AgentLoop to dispatch multiple
  `tool_use` events from one turn concurrently. Architecturally non-trivial;
  high value for long-running tasks.
- **Checkpoint snapshots strategy.** Write a full session snapshot every N
  tool calls. Allows resume mid-task after a crash rather than from scratch.

### Products

- **vp-agent ships v1.** Drop-in fourth harness for the vp spawn system,
  replacing the current `opencode` path for Gemini agents. Owned by the vp
  spawn team.
- **AgentStaple native multi-provider.** Route Anthropic and Gemini natively
  rather than via OpenRouter. Currently OpenRouter-only.
- **AgentStaple graduated permission modes.** Four levels — restrictive,
  ask, session-allowlist, yolo — replacing today's binary YOLO toggle.
- **AgentStaple git worktree per task.** Branch isolation by default; agent
  works in a per-run worktree.
- **harnas-rails gem extraction.** Lift the editorial Rails pipeline's
  Harnas plumbing into a reusable Rails engine, with the two-table
  persistence schema and a base ActiveJob.
- **OpenStaple.** Multi-agent orchestration. Starts when substrate
  prerequisites (subagent events, parent/child sessions, credential proxy,
  cross-session projection) are all landed.

## Deferred (intentionally not on the timeline)

- **Artifact runtime.** Generating XLSX/DOCX/PDF/image artifacts via scripts
  with approvals. Real product need eventually, but no consumer is blocked
  on it today.
- **Scheduled recurring tasks.** Cron-shaped agent triggers. Belongs in
  OpenStaple when it exists, not in the substrate.
- **Multi-channel messaging adapters.** WhatsApp/Slack/Discord integrations.
  Belongs in a product layer, not in Harnas.
- **PTY as a built-in tool.** `bash_session` is deliberately not a PTY. A
  real PTY tool is a separate optional addition, deferred until a consumer
  needs interactive programs (vim, less, ssh).
- **GUI editor detection.** Not a substrate concern.

## What changes this roadmap

- **Real consumer pressure.** When a production deployment hits a gap,
  that gap moves up the queue. The editorial Rails pipeline produced several
  reordering moments in the v0.14 / v0.15 window.
- **Ecosystem signal.** New patterns from inspirations (NanoClaw, zerostack,
  agent-harness-kit, the vp spawn orchestrator doc) get added to the queue
  if they're substrate-shaped, deferred or noted otherwise.
- **Spec changes.** Anything that lands in the spec lands in all four
  implementations in the same release window.

## What this roadmap is not

- **Not a commitment.** Items get reordered. Items get dropped. New items
  get added.
- **Not a release calendar.** "In flight" means active work; "queued" means
  identified and prioritized but not yet started; specific version numbers
  are intentions, not promises.
- **Not exhaustive.** Maintenance work (bug fixes, doc improvements,
  conformance hardening) happens continuously alongside the items above and
  doesn't get its own roadmap entry.

For the canonical record of what shipped when, read the CHANGELOGs in each
implementation repository.
