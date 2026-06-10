# with-hook-fail-turn-variant

Variant canary for `on_error: "fail_turn"` manifest-declared hooks.

The fixture installs a `:post_projection` hook named
`conformance.raise_hook_variant`. Conformant implementations resolve and
invoke the handler through the hook registry; fixture-aware implementations
that only special-case `conformance.raise_hook` fail this fixture.

Conformance-relevant properties checked by this fixture:

- Hook invocation failures are governed by `on_error`
- `fail_turn` appends `:runtime_error` with source, handler,
  exception class, message, and `terminal: true`
- Provider calls do not proceed after a fail-turn hook error
