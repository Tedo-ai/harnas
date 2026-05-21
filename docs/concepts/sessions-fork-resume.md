# Sessions, Fork, and Resume

A **Session** is an agent's runtime context: its [Log](./log-and-events.md),
its manifest snapshot, its metadata. Sessions can be saved to disk, loaded
from disk, forked at any point, and replayed.

These are not bolt-on features. They're consequences of the
append-only-Log architecture: if every state-affecting operation is in the
Log, then reading the Log to any point reconstructs the state at that point.

## What a Session is

In code, a Session bundles:

- The Log (the canonical state)
- The manifest snapshot (provider, tools, strategies, hooks — captured at
  session creation)
- Metadata (app-supplied: user ID, workspace ID, story UID, whatever the
  product wants attached)
- An ID (`ses_...`)
- Timestamps

JSONL on disk represents a Session as a header line plus the Log events:

```jsonl
{"session_id": "ses_x9y8", "harnas_version": "0.16.0", "manifest": {...}, "metadata": {...}, "created_at": "2026-05-20T14:00:00Z"}
{"event_id": "evt_a1b2", "seq": 0, "event_type": "user_message", ...}
{"event_id": "evt_c3d4", "seq": 1, "event_type": "assistant_message", ...}
...
```

`Session.Save(path)` writes this file. `Session.Load(path)` reconstructs
the Session from it.

## Resume

To continue an interrupted or completed session:

```ruby
runtime = Harnas::Runtime.build(
  manifest:     manifest_hash,
  session_path: path_to_saved_jsonl,
  resume:       true
)

result = runtime.run("now continue with the next step")
```

The runtime loads the prior Log, preserves the session ID and event seq
counter, and the new user message appends as the next event. The agent
sees full conversation history; the next provider request is built from
the Log via projection.

Use cases:
- Multi-turn conversations across process boundaries (CLI starts a session,
  exits, user runs the CLI again later, conversation continues)
- Recovering from a crash (the Log was being written; reload it and pick
  up where you left off)
- Long-running agents that occasionally checkpoint

## Fork

To branch from an existing session at a specific point:

```ruby
forked = session.fork(at_seq: 12)
new_runtime = Harnas::Runtime.from_session(forked)
new_runtime.run("try a different approach")
```

The forked Session keeps the Log prefix up to `seq: 12` and starts a new
session ID. The original Session is untouched. The fork can now diverge.

Use cases:
- Retry a turn with a different system prompt or different tools, comparing
  outcomes to the original
- A/B testing two model strategies on the same conversation prefix
- Recovering from a bad agent decision: fork before the bad turn, continue
  with corrected input
- Time-travel debugging: replay the agent's history to a moment, then
  intervene

## Diff

Comparing two Sessions is comparing their Logs. The CLI ships a `diff`
subcommand:

```
harnas diff session-a.jsonl session-b.jsonl
```

This pinpoints the first divergent event by sequence number. Useful when
two forks of the same prefix produced different outcomes and you want to
see exactly where they split.

## Why these operations are cheap

Sessions are JSONL files. Fork is a file copy plus a header rewrite.
Resume is a file read. Diff is a sequential walk over two files.

Compare this to systems that persist agent state as a database snapshot,
or as an opaque "memory" object: there, fork means cloning the database,
resume means reconstructing from snapshots and deltas, diff means
diff'ing two database states. The append-only-Log architecture makes the
operations trivial.

## What's preserved on resume

- Full Log history.
- The session ID.
- The manifest snapshot from session creation (NOT the manifest you're
  currently using — that's recorded but the original is what governs
  semantics for events already in the Log).
- Metadata.

What you can override at resume time: the runtime config (provider, model,
new strategies). The Log is the truth; the runtime config governs what
happens next.

## See also

- [`informative/log-and-projection.md`](../../informative/log-and-projection.md) — the formal spec
- [The Log and Events](./log-and-events.md) — what sessions persist
- [Projections](./projections.md) — used to reconstruct provider context from a resumed Log
