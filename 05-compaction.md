# 05 — Compaction

This document specifies **compaction** as a category of Strategy
(see `14-hooks.md`). A compaction strategy decides *when* and *what*
to compact; it expresses its decisions by appending `:compact`
Mutation Events (defined in `01-overview.md` R4 and demonstrated in
Phase F of the reference implementation) to the Session's Log.

## Compaction is editorial, not performance

[informative]

Framing matters. Compaction is often described as a size/cost
problem: the context window is full, some messages have to go. That
framing misses the point. Which messages go — and which survive —
is not a performance question. It is an **editorial** one. A
compaction strategy decides *what the agent remembers*.

MarkerTail, TokenMarkerTail, SummaryTail, and future retrieval-
or state-document-based strategies differ not in how much they
save but in *what they preserve*:

| Strategy | What survives | What it loses |
|---|---|---|
| MarkerTail / TokenMarkerTail (marker-replaced families) | recency | origin task, earlier decisions |
| SummaryTail (summarization family) | gist | sharp details, exact quotes |
| (reserved) RelevanceWindow | relevance | narrative flow |
| (reserved) DocumentFold | deliberately-written explicit state | all reasoning traces |

Every compaction strategy fails when its editorial choice is wrong
for the scenario: a tail-with-marker agent that "hallucinates" the
origin task is really an agent whose first turn was dropped; a
tail-with-summary agent that "fabricates" an error message is
really an agent whose summarizer filled in a plausible-looking
blank. See each strategy's spec stub for its specific failure
modes.

This spec mandates visualizing compaction outcomes in the
strategy-stub "Visualization" section (see
`spec/strategies/compaction/README.md` §"Visualization convention"):
a block-strip diagram where each row is a strategy and each block
is an event, block width proportional to tokens, color keyed to
event type, faded blocks shown in-position where compaction dropped
them. Two strategies that produce visually similar block-strips on
the same Log behave similarly; two that diverge editorially produce
visibly different strips. If a compaction strategy's output cannot
be drawn on a strip of message blocks, the strategy probably fights
another strategy or hides a second decision inside itself.

## Position in the Stack

[informative]

Compaction is not a primitive in Harnas. It is a **Strategy family**
— a set of hook-handler packs that register at canonical lifecycle
points to observe pressure signals (message count, token count,
cost, latency) and react by appending `:compact` Events. The Log
and Projections machinery do not know that compaction exists;
they just honor `:compact` Mutation Events when they encounter them.

## Contract

**R1.** A compaction Strategy MUST express all of its reshaping
actions by appending Events to the Session's Log. It MUST NOT
modify existing Events and MUST NOT reorder them.

**R2.** A compaction Strategy SHOULD install its logic at the
`:pre_projection` Hook Point so its decisions take effect in the
same turn they're computed. It MAY additionally install at other
lifecycle points (e.g., `:post_ingest`, `:turn_ended`) if the
strategy has per-turn bookkeeping.

**R3.** A compaction Strategy MUST be **idempotent across repeated
invocations of the same lifecycle point**: running twice in a row
MUST produce the same effective Projection output as running once.
The reference implementations achieve this by excluding
`:summary` Events from the count/size signals that trigger them.

**R4.** A `:compact` Event's `replaces` field MUST contain the
sequence numbers of Events that existed in the Log at the time the
`:compact` was appended. A strategy MUST NOT reference Events that
haven't been appended yet (no "forward references") or that don't
exist.

**R5.** A compaction Strategy MAY be reverted by appending a
`:revert` Event referencing the `:compact`'s sequence number. The
reference `Mutations.apply` handles `:revert` transitively (a
revert of a revert restores the original).

**R6.** A compaction Strategy MUST honor the composition rules in
[`17-composition-rules.md`](17-composition-rules.md). In particular,
it MUST be implementable using only the atomic operations enumerated
in R2 of that document. The external-world-callable exception (R3
of `17-composition-rules.md`) does NOT apply to the compaction
family: summarization, selection, and trigger logic are all
expressible through spec primitives, so a compaction Strategy MUST
NOT accept a callable parameter for that work.

**R7.** A compaction Mutation MUST NOT shadow a `:tool_use` without
also shadowing its corresponding `:tool_result`, or vice versa.
Strategies whose Selection axis would orphan one half of a tool-call
pair MUST drop both halves from the candidate set. The reference
implementation provides `Compaction::Helpers.tool_pair_safe_range`
for this.

## Canonical Strategies

[informative]

The reference implementation ships three compaction strategies for
comparison on canonical scenarios:

| Strategy | Trigger | Compaction rule | LLM call? |
|---|---|---|---|
| `MarkerTail` | message count > `max_messages` | keep `keep_recent`, replace older with fixed marker | no |
| `TokenMarkerTail` | estimated tokens > `max_tokens * threshold` | keep `keep_recent`, replace older with fixed marker | no |
| `SummaryTail` | message count > `max_messages` | keep `keep_recent`, replace older with LLM-generated summary via a sub-Log round-trip through the caller's Projection + Provider + Ingestor | yes |

Other strategies named in production harnesses (e.g., Claude Code's
four-stage pipeline; Codex's AgentHandoff; AIOS's KV-cache
preemption) are
additional hook-handler packs an implementation MAY provide. This
specification does not mandate any particular strategy; it only
specifies the contract every compaction strategy MUST honor
(R1–R5) and the Mutation Event shape (R4 of `01-overview.md`) they
emit.

## Installation Pattern

[informative]

Each reference compaction strategy installs as follows:

```ruby
handler = Harnas::Strategies::Compaction::MarkerTail.install(
  max_messages: 20, keep_recent: 10
)
# ... strategy is now attached to :pre_projection
# To remove:
Harnas::Hooks.off(:pre_projection, handler)
```

The `install` class method is an ergonomic wrapper around
`Harnas::Hooks.on(:pre_projection, ...)` that returns the
registered handler for later removal. Strategies MAY expose
additional installation-time parameters.

## Benchmarking

[informative]

The Harnas Benchmark harness (forthcoming, `06-benchmarks.md`)
compares strategies by running canonical scenarios through (provider
× compaction strategy × other hook-handler packs) matrices and
reporting metrics collected via the Observation bus
(`13-observation.md`):

- `:tokens_consumed` counts (input vs output per turn, cumulative)
- `:mutation_applied` counts (how many compactions fired, of what
  sizes)
- `:provider_called` / `:provider_responded` durations (latency)

No compaction-specific benchmark vocabulary is needed; the standard
Observation events carry the relevant signals.

## Versioning Note

**R7.** The shape of `:compact` Mutation Events
(`replaces: [Integer]`, `summary: String`) is normative and stable
within a major spec version. Additional fields MAY be added;
consumers MUST ignore unknown fields.
