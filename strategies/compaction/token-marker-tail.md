# TokenMarkerTail

**Family:** Compaction

**Selection:** Tail (keep the last N message events).
**Replacement:** Marker (fixed format string with token-count
diagnostics).
**Trigger:** TokenEstimate (`estimated_tokens > max_tokens * threshold`).

**Purpose:** Token-estimate threshold compaction. Same Selection +
Replacement as `MarkerTail`; differs only on Trigger — fires when
estimated input tokens exceed a percentage of a declared budget.
No LLM call.

*(Historically named "PercentageHeuristic" in devlog entries
2026-04-19 phase-K through 2026-04-20 phase-O. The rename to a
systematic two-axis name landed with the block-strip
visualization convention; see the devlog entry on the rename.
`MarkerTail` and `TokenMarkerTail` will merge under one class
once the Trigger taxonomy lands in a future spec version.)*

## Composed of

- **Hook:** `:pre_projection`
- **Predicate:** `Helpers.estimate_tokens(Helpers.message_events(log)) > max_tokens * threshold`
- **Action:** `Actions::Compact` with `Helpers.tool_pair_safe_range`
  applied to the candidate seqs

## Algorithm (normative)

```
algorithm TokenMarkerTail(max_tokens, threshold, keep_recent,
    summary_format = "[compacted $N earlier messages (~$E tokens -> threshold $T)]"):

  REQUIRES: max_tokens > 0
  REQUIRES: 0 < threshold <= 1.0
  REQUIRES: keep_recent >= 0

  install handler at hook :pre_projection

  on :pre_projection(session):
    visible        := filter(Mutations.apply(session.log), is_message_event)
    estimated      := estimate_tokens(visible)    # 4 chars per token
    trigger_tokens := floor(max_tokens * threshold)
    if estimated <= trigger_tokens:
      return

    candidates := seqs_of( prefix(visible, |visible| - keep_recent) )
    safe := tool_pair_safe_range(session.log, candidates)
    if |safe| = 0:
      return

    summary := summary_format with
      "$N" -> string(|safe|),
      "$E" -> string(estimated),
      "$T" -> string(trigger_tokens)
    Actions.Compact(session, replaces: safe, summary: summary)
```

**Normative defaults:**

- `summary_format`: the literal string
  `[compacted $N earlier messages (~$E tokens -> threshold $T)]`.
  All three tokens MUST be substituted with decimal string
  representations of the referenced counts.
- `estimate_tokens`: the 4-characters-per-token heuristic from
  `05-compaction.md`. Implementations MAY provide more-precise
  estimators as a separate strategy, but TokenMarkerTail's
  default behavior uses the cheap estimator.

## Configuration

| Parameter | Type | Default | Description |
|---|---|---|---|
| `max_tokens` | Integer | 100_000 | Declared input-token budget for the Session |
| `threshold` | Float (0.0, 1.0] | 0.85 | Fraction of `max_tokens` at which to trigger |
| `keep_recent` | Integer | 10 | Keep this many most-recent messages |
| `summary_format` | String | *(see Algorithm)* | `$N`/`$E`/`$T` substitutions |

## Arbitrary choices

- **Trigger:** strict `Helpers.estimate_tokens(messages) > max_tokens * threshold`
- **Token estimation:** 4-chars-per-token heuristic via
  `Helpers.estimate_tokens` — **NOT a real tokenizer.** For precise
  budget enforcement, write a custom strategy that uses a real
  tokenizer for your provider (this strategy's point is being cheap,
  not precise).
- **Selection:** keep the **last** `keep_recent`; compact everything
  earlier. Same caveat as MarkerTail regarding the first turn.
- **Tool-pair safety:** yes, via
  `Harnas::Compaction::Helpers.tool_pair_safe_range`.
- **Summary:** `"[compacted N earlier messages (~X tokens -> threshold Y)]"` —
  includes diagnostic data so benchmark reports show what triggered.
- **Idempotency:** via `Helpers.message_events` + the token estimate
  dropping sharply once older messages become shadowed by the
  compact. A second pass sees only `keep_recent` messages, whose
  estimated tokens are below threshold.

## When to use

- You have a declared input-token budget (e.g., provider's context
  window) and want a hands-off threshold alert that fires before you
  hit it.
- You don't care about tokenization precision — an approximate
  signal is enough to trigger compaction before real cost spikes.

## When NOT to use

- Your provider charges by precise token count and you're optimizing
  right up against the budget — the 4-chars-per-token heuristic can
  be off by ±30%.
- You want compaction to trigger on cost, not token count. Write a
  custom strategy that uses `Observation`'s `:tokens_consumed`
  accumulations.

## Failure modes

TokenMarkerTail shares MarkerTail's editorial failure modes
(origin-task hallucination, decision re-litigation, tool-result
amnesia — see `marker-tail.md`) *plus* two that are specific to the
token-estimate trigger:

- **Under-shoot: never-trigger.** The 4-chars-per-token estimator
  systematically under-counts for dense content (code, structured
  JSON tool output, non-Latin text — where token ratios are
  typically 1:2 or worse). A budget set at 100k tokens with
  threshold 0.85 can silently permit a real context usage over
  120k — well into provider-rejection territory — before any
  estimate crosses the 85k trigger. The strategy appears to "not
  fire" when in fact the budget has already been exceeded in
  reality.
- **Over-shoot: trigger-too-early.** The same estimator over-counts
  for sparse content (prose with whitespace, Markdown with heavy
  formatting). A budget set at 10k with threshold 0.7 can trigger
  compaction at ~5k real tokens, discarding context the agent still
  comfortably fit — an unnecessary loss.

The failures are invisible to the strategy's log output: its
summary reports the *estimated* trigger value, not the true one.
If real tokenization matters, write a variant that calls the
provider's tokenizer endpoint (and document the extra latency
cost).

## Benchmark profile

Latest run on canonical scenarios:

| Scenario | Config | Compactions | Input tokens | Note |
|---|---|---|---|---|
| long-conversation | max=1000, threshold=0.5, keep=3 | 0 | 2224 | Canned responses stay below 500-token trigger; strategy never fires |

The benchmark reveals a tuning lesson: strategy thresholds need to
match actual traffic profiles. For this scenario, either lower
`max_tokens` or use the message-count-based MarkerTail.

## Visualization

Block-strip per `spec/strategies/compaction/README.md`
§"Visualization convention". TokenMarkerTail's strip is
identical in shape to MarkerTail's — the two differ only in *when* they
fire, not in *what they preserve*:

```
token_marker_tail   [S|d|d|d|d|d|A|Tr|U]   ← same faded-dropped / full-kept shape as MarkerTail
```

For comparison visualizations, both share the "recency-preserving"
signature.

## Implementation

`reference/lib/harnas/strategies/compaction/token_marker_tail.rb` —
plain Ruby, ~60 lines, uses the shared Compaction helpers.
