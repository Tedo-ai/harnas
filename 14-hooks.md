# 14 — Hooks

This document specifies the **Hooks** layer: the bidirectional
intervention mechanism through which Strategies — compaction,
permission, memory, tool discovery, meta-reflection, cache awareness,
retry, and every similar concern — plug into the harness's agent loop.

Hooks complement `13-observation.md`. Observation is read-only metric
emission; Hooks are intervention points where a registered handler
can append Events, deny actions, modify behavior, or return decisions
the harness then honors.

## Position in the Stack

[informative]

    Observation → one-way notification bus (read-only)
    Hooks       → bidirectional intervention bus (can return decisions
                  and append Events)

Both fire at canonical lifecycle moments. An implementation MAY
implement both on top of the same underlying registration mechanism,
but the semantics differ: Observation always short-circuits cheaply
when no subscribers exist and never affects control flow; Hooks MAY
affect control flow and MAY carry default behavior when no handlers
are registered.

## Registration and Invocation

**R1.** A Harnas implementation MUST expose a way to register one or
more **Hook Handlers** at a named **Hook Point**. A Hook Handler is a
callable that receives a keyword-argument payload specific to the
Hook Point.

**R2.** A Hook Handler MAY return any value. The meaning of the
return value is specific to the Hook Point; this specification
defines the expected return shape per canonical Hook Point below.

**R3.** When a Hook Point is invoked, each registered Handler for
that Point MUST be called in registration order. The invocation
result MUST be the Array of non-nil return values from all Handlers,
preserving registration order. If no Handlers are registered, the
result MUST be an empty Array.

**R4.** Handler exceptions MUST NOT propagate into the calling Harnas
code path. An implementation MUST isolate exceptions and continue
delivering the invocation to other registered Handlers. Exceptions
MAY be surfaced to Observation subscribers via a canonical
`:hook_handler_failed` event.

## Canonical Hook Points

**R5.** The following Hook Points MUST be invoked by any
implementation of the Harnas agent loop at the moments described. An
implementation MAY define additional Points; Handler callers MUST
tolerate Points they don't recognize (they simply never fire).

### Lifecycle

| Hook Point | Payload | Expected return | Emitted when |
|---|---|---|---|
| `:session_started` | `session:` | ignored | Before the first turn of an agent loop |
| `:session_ended` | `session:`, `reason:` (Symbol) | ignored | After the loop exits (normal, max_turns, error) |
| `:turn_started` | `session:`, `turn:` (Integer) | ignored | At the start of each loop iteration |
| `:turn_ended` | `session:`, `turn:`, `stop_reason:` (Symbol) | ignored | After each iteration, before pending tool dispatch |

### Request path

| Hook Point | Payload | Expected return | Emitted when |
|---|---|---|---|
| `:pre_projection` | `session:` | ignored (side effects to Log) | Before calling `projection.call(log)` |
| `:post_projection` | `session:`, `request:` (Hash) | ignored | After the Projection produced a request |
| `:pre_provider_call` | `session:`, `request:` | ignored | Before dispatching the wire request |
| `:post_provider_call` | `session:`, `response:` (Hash or nil) | ignored | After the Provider returned (or failed) |

### Ingest

| Hook Point | Payload | Expected return | Emitted when |
|---|---|---|---|
| `:pre_ingest` | `session:`, `response:` | ignored | Before the Ingestor converts the response |
| `:post_ingest` | `session:`, `events:` (Array) | ignored | After the ingested events have been appended |

### Tool execution

| Hook Point | Payload | Expected return | Emitted when |
|---|---|---|---|
| `:pre_tool_use` | `session:`, `tool_use:` (Event) | `{ allow: Boolean, reason?: String }` or nil | Before executing a :tool_use Event |
| `:post_tool_use` | `session:`, `tool_use:`, `tool_result:` (Event), `denied:` (Boolean) | ignored | After execution (real or denial) |

**R6.** For the `:pre_tool_use` Hook Point: any Handler return
matching `{ allow: false }` MUST cause the Runner to skip actual tool
execution and append a failure `:tool_result` Event carrying the
returned `reason` (or a generic message if absent). Multiple
Handlers MAY register; a single `{ allow: false }` from any Handler
denies the call (any-deny-wins).

## Side Effects and the Event-Sourced Substrate

[informative]

Most Hook Handlers need not return values at all; they effect change
by appending Mutation Events to the Session's Log. For example, a
compaction Strategy registered at `:pre_projection` measures projected
context size via the Observation layer, and — when it exceeds a
threshold — appends a `:compact` Event. The next Projection invocation
sees the `:compact` and applies it via `Mutations.apply`. The Log
remains the source of truth; the Hook is merely the trigger.

Decision-returning Handlers (`:pre_tool_use`) are used only where
control flow genuinely cannot be expressed through Event appends.

## Composition Order

**R7.** When multiple Handlers register for the same Hook Point, they
MUST be invoked in registration order. Implementations MAY expose a
priority mechanism (higher-priority Handlers run first) as an
extension; the default is FIFO.

## Scoped Registration

[informative]

Implementations SHOULD provide a scoped registration mechanism for
test and ad-hoc usage — the reference implementation exposes
`Harnas::Hooks.scoped { ... }` which preserves the registry state
across the block.

## Versioning Note

**R8.** New Hook Points and payload fields MAY be added in later spec
versions. Existing Hook Point names and their required payload fields
and expected return shapes are stable within a major spec version.
Handlers that don't recognize a payload field MUST ignore it.
