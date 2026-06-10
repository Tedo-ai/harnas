# with-manifest-hooks-variant

Variant canary for manifest hook dispatch. The manifest installs a
`:post_tool_use` hook named `conformance.audit_post_tool_use_variant`.
Conformant implementations resolve the handler through the hook registry;
fixture-aware implementations that special-case only
`conformance.audit_post_tool_use` fail this fixture.

Conformance-relevant properties checked by this fixture:

- Manifest `hooks` entries are installed at Session start
- Handler names resolve through the implementation-defined hook
  handler registry
- Hook registration order places the hook effect after the tool result
  and before the next provider turn
