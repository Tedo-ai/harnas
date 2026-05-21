# Log And Events

[informative]

The Log is the durable source of truth for a Session. Every row is an
immutable Event with a type and payload. Event payloads may evolve
additively across Harnas releases, but loaders preserve old Session
JSONL files so saved conversations remain replayable.

## Event Vocabulary

Core persisted Event types include:

- `user_message`
- `assistant_message`
- `tool_use`
- `tool_result`
- `compact`
- `revert`
- `summary`
- `annotation`
- `provider_error`
- `runtime_error`
- `agent_spawn`
- `agent_status`
- `agent_result`

`agent_spawn`, `agent_status`, and `agent_result` are the delegation
events introduced in v0.18.0. A parent Log records spawn edges,
operator-visible status updates, and terminal child outcomes; child
internals stay in the child Session's own Log.

## Message Payloads

Harnas v0.17.0 introduces typed `content` blocks for `:user_message`
and `:assistant_message` payloads. A `:user_message` payload carries
the user's turn as an ordered list of text, image, and document blocks:

```json
{
  "content": [
    { "type": "text", "text": "hello" }
  ]
}
```

An `:assistant_message` payload uses the same `content` field for the
assistant's visible response. Existing assistant metadata remains
alongside it:

```json
{
  "content": [
    { "type": "text", "text": "The PDF is a quarterly report." }
  ],
  "stop_reason": "end_turn",
  "usage": { "input_tokens": 120, "output_tokens": 16 },
  "reasoning": []
}
```

Current v0.17.0 ingestors emit assistant text content from provider
responses. Assistant image/document generation and non-text tool results
are future work; the shared content block vocabulary intentionally
leaves room for those additions.

## Legacy Text Migration

Earlier Harnas releases used a legacy `text` field:

```json
{ "text": "hello" }
```

Implementations parsing `:user_message` or `:assistant_message`
payloads MUST accept both shapes. On read, a legacy `text` field MUST
be normalized to:

```json
[{ "type": "text", "text": "..." }]
```

New Events written by a v0.17.0 or later runtime MUST use `content`.
The `text` field is read-only legacy compatibility. Implementations MAY
preserve the original serialized bytes when copying an old Session file
without interpreting it, but any parsed in-memory Event view and any new
Session save produced from that view use the canonical `content` shape.

See [`multimodal.md`](multimodal.md) for the full content block schema,
attachment source kinds, provider projection behavior, and capability
mismatch policy.

## Delegation Session Metadata

Subagent-capable runtimes use top-level Session header fields to make
parent/child correlation explicit:

```json
{
  "__session__": true,
  "id": "ses_child_xyz",
  "metadata": {},
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

A root Session has these fields omitted or set to `null` / `[]`. A
child Session has them populated. The immediate edge is
`parent_session_id` plus `spawn_id`; `root_session_id` and
`delegation_chain` are denormalized for fast projections and robust
ancestry queries.

Cross-session integrity is reciprocal: a child header references a
parent Session whose Log contains a matching `agent_spawn`, and the
parent `agent_spawn` references a child whose header points back at the
same parent and spawn id. See [`subagents.md`](subagents.md) for the
delegation model and projection helpers.

The reference helper projections are:

- `delegation_tree(session_id)`
- `descendant_timeline(session_id)`
- `open_children(session_id)`
- `descendant_usage(session_id)`

They are computed on demand from separately persisted Session Logs.
Harnas does not persist a global interleaved Log.

## Capability Manifest References

`agent_spawn.payload.capabilities.manifest_ref` names the resolved
capability manifest the child received. The ref format is
`cap_sha256_<hash>`, where the hash is computed over a canonical JSON
serialization of the manifest content. Implementations may store the
manifest content in an AttachmentStore, side table, filesystem
directory, or database row.

The spawn event carries high-signal overrides inline so operators can
see what changed without expanding the full manifest:

```json
{
  "capabilities": {
    "inherit": true,
    "manifest_ref": "cap_sha256_...",
    "overrides": {
      "tools_deny": ["bash_session"]
    }
  }
}
```

By default, children receive equal or fewer capabilities than their
parent. Capability escalation is a product policy decision. If a child
receives more capability than the parent, the escalation MUST be visible
in the spawn event's `overrides`, and implementations SHOULD warn or log
at spawn time.
