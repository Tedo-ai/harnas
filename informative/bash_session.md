# bash_session Convention

This document is informative. It describes a candidate built-in tool for
sandboxed coding agents that want one shell-shaped capability instead of
separate descriptors for directory listing, globbing, grep, and one-shot
command execution.

The convention is intentionally not normative in v0.11. Process
lifecycle, sandboxing, and cross-platform shell behavior are subtle
enough that the shape should be proven by implementations before it is
required of every Harnas port.

## Motivation

The existing built-in tools `list_dir`, `glob`, `grep`, and `run_shell`
are useful because they are narrow and easy to reason about. In a
Unix-like sandbox, however, they also spend four tool descriptors on
capabilities a shell already provides.

`bash_session` is the denser shape for coding-agent sandboxes:

- one descriptor covers listing, globbing, grep, and command execution;
- a named session preserves working directory and environment variables
  across calls;
- non-zero exit codes are ordinary command results, not tool failures;
- long-running commands can be observed and killed by session id.

New sandboxed coding agents SHOULD prefer `bash_session` when they are
comfortable exposing shell access. The narrower tools remain appropriate
for hosted agents, restricted environments, or policies that want
separate permission decisions per capability.

## Tool Shape

```json
{
  "name": "bash_session",
  "handler": "harnas.builtin.bash_session",
  "description": "Run a command in a persistent bash session. Sessions preserve working directory and environment variables across calls. stdin is /dev/null; interactive programs cannot receive input.",
  "input_schema": {
    "type": "object",
    "properties": {
      "session_id": { "type": "string" },
      "command": { "type": "string" },
      "action": { "type": "string", "enum": ["run", "status", "kill"] },
      "timeout_ms": { "type": "integer", "minimum": 1 }
    }
  },
  "config": {
    "shell": "bash",
    "cwd": ".",
    "max_output_bytes": 65536
  }
}
```

`action` defaults to `"run"` when `command` is present.

The tool result is a JSON object encoded as a string, because
`:tool_result.payload.output` is currently a string in the Harnas Event
model:

```json
{
  "session_id": "string",
  "status": "completed",
  "exit_code": 0,
  "stdout": "...",
  "stderr": "...",
  "truncated": false
}
```

`exit_code` is `null` while a command is still running. `truncated` is
`true` when stdout or stderr exceeded `max_output_bytes`; implementations
SHOULD keep the tail and drop the head.

## Semantics

- Sessions are named. If `session_id` is omitted on `run`, the handler
  creates a new session and returns the generated id.
- Sessions preserve shell state within one agent run: `cd`, `export`,
  shell variables, and other shell-local state survive subsequent
  commands in the same session.
- Sessions do not share state with each other.
- Environment variables are inherited from the harness process when a
  session is created. Implementations SHOULD document how secrets enter
  that environment and SHOULD avoid inheriting more than the sandbox
  policy allows.
- stdin is not available to commands. Implementations SHOULD connect it
  to `/dev/null` or equivalent. Programs that require interactive input
  may exit on EOF or keep running until timeout.
- `timeout_ms` does not turn a running command into a tool error. It
  returns `status: "running"` with output captured so far.
- `status` returns the current output and status for an existing session.
- `kill` terminates the running command and its children. On Unix-like
  systems this SHOULD target the process group, not only the direct
  shell pid.
- Concurrent `run` calls for the same `session_id` SHOULD serialize.
- ANSI escape sequences SHOULD be stripped from captured output.
- Non-zero exit codes remain successful tool results with
  `status: "completed"` and the integer `exit_code`.

## Manifest Example

```json
{
  "name": "bash",
  "handler": "harnas.builtin.bash_session",
  "description": "Run commands in a persistent shell session",
  "input_schema": {
    "type": "object",
    "properties": {
      "session_id": { "type": "string" },
      "command": { "type": "string" },
      "action": { "type": "string", "enum": ["run", "status", "kill"] },
      "timeout_ms": { "type": "integer", "minimum": 1 }
    }
  },
  "config": {
    "shell": "bash",
    "cwd": ".",
    "max_output_bytes": 65536
  }
}
```

Agents exposing this tool SHOULD pair it with an appropriate permission
strategy for destructive operations. A shell is a broad capability; the
tool descriptor is compact, but the policy surface is not small.

## Interaction Examples

```text
user: list files here
assistant -> bash_session(command="ls -1")
tool_result: {"session_id":"sh_...","status":"completed","exit_code":0,"stdout":"README.md\nsrc\n","stderr":"","truncated":false}
assistant: README.md and src are present.
```

```text
assistant -> bash_session(session_id="sh_1", command="cd /tmp && export MYVAR=hello")
assistant -> bash_session(session_id="sh_1", command="echo $MYVAR && pwd")
tool_result: {"stdout":"hello\n/tmp\n", ...}
```

```text
assistant -> bash_session(session_id="sh_1", command="python -m http.server", timeout_ms=100)
tool_result: {"status":"running","exit_code":null, ...}
assistant -> bash_session(session_id="sh_1", action="status")
assistant -> bash_session(session_id="sh_1", action="kill")
```

## Open Questions Before Normative Promotion

- Whether `:tool_result.output` should remain a string containing JSON
  for structured tool outputs, or whether a future Event version should
  permit structured outputs directly.
- Whether the canonical name should stay `bash_session` or become the
  more accurate `shell_session` for implementations that fall back to
  `sh`.
- What minimum sandbox controls, environment filtering, and default
  permission gates are required before this should be a required
  built-in across all implementations.
