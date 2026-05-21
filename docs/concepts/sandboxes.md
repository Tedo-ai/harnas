# Sandboxes

Harnas ships two sandbox strategies: `sandbox/write` (path-scoped writes)
and `sandbox/network` (host-scoped HTTP). They share the same shape and
the same critical limitation.

## What they are

Sandboxes are tool-boundary guards. They sit at the `pre_tool_use` hook
point and check tool calls against configurable allow/deny lists before
the tool runs. If a call is denied, the tool sees a refusal; the
underlying action never happens.

### `sandbox/write`

Checks `write_file` and `edit_file` calls against allow/deny path lists.

```json
{
  "strategy": "sandbox/write",
  "config": {
    "allow": ["./workspace"],
    "deny":  ["./workspace/secrets", "/etc", "/usr"]
  }
}
```

- Deny wins over allow. A path matching anything in `deny` is refused,
  even if it also matches `allow`.
- Paths are prefix-matched and normalized. `./workspace/secrets` blocks
  `./workspace/secrets/key.pem`.
- Defaults: `allow: ["."]`, `deny: []`.

### `sandbox/network`

Checks `fetch_url` calls against allow/deny host lists.

```json
{
  "strategy": "sandbox/network",
  "config": {
    "allow": ["api.github.com", "api.openai.com"],
    "deny":  []
  }
}
```

- Same allow/deny semantics. Deny wins.
- Hosts are matched exactly. Subdomain matching is opt-in via a future
  field; v0.14 does not include it.
- Default: no allow list = block all outbound HTTP.

## How violations show up

When a sandbox refuses a call, the `tool_result` event carries a clear
error message naming what was blocked:

```json
{
  "event_type": "tool_result",
  "payload": {
    "tool_use_id": "call_4",
    "output": "",
    "error": "Write to './workspace/secrets/key.pem' is not permitted. Allowed paths: ['./workspace']. Denied paths: ['./workspace/secrets']."
  }
}
```

The agent sees the error in its tool result. It can choose a different
path, ask the user, or give up. The strategy does not silently fail; the
agent is informed.

After 3 consecutive sandbox violations of the same type, the strategy
escalates: it emits a `runtime_error` event and exits the agent with
code 4 (sandbox violation). This prevents agents from spinning forever
on a blocked operation.

## The critical limitation

> Sandboxes are tool-boundary guards inside the agent process. They are
> not OS-level isolation.

`sandbox/write` blocks `write_file` and `edit_file`. It does NOT block
shell commands inside `bash_session` or `run_shell` from writing
anywhere the agent process can write. If the agent runs `bash_session`
with `command: "cp secrets.txt /tmp/"`, that copy happens; `sandbox/write`
is not in the path.

`sandbox/network` blocks `fetch_url`. It does NOT block shell commands
from making network connections. `bash_session` with `command: "curl
evil.example.com"` reaches evil.example.com freely.

This is by design. The substrate has no OS-level visibility into shell
commands. For real isolation — guaranteeing that an agent cannot write
outside a directory or reach the internet regardless of which tool it
uses — run the agent inside a container, network namespace, or chroot.
See [`informative/isolation.md`](../../informative/isolation.md) for
production patterns.

## When tool-boundary guards are enough

For many use cases, they are:

- **Trusted-agent contexts.** The agent is your own product code, the
  tools are the only paths to side effects, and you control the tool
  surface.
- **Defense in depth.** OS-level isolation handles the worst case;
  sandbox strategies catch routine mistakes (the agent tries to write to
  the wrong path) without escalating to the OS layer.
- **Development and CI.** Where containers may be overkill but you still
  want clear refusals when the agent tries to do something outside its
  scope.

## When you need real isolation

For production deployments where the agent's shell access could be
weaponized — multi-tenant systems, untrusted prompts, sensitive data on
the host — the substrate-level sandboxes are not sufficient. Run inside
a container or namespace.

## See also

- [`informative/isolation.md`](../../informative/isolation.md) — OS-level isolation patterns
- [Strategies and Hooks](./strategies-and-hooks.md) — how strategies plug
  into the lifecycle
- [Credential proxy](./strategies-and-hooks.md) — the third member of the
  policy-at-tool-boundary family
