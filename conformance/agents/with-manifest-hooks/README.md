# with-manifest-hooks

Exercises declarative hook installation from an Agent Manifest.

The manifest installs a `:post_tool_use` hook named
`conformance.audit_post_tool_use`. The conformance runner resolves
that handler and appends a deterministic `:annotation` after the
tool result.

Conformance-relevant properties checked by this fixture:

- Manifest `hooks` entries are installed at Session start
- Handler names resolve through the implementation-defined hook
  handler registry
- Hook registration order places the hook effect after the tool result
  and before the next provider turn
