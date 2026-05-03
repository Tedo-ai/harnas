# 15 — Streaming

This document specifies **streaming** as the canonical wire shape of a
provider response. Streaming is a first-class primitive in Harnas: a
provider response is naturally expressed as a sequence of transport
Events terminated by a turn-completion marker, followed by the
consolidated semantic Events that enter the Log.

Non-streaming responses are the degenerate case of streaming, not the
other way around.

## Why Native

[informative]

Every production LLM API supports Server-Sent Events or chunked JSON
for responses. Harnas treats this as the default shape of a response
rather than as an optional feature. A subscriber reading the Observation
bus sees text, tool calls, and tool arguments arrive incrementally —
the same shape an end-user UI wants to render. The durable Log records
the consolidated semantic result, not every transport chunk.

## Canonical Delta Event Vocabulary

**S1.** The following Event types MUST be used to represent
incremental provider output on the Observation bus. Additional payload
fields MAY be added in later spec versions; existing fields are stable
within a major version.

| Event type | Payload fields | Fires when |
|---|---|---|
| `:assistant_turn_started` | `turn_id:` (String) | The provider has begun streaming a new assistant turn |
| `:assistant_text_delta` | `turn_id:`, `chunk:` (String) | A text chunk has arrived |
| `:tool_use_begin` | `turn_id:`, `tool_use_id:` (String), `name:` (String) | A tool-use block begins within the stream |
| `:tool_use_argument_delta` | `turn_id:`, `tool_use_id:`, `chunk:` (String; a partial JSON fragment of the tool input) | A tool-argument chunk has arrived |
| `:tool_use_end` | `turn_id:`, `tool_use_id:`, `arguments:` (Hash) | A tool-use block has been fully assembled |
| `:assistant_turn_completed` | `turn_id:`, `stop_reason:` (Symbol), `usage:` (Hash) | The provider has finished streaming this turn |
| `:assistant_turn_failed` | `turn_id:`, `error:` (String) | The stream was interrupted or aborted before `:assistant_turn_completed` |

## Event Ordering

**S2.** Within a single streaming turn, transport events MUST be
emitted on the Observation bus in this order:

1. Exactly one `:assistant_turn_started` at the start.
2. Zero or more `:assistant_text_delta`, `:tool_use_begin`,
   `:tool_use_argument_delta`, and `:tool_use_end` events, in the
   order they arrive from the provider.
3. Exactly one of `:assistant_turn_completed` or
   `:assistant_turn_failed` at the end.

**S3.** For each `:tool_use_begin(turn_id:, tool_use_id:)`, the
Observation stream MUST contain a corresponding
`:tool_use_end(turn_id:, tool_use_id:)` with a matching `tool_use_id`
before `:assistant_turn_completed`.

**S4.** Streaming transport Events (`:assistant_turn_started`,
`:assistant_text_delta`, `:tool_use_begin`,
`:tool_use_argument_delta`, `:tool_use_end`,
`:assistant_turn_completed`, and `:assistant_turn_failed`) MUST be
emitted on the Observation bus and MUST NOT be appended to the Log.
Only consolidated semantic Events such as `:assistant_message` and
`:tool_use` are appended to the Log.

## Provider Stream Contract

**S5.** A Harnas Provider MUST provide a streaming operation that
yields delta Events (per S1) to a caller-supplied block:

    provider.stream(request) do |event_args|
      # event_args is { type:, payload: } ready for AgentLoop handling
    end

The operation MUST honor S2 ordering; each call to the block MUST
correspond to one Event's worth of progress. Wire-format parsing
(Anthropic SSE, OpenAI SSE, Gemini streamGenerateContent JSON) is an
implementation detail of each Provider.

**S6.** At the AgentLoop boundary, **stream completion** means the
provider has yielded exactly one `:assistant_turn_completed` Event for
the active `turn_id`, followed by the consolidated Events for that
turn. The consolidated Events MUST be yielded after all transport
Events for that turn and MUST preserve the same turn result: one
`:assistant_message`, plus one `:tool_use` for each completed tool-use
block in provider order.

**S7.** After the stream terminates successfully, the provider MUST
yield the **consolidated** Events that are equivalent to what the
non-streaming `#call` would have produced — so that later Projections
can be written against the consolidated shape and ignore deltas:

    ...deltas...
    :assistant_turn_completed
    :assistant_message     { text, stop_reason, usage }   # consolidated
    :tool_use              { id, name, arguments }         # one per tool call in the turn

If the stream fails (network error, provider-signaled error before
completion), the provider MUST yield `:assistant_turn_failed` and MUST
NOT yield `:assistant_turn_completed` or the consolidated events.

## Stream Failure Semantics

**S8.** A streaming Provider call may fail mid-stream, including from
network failure, a server-signaled error after partial deltas, or a
malformed event. Partial transport Events already emitted on
Observation MUST remain visible to subscribers that received them.
They are not retroactively removed from the Observation stream.

**S9.** When a streaming Provider call fails, the runtime MUST emit
`:assistant_turn_failed` on Observation recording the failure. It MUST
NOT emit `:assistant_turn_completed` or append the consolidated
`:assistant_message` / `:tool_use` Events that complete a successful
stream.

**S10.** After a streaming Provider failure, the runtime MUST either
retry per its RetryPolicy, yielding a new `:assistant_turn_started` and
a fresh delta sequence, or terminate the Session with `:provider_error`
carrying `terminal: true`. Either outcome is conformant.

## Projection Behavior

**S11.** Projections MUST ignore all delta Event types
(`:assistant_turn_started`, `:assistant_text_delta`, `:tool_use_begin`,
`:tool_use_argument_delta`, `:tool_use_end`,
`:assistant_turn_completed`, `:assistant_turn_failed`) when building
outbound requests. Projections consume the consolidated `:assistant_message`
and `:tool_use` Events emitted after the stream completes.

This property makes streaming transparent at the Projection boundary
— the same Projection code works for streaming and non-streaming
providers.

Because these transport Events are Observation-only, a conforming
Projection usually never sees them in a newly-produced Log. The ignore
rule preserves compatibility with pre-v0.8 saved Logs and with
adopter-created diagnostic Logs that may still contain legacy delta
rows.

## Non-Streaming Providers

**S12.** Providers whose wire protocol is not actually incremental
(or providers that opt out of streaming for a given request) MUST
still emit the canonical sequence (S2), collapsed into a single
`:assistant_text_delta` (or a single `:tool_use_begin` +
`:tool_use_argument_delta` + `:tool_use_end` per tool call) followed
by `:assistant_turn_completed` and the consolidated events. This
preserves the invariant that Observation subscribers can render the
same streaming shape even when the underlying wire call was buffered.

## Observation Integration

[informative]

A UI renderer subscribes to the streaming Observation event and filters
for the delta types above:

    Harnas::Observation.subscribe do |event_name, payload|
      next unless event_name == :stream_event
      event = payload.fetch(:event)
      case event.type
      when :assistant_text_delta then print(event.payload[:chunk])
      when :assistant_turn_completed then puts
      end
    end

No durable Log write is required for live streaming UI: the Observation
bus is the streaming interface.

## Conformance

Streaming agent fixtures under `spec/conformance/agents/` use
`provider-script-stream.json` instead of `provider-script.json`. The
stream script is an ordered list of provider-call streams; each stream
is an ordered list of Event-args objects `{type, payload}` yielded to
the AgentLoop's stream callback.

**S13.** Streaming conformance fixtures MUST feed every scripted
transport Event to the AgentLoop in order, but `expected-log.jsonl`
MUST contain only the consolidated semantic Events that are appended to
the Log. Fixtures that need to assert transport-level detail SHOULD use
an Observation sidecar such as `expected-deltas.jsonl`.

The fact that real network chunking can vary is exactly why transport
deltas are not durable Log conformance. Given the same scripted stream,
two conformant implementations MUST produce byte-identical Logs for the
semantic result and MAY separately test byte-identical sidecar traces
for debugging surfaces.

## Versioning Note

**S14.** The delta Event vocabulary (S1) and ordering (S2, S3) are
stable within a major specification version. New payload fields MAY
be added; Subscribers MUST ignore unknown fields.
