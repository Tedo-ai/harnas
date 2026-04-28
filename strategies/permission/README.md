# Permission Strategies

This directory is the **strategy catalog** for the permission family.
Each strategy is one short Markdown stub declaring its purpose,
configuration surface, arbitrary choices, and composed-of shape.
The implementation for each is plain Ruby — not a framework — living
under `reference/lib/harnas/strategies/permission/<name>.rb`.

The family contract (R1–R5 — what every permission strategy MUST
honor regardless of its implementation) is specified once in
[`../../07-permission.md`](../../07-permission.md). This README is
family-level documentation about *how permission strategies are
written*, so authors can follow the pattern and cross-language
implementers can port the catalog faithfully.

## Catalog

| Strategy | Decision basis | Blocking? | Spec |
|---|---|---|---|
| AlwaysAllow | unconditional | never | [always-allow.md](always-allow.md) |
| DenyByName | tool name in configured deny-list | for listed names | [deny-by-name.md](deny-by-name.md) |
| HumanApproval | user-supplied callable | per user's choice | [human-approval.md](human-approval.md) |

## How permission strategies are written

A permission strategy is plain Ruby that installs as a
`:pre_tool_use` hook handler and returns a decision Hash produced by
`Actions::Allow` or `Actions::Refuse`. That's the entire contract.
Everything else — deny-list lookup, user prompt, classifier call,
sandbox probe — is the strategy's own code.

Reference strategies in this catalog follow a common pattern for
readability:

```ruby
class MyStrategy
  def self.install(**config)
    new(**config).install
  end

  def initialize(**config)
    # validate config
  end

  def install
    handler = method(:on_pre_tool_use)
    Harnas::Hooks.on(:pre_tool_use, handler)
    handler
  end

  def on_pre_tool_use(tool_use:, **_)
    if my_predicate?(tool_use)
      Harnas::Actions::Allow.call
    else
      Harnas::Actions::Refuse.call(reason: "<why>")
    end
  end
end
```

Authors return `Actions::Allow.call` / `Actions::Refuse.call` rather
than hand-rolling the decision Hash — the Actions are the family's
canonical vocabulary (see [`../../16-actions.md`](../../16-actions.md)).

## Composition (any-deny-wins)

Multiple permission strategies can install on `:pre_tool_use`
simultaneously. The AgentLoop invokes them all and applies
**any-deny-wins** (normative; see R6 of
[`../../14-hooks.md`](../../14-hooks.md) and R4 of
[`../../07-permission.md`](../../07-permission.md)): if any handler
returns `{ allow: false, reason: ... }`, the tool call is skipped
and that handler's reason is carried into the resulting
`:tool_result`.

This composition rule means strategies don't need to know about each
other. A benchmark run can stack `DenyByName` + `HumanApproval` and
the allow-set is the intersection; denials are union.

## Spec stub template

Every strategy's spec stub lives next to this README and looks like:

```markdown
# <StrategyName>

**Family:** Permission

**Purpose:** <one sentence>

## Composed of
- **Hook:** `:pre_tool_use`
- **Predicate:** <exact condition>
- **Action:** `Actions::Allow` or `Actions::Refuse` with `reason: "..."`

## Configuration
- `<param>:` <type>, default <value>

## Arbitrary choices
- <choice 1>
- <choice 2>

## When to use
<one paragraph>

## When NOT to use
<one paragraph>
```

When adding a new permission strategy, fill in the template,
implement the Ruby, add tests. The arbitrary choices line-by-line
comparison between strategies is the value the catalog provides.

## Out of scope for this README

- **R1–R5 family contract** — lives in [`../../07-permission.md`](../../07-permission.md).
- **Action catalog** — lives in [`../../16-actions.md`](../../16-actions.md).
- **Hook mechanism** — lives in [`../../14-hooks.md`](../../14-hooks.md).
