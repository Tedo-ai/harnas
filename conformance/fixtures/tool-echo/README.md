# Case: `tool-echo`

**Prompt:** "Please call the echo tool with text set to 'hello from harnas'.
After the tool returns, reply with exactly the word: done."

**Intent:** The smallest complete tool round-trip a harness can perform —
a two-turn agent loop where the assistant requests a tool call, the
harness executes it, and the assistant finishes with a terminal reply.
This case fixes the minimal wire shape for tool-enabled requests and
responses: the `tools:` descriptor array in the request, a `tool_use`
content block in the response, a `tool_result` content block in the
follow-up request, and a terminal text response.

**Shape:** two API round-trips per provider, recorded as
`turn-1-request.json`, `turn-1-response.json`, `turn-2-request.json`,
`turn-2-response.json`.

**Expected behavior:** the response in turn 1 MUST contain at least one
`tool_use` content block referencing `name: "echo"` and some input hash
containing the requested text. Turn 2 MUST end with the assistant's text
response and `stop_reason` indicating end of turn. The exact text of the
final reply is not asserted — LLM outputs are non-deterministic.

**Used by:** the `bin/smoke_tool.rb` script and future tool-round-trip
mock providers. Regenerate with `just tool --record`.
