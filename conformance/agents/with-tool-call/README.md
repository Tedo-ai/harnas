# with-tool-call

Exercises the tool-use round-trip inside an agent-level fixture.

- Single user prompt: "what time is it?"
- Provider script returns a `tool_use` response first, then a
  final text response after the tool result is appended.
- One tool declared in the manifest (`get_current_time`); the
  conformance runner stubs the handler to echo its name + args,
  producing a deterministic tool_result.

Expected Log captures the full two-turn flow: user_message →
(Anthropic assistant_message with empty text, stop_reason
`tool_use`) → tool_use → tool_result → (second assistant_message
with the final text).

Conformance-relevant properties checked by this fixture:

- Anthropic ingestor emits the consolidated `:assistant_message`
  AND a separate `:tool_use` event (per `spec/15-streaming.md` S5)
- AgentLoop dispatches pending tool_use events through the
  registry's Runner and appends `:tool_result` before the next
  provider call
- Second turn picks up the tool_result in its projection and
  receives the final assistant_message
