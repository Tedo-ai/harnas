# with-text-and-tool-anthropic

Anthropic tool-use projection with non-empty assistant text on the same turn as
the tool call.

The second provider request asserts that the prior assistant turn projects both
the text block and the `tool_use` block. This guards R7a for the tool-call
branch: an implementation must not drop assistant text just because a tool call
co-occurs on the same turn.
