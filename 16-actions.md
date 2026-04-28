# 16 — Actions

This document specifies **Actions**: the canonical primitive
effects a Hook Handler produces. Actions are the write-side
complement to Hooks' read-side attachment points — together they
form the vocabulary that Strategies compose.

## The composite model

Harnas's strategy layer decomposes into three concepts:

| Concept | Role | Ownership |
|---|---|---|
| **Hook** (see `14-hooks.md`) | attachment point: where a handler can run | Harnas core |
| **Action** (this spec) | named discrete effect: what a handler can produce | Harnas core |
| **Strategy** | named composite: `(hook registrations × predicate logic × actions)` | strategy catalog (`spec/strategies/`) |

A strategy is a composition of Hooks + Actions. It is not itself a
code primitive — it's a documented pattern. Actions ARE code
primitives, small and named.

## Canonical Actions

**R1.** A Harnas implementation MUST expose the following canonical
Actions. Additional Actions MAY be added; consumers MUST ignore
unknown Actions.

| Action | Signature (conceptual) | What it does |
|---|---|---|
| `Compact` | `(session, replaces:, summary:)` → Event | Appends a `:compact` Mutation Event |
| `Revert` | `(session, revokes:)` → Event | Appends a `:revert` Mutation Event |
| `Refuse` | `(reason:)` → decision Hash | Returns `{ allow: false, reason: ... }` for decision-style Hooks |
| `Allow` | `()` → decision Hash | Returns `{ allow: true }` for decision-style Hooks |

## Action Contract

**R2.** Each Action MUST be a pure, named callable. Its inputs are
defined by its signature; its output is either:

- a Log mutation (appended Event, returned to caller), or
- a Hook return value (a decision Hash or similar structured data).

**R3.** Actions MUST be side-effect-local: the only Log they mutate
is the one explicitly passed as `session`. They MUST NOT register
Hooks, emit Observation events, or modify global state.

**R4.** Actions MUST validate their inputs via the corresponding
Event payload type's existing validation (for mutation Actions) or
at construction (for decision Actions). Invalid inputs MUST raise
`ArgumentError` before any side effect occurs.

## Why Actions exist as a named layer

[informative]

Without a named Actions layer, every Strategy's hook handler would
hand-roll its own `session.log.append(type: :compact, payload: ...)`
boilerplate. That creates drift:

- Each Strategy's ToolPair-orphan handling differs.
- Each Strategy's input validation differs.
- Cross-language implementers have nothing named to port.
- Benchmarks can't ask "does this Strategy use the Compact Action?"
  because Compact isn't a thing.

With Actions as a named layer, strategies become **compositions
that name what they do**. `MarkerTail` is "at `:pre_projection`, when
message count exceeds threshold, apply `Compact` with tool-pair
safety." That description maps 1:1 to the code.

## Strategy spec stubs carry a "Composed of" section

[informative]

Every strategy spec stub (under `spec/strategies/<family>/<name>.md`)
declares its composition using the vocabulary from this document:

```markdown
## Composed of
- Hook: :pre_projection
- Predicate: message count > max_messages
- Action: Compact (with Helpers.tool_pair_safe_range safety)
```

Cross-strategy comparability follows directly: "which Action(s)
does this strategy use?" is a meaningful, answerable question
across the whole catalog.

## Versioning Note

**R5.** The canonical Action set (R1) and each Action's signature
are stable within a major spec version. New Actions MAY be added;
existing Actions' signatures MUST NOT change without a major spec
version bump.
