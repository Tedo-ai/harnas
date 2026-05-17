# with-bash-session-timeout

Exercises timeout and kill semantics for `bash_session`.

A timed run of `sleep 60` must return a successful tool result whose
JSON output has `status: "running"` and `exit_code: null`. A follow-up
`kill` action for the same session must return `status: "killed"`.
