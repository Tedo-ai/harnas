# with-bash-session-basic

Exercises the normative `harnas.builtin.bash_session` run path.

The manifest exposes only `bash_session`, configured with a
fixture-local workspace. The provider calls `ls -1` and the second
OpenAI-shaped request asserts that the resulting `:tool_result` is
projected as `role: "tool"` with the original `tool_call_id`.

The fixed `session_id` keeps the byte-exact expected Log deterministic;
session creation without an explicit id remains implementation-defined.
