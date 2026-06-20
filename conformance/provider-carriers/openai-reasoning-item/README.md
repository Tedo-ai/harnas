# openai-reasoning-item

OpenAI provider-carrier fixture for a reasoning detail with a
provider-native id.

The canonical semantic layer records the reasoning text and visible
assistant text. The carrier layer preserves the exact OpenAI
`reasoning_details` item so a later `openai.chat_completions`
projection can round-trip the provider-native item when the destination
matches.
