# 07 — Permission

This document specifies **permission** as a category of Strategy.
A permission strategy decides, per tool_use, whether the Runner
should execute it or record a failure result. Permission strategies
compose around the `:pre_tool_use` Hook (see `14-hooks.md`) and the
`Actions::Allow` / `Actions::Refuse` Actions (see `16-actions.md`).

## Position in the Stack

[informative]

Permission is a decision-returning concern, not a mutation-producing
one. Handlers at `:pre_tool_use` return decision Hashes; the
AgentLoop's any-deny-wins composition (R6 of `14-hooks.md`) converts
those returns into control flow. If any handler returns
`{ allow: false, reason: ... }`, the Runner skips the tool and
appends a failure `:tool_result` carrying the reason.

## Contract

**R1.** A permission strategy MUST install at the `:pre_tool_use`
Hook Point and MUST return a value produced by `Actions::Allow` or
`Actions::Refuse` (or return nil to abstain). Returning any other
shape is undefined behavior.

**R2.** A permission strategy MUST NOT mutate the Session's Log.
Side-effectful behavior (appending a `:tool_result`, recording
audit) is the AgentLoop's responsibility based on the composed
decisions.

**R3.** A permission strategy SHOULD treat the `:tool_use` payload
as advisory input, not as a contract. Providers may rename fields
across spec versions; strategies that match on `name` or inspect
`arguments` MUST tolerate unknown fields.

**R4.** When multiple permission strategies register at
`:pre_tool_use`, the AgentLoop composes their returns via
any-deny-wins: any `{ allow: false }` from any handler causes the
tool call to be skipped, with that handler's `reason` carried to
the resulting `:tool_result`. This composition is normative; a
compliant implementation MUST NOT require strategies to coordinate
among themselves.

**R5.** A permission Strategy MUST honor the composition rules in
[`17-composition-rules.md`](17-composition-rules.md). In particular,
it MUST be implementable using only the atomic operations
enumerated in R2 of that document. The external-world-callable
exception (R3 of `17-composition-rules.md`) DOES apply to the
permission family: because the canonical use case (`HumanApproval`)
reaches to a human, permission strategies MAY accept a callable
parameter whose purpose is to interact with an external system
(human, filesystem, non-Provider network). Callables for
harness-internal work remain forbidden.

## Canonical Strategies

[informative]

The reference implementation ships three permission strategies:

| Strategy | Decision basis | Blocking? |
|---|---|---|
| `AlwaysAllow` | unconditional | never |
| `DenyByName` | tool name in configured deny-list | for listed names |
| `HumanApproval` | user-supplied callable | per user's choice |

Other production strategies (Codex's Guardian Agent, classifier-gated
LLM review, sandbox-execution gating, multi-tier approval chains)
are additional implementations an installation MAY provide. This
specification does not mandate any particular strategy; it only
specifies the contract every permission strategy MUST honor (R1–R4)
and the composition rule (any-deny-wins).

## Installation Pattern

[informative]

```ruby
Harnas::Strategies::Permission::AlwaysAllow.install
Harnas::Strategies::Permission::DenyByName.install(names: %w[shell rm])
Harnas::Strategies::Permission::HumanApproval.install(
  prompt: ->(tool_use) { ask_user("allow #{tool_use.payload[:name]}?") }
)
```

Multiple strategies can stack. The AgentLoop invokes them all at
`:pre_tool_use` and applies any-deny-wins.

## Observation Integration

[informative]

Permission strategies are observable through:

- `:tool_invoked` (emitted by the Runner) with `outcome: :error`
  when a tool was denied.
- The `:tool_result` Event appended by the AgentLoop carries
  `error: "denied by hook: <reason>"`.

A benchmark subscriber can count denials by strategy, compare
false-positive rates, and measure the latency cost of human prompts
vs classifier checks vs lookup-based strategies.

## Versioning Note

**R6.** The permission contract (R1–R5) and the composition rule
are stable within a major spec version. New canonical Actions for
decision-style hooks MAY be added; existing signatures are stable.
