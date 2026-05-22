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
      "timeout_ms": { "type": "integer", "minimum": 1 },
      "env": {
        "type": "object",
        "additionalProperties": { "type": "string" }
      }
    }
  },
  "config": {
    "shell": "auto",
    "shell_type": "auto",
    "cwd": ".",
    "max_output_bytes": 65536
  }
}
```

`action` defaults to `"run"` when `command` is present.

For `run`, callers MAY pass an `env` object. These environment variables
apply only to that command and do not persist in the shell session. To
persist state, the agent should use ordinary shell commands such as
`export NAME=value`.

`bash_session` is not a PTY. It uses pipes, with stdin connected to
`/dev/null`. Full-screen TUIs, interactive password prompts, and
programs that require terminal control are out of scope for this tool.
A future PTY tool, if one is needed, should be a separate tool with its
own semantics.

## Portability

`bash_session` is intentionally NOT a PTY. It is a persistent shell
session with per-call `run`, `status`, and `kill` semantics. The
protocol is portable across operating systems; OS-specific details are
surfaced via configuration and capability fields.

### Normative Across All OSes

- The shell process persists across `run` calls within a `session_id`.
- Working directory and environment variables set in one `run` persist
  to subsequent runs in the same session.
- `run` returns stdout, stderr, exit_code, and status; `status` returns
  lifecycle state; `kill` terminates the session.
- `stdin` is `/dev/null` or the platform equivalent. Interactive
  programs are not supported.
- The `env` per-command field, when provided, scopes the env vars to
  that single command, not the session.

### OS-Specific Implementation Freedom

- **Default shell:** bash on Unix-like systems (Linux, macOS), `pwsh`,
  `powershell.exe`, or `cmd.exe` on Windows. Implementations SHOULD
  document their detection order and allow override via the `shell`
  config field.
- **Process cleanup:** implementations SHOULD kill the process group on
  Unix by signaling `-pgid`. On Windows, implementations SHOULD
  terminate the shell process; full process-tree cleanup is
  OS-version-dependent.
- **Command semantics:** agents MUST NOT assume POSIX shell semantics on
  Windows by default. The `shell_type` capability field exposes the
  active shell family so the agent can adapt.

### The `shell_type` Capability Field

The `bash_session` tool's `config` map MUST include `shell_type` with
one of: `posix` (bash, sh, zsh, etc.), `powershell` (`pwsh`,
`powershell.exe`), or `cmd` (`cmd.exe`). Manifests MAY use
`shell_type: "auto"` to ask the runtime to resolve the value from the
active shell. Implementations SHOULD detect this from the resolved shell
at session start and surface it in the tool descriptor's effective
config.

Agents should use `shell_type` to adapt command syntax: POSIX shells
expect `ls`, `grep`, `cd`, and `find`; PowerShell expects
`Get-ChildItem`, `Select-String`, `Set-Location`, and
`Get-ChildItem -Recurse`.

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
  "command_stdout": "...",
  "command_stderr": "...",
  "truncated": false
}
```

`stdout` and `stderr` are cumulative for the shell session. They let an
agent inspect the whole transcript so far, but can become noisy in long
runs. `command_stdout` and `command_stderr` contain only the output
produced since the current command started. Agents SHOULD prefer the
command-local fields for ordinary reasoning, and use the cumulative
fields when they need session history.

`exit_code` is `null` while a command is still running. `truncated` is
`true` when stdout or stderr exceeded `max_output_bytes`; implementations
SHOULD keep the tail and drop the head. If truncation drops content from
before the current command, `command_stdout` and `command_stderr` can
still be complete. If truncation drops content produced by the current
command, the command-local fields also contain only the retained tail.

## Sentinel Format

Reference implementations delimit command completion with stdout and
stderr sentinels generated inside the persistent shell. The framing is:

```sh
{ <command>
} </dev/null; __harnas_status=$?; printf '__HARNAS_ERR_DONE_<token>\n' >&2; printf '__HARNAS_DONE_<token>:%s\n' "$__harnas_status"
```

The stdout sentinel is `__HARNAS_DONE_<token>:<exit_code>\n`. The stderr
sentinel is `__HARNAS_ERR_DONE_<token>\n`. The `<token>` is an
implementation-generated opaque identifier scoped to one command.

Implementations strip the sentinel markers from returned output. Text
before a sentinel on the same line remains command output. This format
is an implementation convention for the reference built-ins, not a Log
event shape.

## Semantics

- Sessions are named. If `session_id` is omitted on `run`, the handler
  creates a new session and returns the generated id.
- Sessions preserve shell state within one agent run: `cd`, `export`,
  shell variables, and other shell-local state survive subsequent
  commands in the same session.
- Sessions do not share state with each other.
- `bash_session` is arbitrary shell execution. It is not a read-only
  inspection tool and should not be described as one. If an application
  allows a command, the command's filesystem, process, and network side
  effects are allowed. Command approval, YOLO modes, improvement flows,
  and other policy choices live at the application layer.
- The configured working directory is a starting directory, not a
  sandbox boundary. Implementations MAY run inside an external sandbox,
  but this tool by itself does not confine commands to `cwd`.
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
- Background jobs started by a completed shell command, such as
  `sleep 30 &`, are shell-managed. Once the top-level command completes,
  `bash_session.status` reports the shell as ready for the next command;
  the agent must use ordinary shell commands such as `jobs`, `ps`, or
  `kill` to inspect and manage those background jobs.
- Concurrent `run` calls for the same `session_id` SHOULD serialize.
- ANSI escape sequences SHOULD be stripped from captured output.
- Non-zero exit codes remain successful tool results with
  `status: "completed"` and the integer `exit_code`.

## Agent Usage Guidance

Agents using this tool SHOULD:

- reuse a stable `session_id` for related work so `cd`, environment
  variables, and shell history remain useful;
- run `pwd` after `cd` when location matters;
- prefer non-interactive commands, because stdin is unavailable;
- use `timeout_ms` for commands that may run for a long time;
- call `status` for a top-level command that returned
  `status: "running"`;
- call `kill` when a top-level command should be stopped;
- state destructive intent plainly instead of hiding it inside a large
  compound command.

These are usability guidelines, not security guarantees. The application
decides whether the command is allowed before dispatch.

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
      "timeout_ms": { "type": "integer", "minimum": 1 },
      "env": {
        "type": "object",
        "additionalProperties": { "type": "string" }
      }
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
tool_result: {"session_id":"sh_...","status":"completed","exit_code":0,"stdout":"README.md\nsrc\n","stderr":"","command_stdout":"README.md\nsrc\n","command_stderr":"","truncated":false}
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

```text
assistant -> bash_session(session_id="sh_1", command="touch foo.txt")
tool_result: {"status":"completed","exit_code":0,"command_stdout":"","command_stderr":"","...":"..."}
```

The `touch` command changes the filesystem because the application
allowed shell execution. A product that wants human review for such
commands should gate `bash_session` calls before dispatch.

## Open Questions Before Normative Promotion

- Whether `:tool_result.output` should remain a string containing JSON
  for structured tool outputs, or whether a future Event version should
  permit structured outputs directly.
- Whether the canonical name should stay `bash_session` or become the
  more accurate `shell_session` for implementations that fall back to
  `sh`.
- Whether the cumulative transcript should remain in `stdout` /
  `stderr`, move to explicitly named transcript fields, or be made
  configurable per application.
- What language-neutral permission guidance is sufficient before this
  should be a required built-in across all implementations.
