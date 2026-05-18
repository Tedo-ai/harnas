# with-session-timeout

Verifies that `guard/timeout` can stop a session before a provider
call. The fixture uses `timeout_seconds: 0` as a deterministic sentinel:
the first check is allowed through, and the second check emits a
terminal `runtime_error`.
