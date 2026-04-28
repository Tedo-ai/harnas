# AlwaysAllow

**Family:** Permission

**Purpose:** Permission baseline. Allows every `:tool_use`
unconditionally. Useful as a benchmark baseline and as an explicit
"I'm choosing to allow all" rather than relying on the no-handler
default.

## Composed of

- **Hook:** `:pre_tool_use`
- **Predicate:** *(none — always fires)*
- **Action:** `Actions::Allow`

## Algorithm (normative)

```
algorithm AlwaysAllow():

  install handler at hook :pre_tool_use

  on :pre_tool_use(tool_use):
    return Actions.Allow()     # { allow: true }
```

No configuration, no predicate, no normative strings. The algorithm
is complete as written.

## Configuration

*(none)*

## Arbitrary choices

- **Predicate:** unconditional. There is no inspection of the
  `tool_use` payload at all.
- **Composition:** designed to compose cleanly under any-deny-wins
  (R6 of `14-hooks.md`). Stacking AlwaysAllow with DenyByName is
  equivalent to just DenyByName, because Refuse decisions win.
- **Audit visibility:** an installed AlwaysAllow makes the permission
  decision *explicit* in the Hooks registry. Inspection tools can
  surface "permission strategy: AlwaysAllow" rather than "no handler
  installed."

## When to use

- Local development, scripting, and CI fixtures where every tool is
  trusted.
- Baseline runs in the benchmark harness, so other permission
  strategies have a no-op comparator.
- Documenting in code that the permission decision was made
  deliberately, not by omission.

## When NOT to use

- Anything user-facing. Production surfaces should always install at
  least one substantive permission strategy (DenyByName,
  HumanApproval, classifier-gated, sandbox-gated, …).

## Implementation

`reference/lib/harnas/strategies/permission/always_allow.rb` — plain
Ruby, ~15 lines.
