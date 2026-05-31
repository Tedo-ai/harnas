# with-text-and-tool-openai

OpenAI tool-call projection with non-empty assistant text on the same turn as
the tool call.

The second provider request asserts that the prior assistant message preserves
its text `content` while also carrying the `tool_calls` array.
