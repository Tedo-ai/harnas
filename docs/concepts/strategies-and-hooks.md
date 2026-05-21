# Strategies and Hooks

Strategies and hooks are how Harnas extends the agent loop without changing
the spec. They intercept the loop at well-defined points, enforce policy,
or emit observations.

## Hooks

A **hook** is a callback registered against a lifecycle event. The agent
loop emits these events at specific points; registered handlers run
synchronously and can refuse, mutate, or augment the action being taken.

The current hook points:

- `pre_tool_use` — fires after the assistant has emitted a `tool_use` event
  but before the tool runs. Handlers can refuse the call (returning a
  `tool_result` with an error), mutate the arguments (with care), or emit
  annotations.
- `post_tool_use` — fires after a tool returns, before the result is
  appended to the Log. Handlers can observe but not mutate the result.
- `pre_turn` — fires before the next provider request is built. Handlers
  can refuse the turn (timeout, budget exceeded, health check failed).
- `on_error` — fires when the harness encounters a runtime error. Handlers
  decide whether to retry, escalate, or surface the error.

Hooks are the mechanism. Strategies are the patterns that use them.

## Strategies

A **strategy** is a named, configurable bundle of hook handlers that
implements a specific policy. Strategies are declared in the manifest and
take effect for the session.

The currently-shipped strategies:

- `sandbox/write` — blocks `write_file` and `edit_file` calls to paths
  outside an allowlist. Deny wins over allow.
- `sandbox/network` — blocks `fetch_url` calls to hosts outside an
  allowlist. Same allow/deny semantics.
- `guard/timeout` — refuses the next turn if wall-clock time exceeds a
  threshold. Emits a `runtime_error` and exits cleanly.
- `guard/repetition` — detects consecutive tool failures or identical
  repeated calls (now also: repeated approval rejections). Refuses to
  proceed past a configured threshold.
- `guard/cost_budget` — checks accumulated token usage before each provider
  call; refuses if the next call would exceed configured token limits.
- `guard/health` — runs a configurable shell command before each turn; if
  the command exits non-zero, refuses the turn and surfaces the failure to
  the agent.
- `credential/proxy` — injects credentials into tool calls (e.g., auth
  headers for `fetch_url`) without persisting values in the Log.

Strategies compose. A manifest can declare any combination; they all
register their handlers and run in declaration order at each hook point.

## How they show up in the Log

Strategy decisions are observable. When `sandbox/write` blocks a path, the
`tool_result` event carries a clear error explaining why. When
`guard/timeout` fires, a `runtime_error` event records the reason.
Replaying a session always shows you what strategies did and why.

Strategies that don't reject a call leave no Log trace by default. Some
emit `annotation` events for visibility (e.g., `credential/proxy` annotates
which credentials were injected, by name).

## When to write your own strategy

You write a strategy when:

- You're enforcing a policy across multiple agent sessions (a sandbox, an
  auth pattern, a circuit breaker).
- The policy is independent of any specific tool — it's lifecycle, not
  tool implementation.
- You want the policy to be declarable in a manifest rather than baked
  into product code.

You DON'T write a strategy when:

- The policy is specific to one tool — that's better expressed inside the
  tool's handler.
- The policy is about session metadata or user identity — those belong in
  your product layer above Harnas.

## What hooks and strategies are not

- They don't replace the provider. The provider decides what the assistant
  says; strategies decide whether to let actions happen.
- They don't replace tools. A strategy intercepts a tool call; it doesn't
  implement one.
- They don't mutate the Log retroactively. Strategies emit new events;
  they never modify old ones.

## See also

- [Sandboxes](./sandboxes.md) — the `sandbox/*` strategy family in detail
- [`informative/conformance-process.md`](../../informative/conformance-process.md) — how new strategies enter the spec
- [Tools and built-ins](./tools-and-built-ins.md) — the actions strategies intercept
