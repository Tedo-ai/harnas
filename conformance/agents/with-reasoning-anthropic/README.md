# with-reasoning-anthropic

Anthropic-shaped reasoning capture and round-trip. The first assistant turn
contains a `thinking` block plus a tool call. The follow-up provider script
asserts that the projection sends the captured reasoning back as a thinking
content block before the tool call.
