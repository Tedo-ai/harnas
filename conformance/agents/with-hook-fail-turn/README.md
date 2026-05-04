# with-hook-fail-turn

Exercises `on_error: "fail_turn"` for manifest-declared hooks.

The fixture installs a `:post_projection` hook that raises during
invocation. Because the hook declares `fail_turn`, the runtime aborts
the turn and appends a terminal `:runtime_error` event instead of
calling the provider.

Conformance-relevant properties checked by this fixture:

- Hook invocation failures are governed by `on_error`
- `fail_turn` appends `:runtime_error` with source, handler,
  exception class, message, and `terminal: true`
- Provider calls do not proceed after a fail-turn hook error
