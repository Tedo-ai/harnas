# The Log and Events

The Log is the only durable state Harnas requires. Everything an agent does
becomes a typed event in the Log.

## What the Log is

An append-only sequence of events, persisted as JSONL (newline-delimited
JSON). One event per line. Events are never modified or removed once
appended.

Each event has a stable shape:

```json
{"event_id": "evt_a1b2", "session_id": "ses_x9y8", "seq": 0, "event_type": "user_message", "created_at": "2026-05-20T14:00:00Z", "payload": {"text": "process story ovxpoM6g"}}
{"event_id": "evt_c3d4", "session_id": "ses_x9y8", "seq": 1, "event_type": "assistant_message", "created_at": "2026-05-20T14:00:02Z", "payload": {"text": "Starting pipeline...", "stop_reason": "tool_use", "usage": {"input_tokens": 142, "output_tokens": 18}}}
{"event_id": "evt_e5f6", "session_id": "ses_x9y8", "seq": 2, "event_type": "tool_use", "created_at": "2026-05-20T14:00:02Z", "payload": {"tool_use_id": "call_1", "name": "fetch_story", "arguments": {"uid": "ovxpoM6g"}}}
{"event_id": "evt_g7h8", "session_id": "ses_x9y8", "seq": 3, "event_type": "tool_result", "created_at": "2026-05-20T14:00:03Z", "payload": {"tool_use_id": "call_1", "output": "{...}", "error": null}}
```

- `seq` increases monotonically per session. It's the canonical ordering.
- `event_id` is unique within a session. Use for cross-references between
  events (e.g., a `tool_result` references its triggering `tool_use_id`).
- `event_type` is the discriminator. Consumers pattern-match on it.
- `payload` shape is determined by `event_type`.

## Event types

The current vocabulary:

- `user_message` — input from the user (or upstream system).
- `assistant_message` — text from the model. Includes `stop_reason` and
  `usage` metadata.
- `tool_use` — the assistant requested a tool call.
- `tool_result` — the result of executing a tool. Contains `error` (null on
  success).
- `provider_error` — the provider returned an error (rate limit, content
  filter, transient failure). The agent loop may retry or surface it.
- `runtime_error` — the harness itself failed in a way that ended the turn
  or the session (sandbox violation, repetition guard, timeout, cost budget
  exceeded).
- `annotation` — non-load-bearing metadata attached to the Log by strategies
  or hooks (e.g., credential injection markers, compaction notes).
- `compaction` — a strategy compressed older Log content into a shorter
  representation for context-window management.
- `agent_spawn` — a parent session created or attached a child session.
- `agent_status` — optional lifecycle/progress update for a spawned child.
- `agent_result` — terminal child outcome summarized back to the parent.

Adding an event type is a semver-significant change to the spec.

## Why append-only

Because the Log is the truth, every useful operation reduces to reading
the Log:

- **Replay** — read events in `seq` order, reconstruct the session.
- **Audit** — every action the agent took is in the Log, with timestamps
  and reasoning context.
- **Fork** — `Session.Fork(seq)` keeps the prefix up to `seq` and creates a
  new session for divergent continuation.
- **Diff** — comparing two sessions is comparing their Logs.
- **Time-travel** — reading the Log up to any `seq` reconstructs the
  session's state at that moment.

If the Log were mutable, none of these would be reliable. Append-only is
not a stylistic choice; it's what makes everything else possible.

## What's in the Log vs what's derived

The Log contains every observable event from the agent's session. It does
NOT contain:

- The provider request body (computed by projection)
- The current UI transcript (computed by projection)
- Compacted summaries embedded in prompts (derived at projection time)
- Token usage totals (sum across events on demand)

This separation is deliberate. See [Projections](./projections.md) for why.

## Persistence

JSONL on disk. One file per session, conventionally named by the session
ID. Implementations may also persist to a database — the editorial Rails
pipeline uses Postgres with a `harnas_events` table whose row payload is
the same JSON shape. The on-disk JSONL is the canonical wire format;
storage backends are an implementation detail.

## See also

- [`informative/log-and-projection.md`](../../informative/log-and-projection.md) — the formal spec
- [Projections](./projections.md) — derived views of the Log
- [Sessions, fork, resume](./sessions-fork-resume.md) — operating on the Log
