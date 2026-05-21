# Log And Events

[informative]

The Log is the durable source of truth for a Session. Every row is an
immutable Event with a type and payload. Event payloads may evolve
additively across Harnas releases, but loaders preserve old Session
JSONL files so saved conversations remain replayable.

## Message Content Migration

Harnas v0.17.0 introduces typed `content` blocks for `:user_message`
and `:assistant_message` payloads. The canonical payload shape is:

```json
{
  "content": [
    { "type": "text", "text": "hello" }
  ]
}
```

For `:assistant_message`, `stop_reason`, `usage`, and optional
`reasoning` remain alongside `content`.

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
