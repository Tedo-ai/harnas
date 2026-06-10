# streaming-malformed-frame

Exercises malformed streaming frame semantics. A scripted stream emits a
partial text delta, then simulates a malformed provider frame. The runtime
must emit stream failure on Observation, append a terminal
`:provider_error`, and must not append a consolidated assistant message.

The provider error message includes the provider kind and a bounded,
sanitized frame preview. The bad frame itself is not preserved as durable
Log data.
