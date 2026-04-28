# SummaryTail

**Family:** Compaction

**Selection:** Tail (keep the last N message events).
**Replacement:** LLMSummary (a one-turn round-trip through the
caller's Projection + Provider + Ingestor).
**Trigger:** MessageCount.

**Purpose:** Threshold-triggered compaction that generates the
summary text via a real LLM turn, instead of a mechanical
placeholder. Same Selection axis as `MarkerTail`; differs on
Replacement (LLMSummary vs Marker). Built entirely from the spec's
atomic operations — Log, Projection, Provider, Ingestor, Actions —
with no escape-hatch callable. Honors
[`17-composition-rules.md`](../../17-composition-rules.md) R1.

*(Historically named "Autocompact" in devlog entries 2026-04-20
phase-O and the composition-rules entry. The rename to a
systematic two-axis name landed with the block-strip
visualization convention; see the devlog entry on the rename.)*

## Composed of

- **Hook:** `:pre_projection`
- **Predicate:** `Helpers.message_events(log).size > max_messages`
- **Action:** `Actions::Compact` with `Helpers.tool_pair_safe_range`
  applied to the candidate seqs and `summary:` set to the assistant
  text returned by a one-turn sub-Log round-trip through the caller's
  Projection + Provider + Ingestor

## Algorithm (normative)

```
algorithm SummaryTail(projection, provider, ingestor,
                      max_messages, keep_recent,
                      prompt = DEFAULT_PROMPT):

  REQUIRES: projection.call(log) -> request
  REQUIRES: provider.call(request) -> response
  REQUIRES: ingestor.call(response) -> [event_args]
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

    to_summarize := filter(visible, e -> e.seq in safe)
    summary := summarize(to_summarize)
    if summary = "":
      return                                  # graceful no-op
    Actions.Compact(session, replaces: safe, summary: summary)

  function summarize(events):
    sub_log := Log.new
    for e in events:
      sub_log.append(type: e.type, payload: e.payload)
    sub_log.append(type: :user_message,
                   payload: UserMessage(text: prompt))

    request  := projection.call(sub_log)
    response := provider.call(request)
    for args in ingestor.call(response):
      sub_log.append(**args)

    last_assistant := find_last(sub_log, e -> e.type = :assistant_message)
    return string(last_assistant.payload.text) if last_assistant else ""
```

**Normative defaults:**

- `DEFAULT_PROMPT` is exactly:

  ```
  Summarize the preceding conversation tersely, preserving facts
  the agent will need to continue the work. Prefer specifics
  (names, values, decisions) over generalities. Return only the
  summary text, no preamble.
  ```

  Implementations that expose a `prompt` parameter MUST use this
  exact string (including line breaks and punctuation) as the
  default. Two conformant implementations running with defaults
  against the same Provider and events MUST send byte-identical
  summarization requests (modulo any variance the caller's
  Projection introduces).

- **Empty-response behavior:** if the ingested sub-Log contains no
  `:assistant_message` event or its text is empty, the algorithm
  MUST return without appending a `:compact` event. Compaction
  retries on the next `:pre_projection` invocation.

## Configuration

| Parameter | Type | Default | Description |
|---|---|---|---|
| `projection:` | anything responding to `#call(log)` | *(required)* | Builds the summarization request from the sub-Log |
| `provider:` | anything responding to `#call(request)` | *(required)* | Executes the summarization request |
| `ingestor:` | anything responding to `#call(response)` | *(required)* | Parses the response into Event args |
| `max_messages` | Integer | 20 | Compact when more than this many real messages are visible |
| `keep_recent` | Integer | 10 | Keep this many most-recent messages; compact older |
| `prompt` | String | (built-in; see source) | Summarization instruction appended to the sub-Log |

The caller passes the same `projection` / `provider` / `ingestor`
they're already using for the main agent loop. SummaryTail reuses
them through the sub-Log pattern documented in
[`17-composition-rules.md`](../../17-composition-rules.md); no
provider-specific code lives inside the strategy.

Constructor raises `ArgumentError` for any of: non-callable
`projection` / `provider` / `ingestor`, non-Integer thresholds, or
`max_messages <= keep_recent`.

## Arbitrary choices

- **Trigger:** strict `messages.size > max_messages`. Same trigger
  as MarkerTail — this strategy differs from MarkerTail only in *what summary
  text it emits*, not in *when it fires*.
- **Selection:** keep the last `keep_recent`; compact everything
  earlier. Same as MarkerTail.
- **Tool-pair safety:** yes, via
  `Harnas::Compaction::Helpers.tool_pair_safe_range`.
- **Summarization request shape:** a fresh `Harnas::Log` seeded with
  the events-to-compact (type + payload copied in seq order), then
  a single `:user_message` carrying the summarization prompt. This
  sub-Log is projected through the caller's Projection so the wire
  shape matches whatever the main loop is already using
  (Anthropic-shaped, OpenAI-shaped, Gemini-shaped).
- **Summary source:** the text of the last `:assistant_message`
  ingested from the Provider's response. If none is present, the
  strategy **does not compact** — it returns silently and will be
  retried on the next `:pre_projection` invocation.
- **Prompt:** a built-in default tells the model to summarize tersely
  while preserving facts, names, values, and decisions. Callers can
  override by passing `prompt:`.
- **Idempotency:** via `Helpers.message_events`, same as MarkerTail.

## Why this shape (vs. the original `summarizer:` callable)

The first version of SummaryTail took a `summarizer:` callable and
asked the caller to assemble the provider request themselves. That
violated `17-composition-rules.md` R1: the summarization work was
expressible entirely through the spec's atomic operations
(Projection, Provider, Ingestor), so pushing it out to a caller-
supplied callable was an escape hatch, not a legitimate
external-boundary exception. The current version takes the three
primitives directly and uses them in-spec. Cross-language
implementers port this verbatim; benchmarks can compare SummaryTail
against MarkerTail without the implementation differing in kind.

## When to use

- The agent benefits from real context preservation across long
  conversations (research, debugging, multi-step planning) and
  you're willing to pay for the extra LLM call.
- You want one-knob compaction that works against any provider the
  rest of your stack already talks to.

## When NOT to use

- Latency-sensitive flows where the summarization call would add
  unacceptable wait time on every triggering turn.
- Cost-sensitive flows where the extra call dominates the budget.
- Conversations where MarkerTail's "drop and forget" is acceptable.

## Failure modes

SummaryTail preserves *gist*. Its characteristic failures are all
variants of "the summarizer paraphrased, and the paraphrase is
plausible but not true":

- **Fabricated specifics.** An earlier tool call returned `Error:
  HTTP 503 from api.example.com`. The summarizer, asked to be
  terse, writes "encountered an API error during data fetch." Ten
  turns later the agent is asked "what was the error?" and answers
  "a 500-series error from the API" — confidently. The exact code
  and host are gone; the summary does not signal it omitted them.
- **Collapsed timelines.** The user iterated the task three times
  across early turns ("no, shorter" → "actually, make it formal
  again" → "okay but keep the new opening"). A summary flattens
  this to "the user wants a short formal version with the new
  opening," losing the negotiation structure. Subsequent turns
  re-litigate the same iterations because the agent can no longer
  reason "we already tried that."
- **Silent-failure of the summarization call.** When the
  summarizer Provider call fails (rate limit, network, malformed
  response), SummaryTail returns without compacting (§"Empty-
  response behavior"). That's graceful for one turn — but if the
  failure persists, subsequent turns continue to grow unbounded
  until the next successful summarization. Nothing about the
  Log's visible state signals that compaction is *failing*,
  only that it hasn't fired. A deployment should monitor
  `:provider_failed` Observation events from inside
  SummaryTail's own call path.
- **Prompt-sensitive summary quality.** The `DEFAULT_PROMPT` is
  deliberately brief. Agents whose success depends on specific
  preserved facts (names, IDs, numeric parameters) SHOULD override
  `prompt:` with domain-specific instructions — otherwise the
  summarizer's editorial choice of "what to keep" may not match
  the agent's downstream needs. Default-prompt SummaryTail is a
  generalist.

Unlike MarkerTail, SummaryTail's failure modes are *invisible from the
compaction marker alone*: the `:summary` event's text looks
reasonable, so the agent has no signal that the summarization
dropped something load-bearing.

## Installation

```ruby
projection = Harnas::Projections::Anthropic.new(model: "claude-haiku-4-5-20251001")
provider   = Harnas::Providers::Anthropic.new(api_key: ENV["ANTHROPIC_API_KEY"])
ingestor   = Harnas::Ingestors::Anthropic.new

Harnas::Strategies::Compaction::SummaryTail.install(
  projection: projection,
  provider:   provider,
  ingestor:   ingestor,
  max_messages: 20,
  keep_recent:  10
)
```

Swapping to OpenAI or Gemini is swapping the three primitives for
their provider's equivalents. The strategy doesn't change.

## Visualization

Block-strip per `spec/strategies/compaction/README.md`
§"Visualization convention". SummaryTail's signature is a single
wide synthetic block (the LLM summary) spanning the compacted
range, followed by preserved recent messages:

```
summary_tail   [S|≡ summary · 11 turns           |Tr|A|U]   ← wide synthetic replaces many
```

The width of the synthetic block is roughly the token count of the
LLM-generated summary. Unlike MarkerTail's faded-dropped shape, the
compacted history is *represented* by the summary, not shown as
absence — visually encoding the editorial tradeoff: SummaryTail
keeps the *gist* where MarkerTail keeps *nothing* of the older range.

## Implementation

`reference/lib/harnas/strategies/compaction/summary_tail.rb` — ~100
lines of plain Ruby. Uses the shared Compaction helpers plus the
sub-Log pattern from `17-composition-rules.md`. Zero
provider-specific branches.
