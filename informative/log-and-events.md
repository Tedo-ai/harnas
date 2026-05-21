# Log And Events

[informative]

The Log is the durable source of truth for a Session. Every row is an
immutable Event with a type and payload. Event payloads may evolve
additively across Harnas releases, but loaders preserve old Session
JSONL files so saved conversations remain replayable.

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
