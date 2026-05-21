# Tools and Built-ins

A **tool** is a named action the agent can invoke. The manifest declares
which tools are available; the agent calls them by name; the runtime
dispatches to a registered handler that runs the action and returns a
result.

## What a tool descriptor looks like

```json
{
  "name": "fetch_story",
  "description": "Fetch story context by UID",
  "input_schema": {
    "type": "object",
    "properties": { "uid": { "type": "string" } },
    "required": ["uid"]
  },
  "handler": "harnas.builtin.fetch_url"
}
```

The agent sees `name`, `description`, and `input_schema` — that's what
goes into the provider request as the tool definition. The `handler`
field tells the runtime which function to dispatch to.

## Built-in tools

Harnas ships six built-in tools across all four implementations:

| Tool | What it does |
|---|---|
| `read_file` | Read a file with optional `offset` and `limit`, returns cat -n formatted output |
| `write_file` | Write (overwrite) a file at a path, respecting `sandbox/write` |
| `edit_file` | Exact string replacement in an existing file |
| `bash_session` | Run commands in a persistent shell with `cwd` and env preserved across calls |
| `fetch_url` | HTTP GET (and POST via headers), respecting `sandbox/network` |
| `load_skill` | Load a named skill's body from the skills directory |

That's the entire built-in catalog. No `list_dir` separately (use
`bash_session` with `ls`). No `grep` separately (use `bash_session`). No
shell-specific tools beyond `bash_session` itself. The catalog is
deliberately small.

## "Earn your descriptor"

Every built-in tool earned its place by passing two tests:

1. **Is it something agents demonstrably need across many use cases?**
   File reading, file editing, shell access, web fetching — yes. Skill
   loading — yes, given how many products need lightweight context
   loading.

2. **Can shell commands reasonably replace it?** If yes, it doesn't get
   to be a built-in. `list_dir` could be `bash_session("ls -la")`. `grep`
   could be `bash_session("rg pattern")`. `run_shell` (one-shot) is
   already mostly subsumed by `bash_session`.

Every tool descriptor costs context-window space in the provider request.
Every built-in is also a permanent maintenance commitment across four
implementations. The bar for adding one is higher than the bar for
keeping it out.

## Custom tools

The interesting tools for any real product are the ones you write
yourself. The editorial Rails pipeline has tools like `fetch_story`,
`create_organization_listing`, `generate_article` — all backed by
ActiveRecord and Rails services. AgentStaple has `propose_edit`,
`inspect_shell`, the `self` introspection tool. None of these are
substrate concerns.

You register a tool by:

1. Declaring it in the manifest (`name`, `description`, `input_schema`).
2. Providing a handler — a Ruby lambda, a Go function, a Python callable
   — that takes the parsed arguments and returns a string result (or an
   error).

The runtime takes care of dispatch, serialization, error wrapping, and
appending `tool_use` and `tool_result` events to the Log.

## Tool handlers

Modern Harnas tool handlers take two arguments: the parsed call
arguments, and the tool's `config` map from the manifest descriptor.
Most handlers ignore `config`; some (like the MCP passthrough handler,
or product-specific configurable tools) use it heavily.

Backward compatibility: handlers that only accept `args` still work.
Implementations detect the signature and dispatch accordingly.

## Tool result shape

A tool returns a string or raises an error. The runtime wraps either
into a `tool_result` event:

```json
{
  "event_type": "tool_result",
  "payload": {
    "tool_use_id": "call_4",
    "output": "ok",
    "error": null
  }
}
```

On error: `output` is empty, `error` is the message. The agent sees the
error; how it reacts is its decision (retry, ask the user, give up).

Tool errors are NOT thrown exceptions in the agent loop. They're values
in the Log. This is intentional — the Log captures what happened,
including what failed, without forcing the runtime into branching error
flows.

## What tools are not

- Not lifecycle hooks (those are [strategies and hooks](./strategies-and-hooks.md)).
- Not workflows (those are agent prompts plus tools).
- Not memory (tools have no persistent state across calls except via
  external systems they touch).

## See also

- [Strategies and Hooks](./strategies-and-hooks.md) — for policy that
  intercepts tool calls
- [MCP](./mcp.md) — for tools hosted outside the agent process
- [Sandboxes](./sandboxes.md) — for path and network restrictions on
  built-in tools
