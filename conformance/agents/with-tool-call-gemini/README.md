# with-tool-call-gemini

Proves the Gemini-shaped tool-use round-trip at the agent level.
Parallel to `with-tool-call` (Anthropic) and `with-tool-call-openai`
(OpenAI); the Log they produce is structurally identical — only the
provider wire shape differs.

- Single user prompt: "what time is it?"
- Provider script returns a Gemini `functionCall` part first
  (no text), then a final text response after the tool result is
  appended.
- One tool declared in the manifest (`get_current_time`); the
  conformance runner stubs the handler to echo its name + args.

Gemini has no explicit `id` on `functionCall` — the function's
`name` is the wire-side correlation key. The ingestor synthesizes
a deterministic per-instance id (`gemini.<name>.<counter>`) so
that repeated calls to the same function across turns are
distinct in the canonical Log. The Gemini projection looks up
the function name via the matching `:tool_use` event when
emitting the wire-side `functionResponse`, so on the wire only
the function name is sent — the synthesized id stays in the
Log substrate.

Expected Log captures the full two-turn flow: user_message →
(assistant_message with empty text, stop_reason `tool_use`) →
tool_use → tool_result → (second assistant_message with the final
text).

Conformance-relevant properties checked by this fixture:

- `Projections::Gemini` accepts a `Registry` and emits
  `tools[0].functionDeclarations[]`
- `Projections::Gemini` folds `:tool_use` events into the
  preceding `role: "model"` message's `parts[]` as `functionCall`,
  and emits `:tool_result` as a `role: "user"` message with a
  `functionResponse` part
- `Ingestors::Gemini` emits a consolidated `:assistant_message`
  (with empty text when the model only called tools) plus one
  `:tool_use` event per `functionCall` part; stop_reason is
  coerced to `:tool_use` whenever any part is a `functionCall`
- AgentLoop produces the same Log shape as the Anthropic and
  OpenAI tool-call fixtures — one Log, three wire shapes
