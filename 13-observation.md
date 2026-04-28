# 13 — Observation

This document defines the **Observation** layer: a normative hook bus
that every Harnas implementation MUST emit canonical lifecycle events
through. Observation is the prerequisite for benchmarking strategies
empirically; without normative emission points and a stable event
vocabulary, two implementations cannot be measured apples-to-apples.

## Position in the Stack

[informative]

Observation is cross-cutting — it sits beside the substrate
(`01-overview.md`) and the Provider contract (`02-provider-contract.md`)
rather than above or below them. Every primitive in Harnas (Log,
Projection, Provider, Ingestor, Mutations) emits at well-defined
lifecycle moments; subscribers receive those emissions and may
record metrics, write traces, drive UI updates, or do nothing.

## Subscribers

**R1.** A Harnas implementation MUST expose a way to register one or
more **Subscribers**. A Subscriber is any callable that accepts two
arguments: an *event name* (a Symbol from the canonical vocabulary
defined below) and a *payload* (a Hash with the canonical fields for
that event).

**R2.** With no Subscribers registered, emission MUST be a no-op (no
side effects, near-zero cost). Implementations SHOULD short-circuit
emission when the Subscriber list is empty.

**R3.** Subscriber errors MUST NOT propagate into the calling Harnas
code path. An implementation MUST isolate subscriber exceptions and
continue delivering the event to other registered subscribers.

## Canonical Event Vocabulary

**R4.** The following event names are normative. Implementations MUST
emit each event at the location described under "Emitted when",
carrying at least the listed payload fields. Additional payload
fields MAY be included; subscribers MUST ignore unknown fields.

| Event | Payload fields | Emitted when |
|---|---|---|
| `:event_appended` | `event:` (an Event), `log_size:` (Integer, post-append) | An Event has been appended to a Log |
| `:projection_invoked` | `projection:` (Symbol or String name), `log_size:` (Integer), `request:` (Hash) | A Projection has produced a wire-format request |
| `:provider_called` | `provider:` (Symbol identifier), `request:` (Hash) | A Provider is about to send a wire request |
| `:provider_responded` | `provider:`, `duration_ms:` (Integer), `response:` (Hash) | A Provider has received a successful response |
| `:provider_failed` | `provider:`, `duration_ms:` (Integer), `error:` (Exception) | A Provider call has raised; the exception is also propagated |
| `:mutation_applied` | `log_size:` (Integer), `effective_size:` (Integer), `applied_count:` (Integer) | `Mutations.apply` has resolved a Log to its effective event stream |
| `:tokens_consumed` | `provider:` (Symbol), `input_tokens:` (Integer), `output_tokens:` (Integer) | An Ingestor has extracted normalized token counts |
| `:tool_invoked` | `tool_use_id:` (String), `name:` (String), `outcome:` (`:ok` or `:error`), `duration_ms:` (Integer), `error:` (Exception or nil) | A Tool has been executed by the Runner |

**R5.** Implementations MUST emit `:provider_called` before the wire
request is dispatched, and exactly one of `:provider_responded` or
`:provider_failed` after the call returns or raises. The
`duration_ms` MUST measure wall-clock time between the dispatch and
the return/raise.

**R6.** New event names and payload fields MAY be added in later spec
versions. Existing names and payload field shapes are stable within
a major spec version.

## Versioning Note

[informative]

Subscribers SHOULD treat the canonical event vocabulary as
append-only. A subscriber that handles only the events it knows
about, ignoring the rest, is forward-compatible with future
specification versions. A subscriber that hard-fails on unknown
event names will break across minor spec updates.

## Reference Implementation Shape

[informative]

In the Ruby reference implementation, `Harnas::Observation` is a
module exposing `.subscribe(callable_or_block)`, `.unsubscribe(sub)`,
`.emit(event, **payload)`, and a scoped helper
`.subscribed { |collector| ... }` that registers an in-memory
`Collector` for the duration of a block — useful for tests and ad-hoc
inspection.

A `Collector` records every event in order and exposes:

- `#events` — the full Array of `[event, payload]` pairs
- `#of(event_name)` — filter by event name
- `#count(event_name)` — count emissions of a given event

This shape is informative; conforming implementations in other
languages MAY use any registration / dispatch mechanism idiomatic to
the host language so long as R1–R6 hold.
