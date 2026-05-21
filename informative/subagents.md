# Subagents

Status: informative. This document describes the recommended
delegation model for Harnas-based agents. The event types and Session
metadata it references are part of the spec vocabulary, but this
document explains the design intent, common projections, and product
integration patterns.

The short version: spawn is a receipt. Parent Logs contain edges to
child Sessions, not child internals. Child Sessions remain separately
persisted, separately replayable Logs. Operators and products recover a
multi-agent view through cross-session projections.

## Design Frame

Harnas treats delegation as a relationship between Sessions rather than
as a graph runtime. This keeps the substrate small enough to inspect and
strong enough to replay. A parent can spawn or attach a child, record
what it asked for, record what context and capabilities the child
received, and later record a terminal result. The parent does not copy
the child's full transcript into its own Log.

This is deliberately narrower than many agent frameworks. There are no
role taxonomies, no global task queues, no sibling message bus, and no
graph-node abstraction. Products can build those on top when they need
them. The substrate only needs durable correlation: who spawned whom,
what was asked, what was allowed, and what came back.

The prior-art lesson is simple: framework-specific orchestration objects
age poorly when they leak into persistence. Explicit Session edges age
better. They are easy to diff, easy to inspect, and easy to project into
whatever shape a UI or supervisor needs.

## Event Types

### agent_spawn

`agent_spawn` records that a parent created or attached a child Session.
Required fields are `spawn_id`, `child_session_id`, and `task`.

```json
{
  "event_type": "agent_spawn",
  "payload": {
    "spawn_id": "spn_a1b2c3",
    "child_session_id": "ses_child_xyz",
    "spawned_by_event_id": "evt_parent_tool_use",
    "spawn_mode": "new",
    "task": "Audit the projection model and summarize implications.",
    "context": { "mode": "prompt", "refs": [] },
    "capabilities": {
      "inherit": true,
      "manifest_ref": "cap_sha256_...",
      "overrides": { "tools_deny": ["bash_session"] }
    },
    "join_policy": "async",
    "metadata": { "label": "Projection explorer", "role": "explorer" },
    "budget": { "max_turns": 10, "max_tool_calls": 25 },
    "retry_of_spawn_id": null
  }
}
```

`spawn_mode` is `"new"` by default. `"attach"` means the parent is
attaching an existing Session as a child, for example in a resume-as-child
workflow. The child id must already exist.

`join_policy` is advisory metadata for projections and operator UIs.
`"async"` means the parent intends to continue while the child runs.
`"wait"` means the parent intends to block until `agent_result`.
`"detached"` means no result is expected. The Log semantics are the
same for all three values.

`budget` records intent only. Enforcement belongs to runtimes or guard
strategies.

`retry_of_spawn_id` creates a retry edge. Retries do not mutate the
prior result; they append a new spawn with a new child Session.

### agent_status

`agent_status` is an optional lifecycle update for operator visibility.
It is not required for correctness.

```json
{
  "event_type": "agent_status",
  "payload": {
    "spawn_id": "spn_a1b2c3",
    "child_session_id": "ses_child_xyz",
    "status": "running",
    "summary": "Reading projection code.",
    "progress": { "completed": 2, "total": 5 },
    "details": {}
  }
}
```

The status enum is `queued`, `running`, `waiting`, `succeeded`,
`failed`, `canceled`, and `orphaned`. A child may go directly from
`agent_spawn` to `agent_result` without any status events.

`agent_status` is not an inter-agent communication channel. Children do
not send parent instructions through status updates. Treat it as
operator-visible progress.

### agent_result

`agent_result` is the terminal outcome visible to the parent. Required
fields are `spawn_id`, `child_session_id`, and `status`. `status` is one
of `succeeded`, `failed`, or `canceled`.

```json
{
  "event_type": "agent_result",
  "payload": {
    "spawn_id": "spn_a1b2c3",
    "child_session_id": "ses_child_xyz",
    "status": "succeeded",
    "result": {
      "text": "The child found that explicit spawn ids simplify replay.",
      "structured": null,
      "artifact_refs": []
    },
    "usage": {
      "prompt_tokens": 1234,
      "completion_tokens": 456,
      "total_tokens": 1690
    },
    "last_child_event_id": "evt_...",
    "error": null
  }
}
```

Failures use the same event type with `result: null` and an `error`
object. `agent_result` must appear at most once per `spawn_id` in a
single parent Log. A retry is represented by a new `agent_spawn`, not by
editing the old result.

Large outputs should be stored as artifacts and referenced by URI. The
`harnas://session/<id>/artifacts/<name>` form points into the child
Session's artifact store. The substrate does not require artifacts; they
are a convenient escape hatch for results too large to inline.

## Session Correlation

Child Session headers carry reciprocal metadata:

```json
{
  "session_id": "ses_child_xyz",
  "parent_session_id": "ses_parent_abc",
  "root_session_id": "ses_root_001",
  "spawn_id": "spn_a1b2c3",
  "spawned_by_event_id": "evt_parent_cause",
  "delegation_chain": [
    { "session_id": "ses_root_001", "spawn_id": null },
    { "session_id": "ses_parent_abc", "spawn_id": "spn_parent" }
  ]
}
```

`parent_session_id` plus `spawn_id` is the canonical immediate edge.
`root_session_id` and `delegation_chain` are denormalized for quick
operator lookups and robust ancestry queries. Root Sessions omit these
fields or set them to null.

Cross-session integrity is bidirectional. A parent `agent_spawn` must
point to a child whose header names the parent and spawn id. A child
header must point back to a parent Log containing the matching spawn.
Broken links are load-time or projection-time errors.

## Capability Manifests

Children usually inherit a narrowed form of the parent's capabilities.
The effective manifest can be large, so `agent_spawn` records a stable
`manifest_ref` plus high-signal overrides:

```json
{
  "capabilities": {
    "inherit": true,
    "manifest_ref": "cap_sha256_...",
    "overrides": { "tools_deny": ["bash_session"] }
  }
}
```

`inherit: true` means "parent capabilities, modulo overrides." `inherit:
false` means "only the overrides or supplied manifest." By default a
child receives equal or fewer capabilities than its parent. Escalation is
a product policy decision and should be visible in `overrides`.
Implementations should warn when a spawn appears to grant more than the
parent had.

Implementations may store the full capability manifest in an
AttachmentStore, a side directory, a database table, or any equivalent
content-addressed location. The reference only needs the `manifest_ref`
to be stable and replayable.

## Cross-session Projections

Delegation projections span multiple persisted Session Logs. The
substrate does not store a global interleaved Log.

Required projection helpers:

- `delegation_tree(session_id)` returns a recursive tree of spawns,
  statuses, results, and child branches.
- `descendant_timeline(session_id)` returns a flat stream of events from
  the Session and all descendants, sorted by timestamp with
  `(session_id, seq)` as a tiebreaker.
- `open_children(session_id)` returns spawn ids that have an
  `agent_spawn` but no terminal `agent_result`.
- `descendant_usage(session_id)` aggregates token usage across the
  Session and descendants.

Conformance fixtures may include `expected-projections.jsonl` beside
`expected-log.jsonl`. Each row names a projection, input Session id, and
expected output. This makes projection behavior a tested cross-language
artifact while preserving the Log-per-session invariant.

Projection implementations need a Session resolver. Filesystem runtimes
usually load child JSONL files from a sibling directory. Database-backed
adopters resolve by primary key. Large trees may cache projection output
by `(session_id, seq_at_compute)` and invalidate when any descendant Log
appends.

## Built-in Spawn Tool

The substrate does not require spawning to happen through a built-in
tool. A product can expose its own `delegate_to_agent` tool, create a
child Session, and append `agent_spawn` through the runtime API.

Reference implementations should also provide an optional
`harnas.builtin.spawn_agent` descriptor for common cases:

```json
{
  "name": "spawn_agent",
  "handler": "harnas.builtin.spawn_agent",
  "input_schema": {
    "type": "object",
    "properties": {
      "task": { "type": "string" },
      "label": { "type": "string" },
      "role": { "type": "string" },
      "tools_deny": { "type": "array", "items": { "type": "string" } }
    },
    "required": ["task"]
  }
}
```

The built-in records a spawn receipt and returns generated ids. Products
remain responsible for scheduling, supervising, joining, and persisting
the child according to their own runtime policy.

## Non-goals

The following are intentionally outside the substrate:

- sibling-to-sibling messaging
- task queues and atomic claiming
- crew/team/role taxonomies
- graph node or checkpoint abstractions
- global interleaved Logs
- heartbeat events beyond `agent_status`
- retry or cancellation event types separate from spawn/result
- automatic orphan reapers
- spawn budget enforcement

If a behavior can be represented as a Session edge, a tool call, an
annotation, or a projection, prefer that over adding a new primitive.
