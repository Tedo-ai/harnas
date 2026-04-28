# Case: `hello-one-word`

**Prompt:** `say hello in one word`

**Intent:** The smallest interesting round-trip a provider can do — a single
user turn, a single short assistant reply, no tool calls, no streaming, no
system prompt. This case exists to fix the minimal wire shape of each
provider's request/response.

**Expected behavior:** the provider returns a single token or short word of
text (the exact text is not asserted — LLM outputs are non-deterministic).
The response MUST contain a text block, a stop reason, and token usage
metadata; the precise field names are provider-specific.

**Used by:** both real and mock provider implementations; see
`../../02-provider-contract.md` and `../README.md`.
