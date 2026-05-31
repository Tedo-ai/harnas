# with-reasoning-and-text-anthropic

Anthropic-shaped reasoning capture and projection round-trip when the same
assistant turn contains both non-empty text and a thinking block.

The second provider request asserts that the prior assistant message projects
both the `thinking` block and the assistant `text` block. This fixture guards
against silently dropping the model's answer from conversation history when
reasoning is present.
