<!--
Mirrored from /Users/renevanpelt/projects/agentstaple/SPECS/harnas-feedback.md
on 2026-05-24. Original lives in the AgentStaple repo and is authoritative.

This copy will be promoted to the harnas spec repo at
`feedback/agentstaple-2026-05-16.md` when v0.19 is cut.

Tracking notes (added by harnas project, not part of original):

- Spec-level asks landing in v0.19: #5 Approval, #7 Usage, portability lesson.
- Spec-level asks queued for v0.20: #2 Transcript projection, #6 Snapshot helpers.
- Contrib-pattern asks queued for v0.20+: #3 MCP (per ADR 0005).
- Examples-not-contrib (held): #1 Runtime builder, #4 Tool pack. Reference
  templates land in examples/ in v0.20; promotion only after a second
  downstream consumer independently reaches for the same primitives.
- "Maybe later" items remain held: reflexive self, artifact runtime, subagent
  events. Subagent events to be drafted (spec-only, no impl) in v0.21+ once
  OpenStaple work begins.
-->

# Harnas Feedback

This file collects feedback from building AgentStaple as a real downstream
consumer of Harnas.

The goal is not to push product-specific AgentStaple behavior into Harnas. The
goal is to identify repeatable boilerplate that every serious Harnas-based
agent will otherwise rewrite.

## Current Size Signal

As of 2026-05-16, excluding `node_modules` and built UI artifacts:

- AgentStaple app/core/UI source is about 7,800 lines.
- `cmd/agentstaple/main.go` is about 2,850 lines.
- `internal/agentstaple/tools.go` is about 810 lines.
- `internal/agentstaple/mcp*.go` is about 380 lines.
- `internal/agentstaple/chat.go` is about 430 lines.

Some of that is product code. Some is real Harnas adapter glue.

## Current Upstream Patch Pressure

### harnas-go v0.18.1 `bash_session` Windows build

While preparing downloadable AgentStaple preview builds for macOS, Linux, and
Windows, `GOOS=windows GOARCH=amd64 go build` failed in
`harnas-go/bash_session.go` because the implementation directly references Unix
process-group APIs:

- `syscall.SysProcAttr{Setpgid: true}`
- `syscall.Getpgid`
- `syscall.Kill(-pgid, signal)`

AgentStaple temporarily uses a local `replace` to `third_party/harnas-go` where
the process-group setup/kill behavior is split behind build tags:

- Unix keeps process-group setup and group kill.
- Windows compiles by skipping process-group setup and falling back to
  `Process.Kill()`.

This was fixed upstream in Harnas v0.18.2 with OS-specific build tags, Windows
compile CI, and a `shell_type` capability field. AgentStaple should now delete
the local patch during the next dependency upgrade.

The lasting lesson is useful for future Harnas built-ins: declare portability
explicitly, compile on Windows in CI, and expose OS-specific command semantics
through tool config rather than hiding them from the model.

## Strong Candidates For Harnas

### 1. Session Runtime Builder

AgentStaple currently has to manually assemble:

- `harnas.Session`
- provider
- stream provider
- projection
- ingestor
- registry
- runner
- system prompt
- tool descriptors
- metadata snapshots
- JSONL load/resume/save

This is correct but repetitive.

Recommended Harnas addition:

```go
runtime, err := harnas.NewRuntime(harnas.RuntimeConfig{
    Provider: providerSpec,
    SessionPath: path,
    Resume: true,
    SystemPrompt: prompt,
    Tools: tools,
    Metadata: metadata,
})
```

The exact API can differ, but Harnas should own the boring assembly path for
"create or resume a session with this provider, registry, metadata, and JSONL."

Why it matters:

- Reduces app boilerplate.
- Makes provider projection/ingestor pairing harder to get wrong.
- Gives all downstream agents the same save/resume behavior.

### 2. Transcript Projection

AgentStaple converts Harnas logs into UI transcript items:

- user messages
- assistant messages
- tool uses
- tool results
- tool status/error
- stream deltas while in flight

Every UI will need this.

Recommended Harnas addition:

```go
items := harnas.ProjectTranscript(session.Log, harnas.TranscriptOptions{
    IncludeTools: true,
    IncludeProviderErrors: true,
})
```

The output should be structured and UI-neutral. Harnas should not decide the
visual design, but it can define the canonical semantic view of a Log.

### 3. MCP Stdio Adapter

AgentStaple implemented:

- stdio process spawn
- JSON-RPC initialize
- tools/list
- tools/call
- tool name namespacing
- degraded startup status
- metadata snapshot
- content flattening
- process cleanup

This is almost certainly not AgentStaple-specific.

Recommended Harnas addition:

- `harnas/mcp` package or `harnas-go-mcp` sibling package.
- Stdio first.
- SSE/websocket later.
- Standard flattening for MCP content:
  - join text items with blank lines
  - render images/resources as placeholders
  - do not fail just because content is multimodal

Why it matters:

- Every Harnas agent will want MCP.
- Namespacing and manifest snapshot timing are easy to get subtly wrong.
- Process lifecycle bugs are better solved once.

### 4. Local Workspace Tool Pack

AgentStaple defines common local tools:

- `list_dir`
- `read_file`
- `grep`
- `write_file`
- `edit_file`
- `propose_edit`
- `inspect_shell`

Some belong in Harnas more than others.

Recommended split:

- Harnas should provide a configurable local filesystem pack:
  - `read_file`
  - `list_dir`
  - `grep`
  - `write_file`
  - `edit_file`
  - path scoping
  - stale-read guard integration
- AgentStaple can keep `self` and product-specific policy.
- `propose_edit` should probably move to Harnas after one more product cycle,
  once the diff/approval shape is proven.

Why it matters:

- File tools are not unique to AgentStaple.
- Stale-read protection is already Harnas-shaped.
- Apps should not repeatedly hand-roll scoped path checks.

### 5. Approval Event Convention

AgentStaple has approval rules and wants browser approval prompts for writes and
commands. Today approval is mostly an app-level callback.

Recommended Harnas spec addition:

- Standard metadata shape on `tool_result`:

```json
{
  "approval": {
    "decision": "accepted|rejected|auto_accepted|yolo|edited_then_accepted",
    "rule_matched": "string or null",
    "applied_diff": "string or null"
  }
}
```

- Optional `approval_required` event may be worth considering later, but Harnas
  should not own UI prompts yet.

Why it matters:

- Replay, fork, audit, and UI timelines all benefit from a common shape.
- It avoids each agent inventing incompatible approval logs.

### 6. Dynamic Tool Snapshot Helpers

AgentStaple snapshots skill and MCP tools into session metadata before session
start. The ordering matters.

Recommended Harnas addition:

```go
metadata := harnas.ManifestSnapshot(harnas.ManifestSnapshotInput{
    Tools: registry.Tools(),
    Skills: skills,
    MCP: servers,
})
```

or a smaller helper:

```go
descriptors := harnas.ToolDescriptors(registry)
```

Why it matters:

- Dynamic tools are common.
- Save/load/replay needs tool descriptors.
- The current pattern is easy to forget.

### 7. Usage Projection Support

AgentStaple wants to show token and estimated cost by project, agent, session,
and model. The current Log shape is close but not quite strong enough for
accurate per-model and per-day accounting.

What works today:

- Session metadata records initial `provider` and `model`.
- Assistant messages can carry `payload.usage.input_tokens` and
  `payload.usage.output_tokens`.
- Usage can be projected from JSONL without mutating the Log.

Recommended Harnas additions:

- Standardize a cross-provider usage object:
  - `input_tokens`
  - `output_tokens`
  - `total_tokens`
  - `cache_read_input_tokens`
  - `cache_write_input_tokens`
  - `reasoning_tokens`
  - optional raw provider usage
- Record provider/model on each assistant/provider response event, not only in
  the session header. AgentStaple supports `/model use`; one session can use
  multiple models.
- Add canonical event timestamps so "today", "this week", and chart axes do
  not depend on session filenames or filesystem mtimes.
- For streaming, guarantee the final provider usage lands either on the final
  assistant message or on a standard terminal usage event.
- Mark usage provenance: provider-reported, runtime-estimated, or unavailable.

Do not make Harnas own pricing. Prices change, discounts exist, and local model
costs can be zero or unknowable. Harnas should provide reliable usage and model
identity; AgentStaple should project estimated cost from its configured pricing
table.

## Maybe Harnas Later

### 1. Reflexive `self` Convention

AgentStaple's `self` tool is product-defining, but the pattern is broadly
useful.

Possible Harnas informative convention:

- Agents should expose a single introspection tool.
- It should answer paths/config/tools/session/how-to-change.
- It should return structured JSON.

Do not make this normative yet. Different products will expose different local
truth.

### 2. Artifact Runtime Convention

XLSX/DOCX/PDF/image work will likely use generated scripts plus approvals.

Possible future convention:

- artifact input/output metadata
- generated script logging
- runtime directory metadata
- rendered preview attachment metadata

This is too early for a built-in.

### 3. Subagent Events

OpenStaple will need parent/child sessions, delegated tasks, and heartbeats.

Possible future convention:

- `agent_spawn`
- `agent_status`
- `agent_result`

Too early. Build in AgentStaple/OpenStaple first.

## Probably Keep In AgentStaple

- Web UI.
- CLI command shape.
- Machine registry under `~/.agentstaple`.
- Trust prompts.
- Agent naming and onboarding.
- Product-specific `self` wording.
- Model database UX.
- OpenStaple orchestration.

These are product opinions, not substrate conventions.

## Highest-Leverage Ask To Harnas

If Harnas only takes one thing next, take the **runtime builder plus transcript
projection**.

Those two would immediately reduce AgentStaple boilerplate without forcing a
product opinion into the spec. MCP is the next best candidate because the
adapter code is technical plumbing and likely to be reused by every serious
agent.
