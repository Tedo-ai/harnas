# HumanApproval

**Family:** Permission

**Purpose:** Ask a user-supplied callable whether to allow each
`:tool_use`. The callable is the strategy; this class is the thin
wrapper that conforms it to the `:pre_tool_use` Hook contract.

## Composed of

- **Hook:** `:pre_tool_use`
- **Predicate:** the user-supplied `prompt` callable returns truthy
  when called with the `:tool_use` Event
- **Action:** `Actions::Allow` when truthy, otherwise
  `Actions::Refuse(reason: denial_reason)`

## Algorithm (normative)

```
algorithm HumanApproval(prompt,
                        denial_reason = "human declined"):

  REQUIRES: prompt is callable with signature (tool_use) -> truthy/falsy
            [R3 exception per spec/17-composition-rules.md: prompt
             reaches an external system — a human — so a callable
             parameter is permitted here]

  install handler at hook :pre_tool_use

  on :pre_tool_use(tool_use):
    if prompt(tool_use):
      return Actions.Allow()
    else:
      return Actions.Refuse(reason: denial_reason)
```

**Normative defaults:**

- `denial_reason`: the literal string `human declined`. This string
  surfaces in the `:tool_result` that goes back to the model, so
  every conformant implementation produces the same model-facing
  text by default.

## Configuration

| Parameter | Type | Default | Description |
|---|---|---|---|
| `prompt:` | callable (`#call(tool_use) -> truthy/falsy`) | *(required)* | Decides per tool_use |
| `denial_reason` | String | `human declined` | Reason surfaced on refuse |

The constructor raises `ArgumentError` when `prompt` does not respond
to `#call`.

## Arbitrary choices

- **Synchronous:** the strategy calls `prompt.call(tool_use)`
  inline. The Hook invocation blocks until the callable returns. For
  CLI/TUI surfaces this is the right shape; for non-interactive
  surfaces (web, server) the callable should resolve quickly or the
  strategy should be replaced with an async-friendly variant.
- **Tool_use is passed in full:** the callable receives the full
  `:tool_use` Event (with `payload[:name]`, `payload[:arguments]`,
  `payload[:id]`). The callable can inspect arguments — argument
  awareness is delegated, not built in.
- **Default reason text:** denials carry `reason: "human declined"`.
  The reason text is fixed; it does not include arguments or other
  context. Variants that want richer reasons can wrap or replace the
  strategy.
- **No memory:** approvals are per-call; there is no "approve once,
  remember for session" behavior. Persistent allow-lists are a
  separate strategy (would compose with HumanApproval via
  any-deny-wins).
- **Callback-is-the-predicate:** because the predicate lives in the
  caller's lambda, this is a very thin wrapper. That's deliberate:
  the human is the strategy.

## When to use

- Interactive CLI / TUI sessions where a human is present and tool
  calls should be vetted one at a time.
- Demos and code-review-style sessions.
- Layered with DenyByName (any-deny-wins): coarse-deny first, ask
  about everything else.

## When NOT to use

- Server-side or autonomous runs where no human is available to
  answer the prompt.
- Latency-sensitive flows where blocking on a human read would break
  the SLA.

## Example

```ruby
Harnas::Strategies::Permission::HumanApproval.install(
  prompt: ->(tu) {
    print "Allow tool #{tu.payload[:name]}? [y/N] "
    $stdin.gets.chomp.downcase == "y"
  }
)
```

## Implementation

`reference/lib/harnas/strategies/permission/human_approval.rb` —
plain Ruby, ~30 lines.
