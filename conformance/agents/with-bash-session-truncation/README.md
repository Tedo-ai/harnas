# with-bash-session-truncation

Exercises output truncation for `bash_session`.

The fixture sets `max_output_bytes` to 10 and runs a command that emits
more than 10 bytes. The result must be a successful tool result with
`truncated: true`; truncation is not a tool error.
