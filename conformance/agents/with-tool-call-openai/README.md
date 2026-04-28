# with-tool-call-openai

Proves the OpenAI-shaped tool-use round-trip at the agent level.
Parallel to `with-tool-call` (Anthropic); the Log they produce is
structurally identical — only the provider wire shape differs.

- Single user prompt: "what time is it?"
- Provider script returns an OpenAI `tool_calls` response first
  (`content: null`, `finish_reason: "tool_calls"`), then a final
  text response after the tool result is appended.
- One tool declared in the manifest (`get_current_time`); the
  conformance runner stubs the handler to echo its name + args.

Expected Log captures the full two-turn flow: user_message →
(assistant_message with empty text, stop_reason `tool_use`) →
tool_use → tool_result → (second assistant_message with the final
text).

Conformance-relevant properties checked by this fixture:

- `Projections::OpenAI` accepts a `Registry` and emits
  `tools[]` as OpenAI function declarations
- `Projections::OpenAI` folds `:tool_use` events into the
  preceding assistant message's `tool_calls[]` and emits
  `:tool_result` as `role: "tool"` with `tool_call_id`
- `Ingestors::OpenAI` emits a consolidated `:assistant_message`
  (with empty text when the model only called tools) plus one
  `:tool_use` event per `tool_calls[]` entry
- AgentLoop dispatches pending tool_use events through the
  registry's Runner and appends `:tool_result` before the next
  provider call — the same Log shape as the Anthropic fixture
