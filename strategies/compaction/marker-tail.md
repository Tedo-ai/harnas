# MarkerTail

**Family:** Compaction

**Selection:** Tail (keep the last N message events).
**Replacement:** Marker (a fixed format string; no information
preserved about the compacted content beyond a count).
**Trigger:** MessageCount (strict `messages.size > max_messages`).

**Purpose:** Mechanical threshold-based compaction. Triggers on
message count; no LLM call. Sibling strategy `TokenMarkerTail`
shares Selection + Replacement and differs only on Trigger.

*(Historically named "Snip" in devlog entries 2026-04-19 through
2026-04-20 phase-O. The rename to a systematic two-axis name
landed with the block-strip visualization convention; see the
devlog entry on the rename.)*

## Composed of

- **Hook:** `:pre_projection`
- **Predicate:** `Helpers.message_events(log).size > max_messages`
- **Action:** `Actions::Compact` with `Helpers.tool_pair_safe_range`
  applied to the candidate seqs

## Algorithm (normative)

```
algorithm MarkerTail(max_messages, keep_recent,
                     summary_format = "[snipped $N earlier messages]"):

  REQUIRES: max_messages > keep_recent >= 0

  install handler at hook :pre_projection

  on :pre_projection(session):
    visible := filter(Mutations.apply(session.log), is_message_event)
    if |visible| <= max_messages:
      return

    candidates := seqs_of( prefix(visible, |visible| - keep_recent) )
    safe := tool_pair_safe_range(session.log, candidates)
    if |safe| = 0:
      return

    summary := summary_format with "$N" replaced by string(|safe|)
    Actions.Compact(session, replaces: safe, summary: summary)
```

**Normative defaults:**

- `summary_format`: the literal string `[snipped $N earlier messages]`.
  The token `$N` MUST be substituted with the decimal string
  representation of `|safe|` (the number of compacted events).
  Implementations that expose a `summary_format` parameter MUST
  use this exact string as the default.

**is_message_event** is defined in `spec/05-compaction.md` as the
set of Event types that count toward the size signal used by
compaction triggers (`:user_message`, `:assistant_message`,
`:tool_use`, `:tool_result`). `:summary` Events produced by prior
compactions are excluded, which is what makes the algorithm
idempotent.

## Configuration

| Parameter | Type | Default | Description |
|---|---|---|---|
| `max_messages` | Integer | 20 | Compact when more than this many real messages are visible |
| `keep_recent` | Integer | 10 | Keep this many most-recent messages; compact older |

Constraint: `max_messages > keep_recent`; `keep_recent >= 0`.

## Arbitrary choices

- **Trigger:** strict `messages.size > max_messages` (inclusive
  threshold would compact one message earlier; strict is slightly
  more conservative)
- **Selection:** keep the **last** `keep_recent`; compact everything
  earlier. Does NOT preserve the first user-assistant pair as some
  harnesses do. If the first turn contains load-bearing instructions,
  wrap the user's first prompt with them or use a different strategy.
- **Tool-pair safety:** yes, via
  `Harnas::Compaction::Helpers.tool_pair_safe_range`. An orphaned
  `:tool_use` or `:tool_result` is dropped from the compaction set,
  not compacted alone.
- **Summary:** `"[snipped N earlier messages]"` — fixed format.
  Contains the count; nothing about the conversation. This is the
  cheapest possible summary.
- **Idempotency:** via `Helpers.message_events`, which excludes
  `:summary` events produced by previous compactions from the
  trigger count. A second pass on an already-compacted Log sees
  only the `keep_recent` messages in effective view, which is below
  threshold, and correctly no-ops.

## When to use

- Input-token cost is dominant and summary quality doesn't matter.
- You want a deterministic, zero-extra-cost compaction baseline to
  benchmark other strategies against.
- You don't care that earlier context is lost (no summary
  preserves it).

## When NOT to use

- The agent genuinely needs context from earlier turns.
- You're willing to pay an extra LLM call for a meaningful summary
  (use `SummaryTail` instead).
- You want to preserve the initial prompt as a "session-defining"
  message (not supported; use a custom strategy).

## Failure modes

MarkerTail preserves recency. Its characteristic failures are all
variants of "the agent can't see what it can't remember":

- **Origin-task hallucination.** The first user message contained
  the task definition ("summarize these papers into a report on
  topic X"). After MarkerTail fires, the origin turn is dropped; the
  agent, asked to "continue the report," infers a plausible topic
  from the recent context and writes about the wrong thing. The
  agent speaks confidently — it has no signal that its view is
  truncated.
- **Decision re-litigation.** Earlier in the run, the user
  decided "skip the interview step, go directly to drafting." Ten
  turns later MarkerTail drops that exchange; the agent resumes
  interview-style questioning. No conflict signal fires because
  both behaviors are locally consistent.
- **Tool-result amnesia.** The agent ran a web search three turns
  before the compaction threshold, and its current reasoning depends
  on a fact from that search. MarkerTail drops the `:tool_use` /
  `:tool_result` pair (as a matched unit, via
  `Helpers.tool_pair_safe_range`). The agent's current turn
  references "the paper we found" but the paper's title, URL, and
  content are gone.

The `[snipped N earlier messages]` marker tells the model *that*
something was dropped, but not *what*. In practice models rarely
recover by asking the user to restate; they fill in from context,
which is how the failures above manifest.

## Visualization

Block-strip per `spec/strategies/compaction/README.md`
§"Visualization convention". MarkerTail's signature is distinctive:

```
marker_tail   [S|d|d|d|d|d|d|d|d|d|d|A|Tr|U]   ← faded 'd' blocks show what was dropped
```

Recent messages are preserved full-opacity on the right; the
faded-out left portion shows the exact compacted range. A reader
can eyeball "how much context was lost" at a glance and see
whether load-bearing early turns are among the faded blocks.

## Benchmark profile

Latest run on canonical scenarios (from `just benchmark`):

| Scenario | Config | Compactions | Input tokens | vs. no-compaction |
|---|---|---|---|---|
| long-conversation | max=6, keep=3 | 5 | 1225 | −45% |
| long-conversation | max=4, keep=2 | 5 | 1110 | −50% |

## Implementation

`reference/lib/harnas/strategies/compaction/marker_tail.rb` —
plain Ruby, ~50 lines, uses the shared Compaction helpers.
