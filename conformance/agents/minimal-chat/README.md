# minimal-chat

Smallest meaningful agent conformance fixture.

- Two user messages
- Anthropic-shaped provider script: two text-only responses with
  `stop_reason: end_turn`
- No tools, no strategies, no compaction
- Expected Log is exactly four events: user, assistant, user, assistant

Any conformant Harnas implementation loading this manifest, feeding
these inputs, and serving these scripted provider responses MUST
produce the recorded `expected-log.jsonl`.
