# Projections

A Projection is a derived view of the [Log](./log-and-events.md). Computed
on demand. Never persisted. Different consumers project the same Log
differently.

## What it is

A function from `(Log, options) → view`. Examples:

- The **provider request body** sent to Anthropic, OpenAI, or Gemini. This
  is a projection that walks the Log, picks up `user_message`,
  `assistant_message`, `tool_use`, and `tool_result` events, formats them
  into the provider's wire format, and returns a JSON object ready to POST.
  Different providers have different wire formats; each has its own
  projection.

- The **UI transcript** shown to a human. Walks the Log, formats events for
  human reading, omits internal events (annotations, observation noise),
  renders tool calls and results in a transcript shape. AgentStaple's TUI,
  the editorial Rails dashboard, and any future operator console all use
  some flavor of transcript projection.

- A **token usage summary**. Walks the Log, sums `payload.usage` from every
  `assistant_message` event, returns aggregate counts and (optionally) an
  estimated cost.

- A **diff between two sessions**. Walks two Logs in parallel, identifies the
  first divergent event, returns a structured comparison.

- **Compaction**. Walks older Log events, summarizes them into a shorter
  representation, returns the compressed projection used to build the next
  provider request without losing the underlying Log.

## Why projections instead of stored views

Three reasons:

1. **The Log is the truth.** If a stored view drifts from the Log, the view
   is wrong, not the Log. Computing views on demand from the Log makes
   drift impossible.

2. **Different consumers need different views.** The provider needs a
   wire-format request. The UI needs a transcript. The dashboard needs a
   token summary. The auditor needs an event-by-event timeline. One Log,
   many projections.

3. **Projection logic can change without rewriting history.** If we want to
   change how compaction works, or how a transcript is rendered, or how
   token costs are estimated, we change the projection function. The Log
   stays the same.

## The invariant

> Two consumers reading the same Log derive the same projection given the
> same options.

This is the property that makes projections trustworthy. A projection is a
pure function of the Log and its options. No hidden state, no side effects.
If you give me your Log and your projection options, I can derive exactly
the same view you derived.

This invariant is also why Logs are portable across implementations: the
projection logic is in the spec (or in the impl, deterministically). Move
the Log between Go, Ruby, Python, and TypeScript — projections produce the
same output for the same inputs.

## Where projections live

Most projections are functions inside the harnas implementation libraries:

- `harnas-go`: `TranscriptProject`, `OpenAIProjection`, `AnthropicProjection`,
  `GeminiProjection`
- `harnas-ruby`: `Harnas::Transcript.project`, `Harnas::Projection::OpenAI`,
  etc.
- Same shapes in Python and TypeScript.

Consumers can also write their own projections — a custom UI transcript, a
domain-specific cost report, a session diff for code review. These live in
your product code, not in Harnas.

## What's not a projection

- The Log itself. The Log is the input; projections are outputs.
- Anything that mutates the Log. Append-only means projections can read but
  not modify.
- Cached database tables. If you populate a table from the Log, that's a
  projection materialized to storage. The Log is still the truth; the table
  is a cache.

## See also

- [`informative/log-and-projection.md`](../../informative/log-and-projection.md) — the formal spec
- [The Log and Events](./log-and-events.md) — what projections operate on
- [`informative/adopter-helpers.md`](../../informative/adopter-helpers.md) — `TranscriptProject` and other helpers
