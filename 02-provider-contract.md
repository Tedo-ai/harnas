# 02 — Provider Contract

A **Provider** is the component that accepts a request for model output and
returns the model's response. In practice a provider is usually an LLM API
(Anthropic, OpenAI, OpenRouter, a local inference server); the specification
does not require that providers be language models.

## Position in the Stack

[informative]

The Provider contract is the lowest-level seam in this specification. A
provider knows nothing about Sessions, Logs, Events, or Projections (see
`01-overview.md`). The `request` a provider receives is the materialized
output of a Projection over a Log; the `response` a provider returns is
parsed by the caller and appended back to the Log as a new Event. This
separation is deliberate: providers are usable standalone (for testing,
direct API exploration, or as building blocks in other systems), and the
Session/Log/Projection layer above can be developed and reasoned about
independently of any specific provider.

This document defines the wire-format contract that every Harnas provider
MUST honor. A later document (`03-core-types.md`, forthcoming) will define
the neutral types that a provider exposes on top of this contract. Keeping
the two layers separate is deliberate: the wire-format contract pins down
interoperability at the lowest level (what bytes flow in and out), while the
neutral-types layer defines the harness-visible vocabulary.

## The Contract

A provider is any entity that implements a single operation:

    call(request) -> response

where `request` and `response` are JSON-serializable objects. The operation
MAY involve network I/O, local computation, fixture replay, or any other
mechanism; the contract is about the shapes that flow across the boundary,
not about the implementation.

### Requirements

**R1.** A provider MUST accept a `request` object whose shape is defined by
the provider's own documentation. This specification does not prescribe the
shape of `request` in this document — it is provider-specific and is captured
normatively by **conformance fixtures** (see `conformance/README.md`).
The `request` is the *input handed to the provider*; it is not necessarily
identical to the bytes sent on the wire. A provider MAY route fields of the
request to other parts of the underlying call (e.g. URL path, headers,
query string) before transmission. The Gemini provider does this with
`model`, which is part of the URL path on the wire but appears as a
top-level field in the fixture.

**R2.** A provider MUST return a `response` object whose shape is defined by
the provider's own documentation. As with `request`, this specification does
not prescribe the shape of `response` here; conformance fixtures are
normative.

**R3.** A provider MUST signal transport-level failures (non-success status
codes from an underlying HTTP call, network errors, timeouts) through a
distinct error channel, separate from the normal `response` return path.
In the reference implementation this is `Harnas::Providers::HTTPError`;
other implementations MAY use idiomatic equivalents (typed exceptions,
result types, error values).

**R4.** A provider MUST signal malformed-payload failures (for example, a
200 response with a body that is not valid JSON) through an error channel
distinct from successful return. In the reference implementation this is
`Harnas::Providers::Error` (non-`HTTPError`).

**R5.** A provider MUST NOT mutate the `request` object it receives.

**R6.** Two provider implementations that present themselves as implementing
the same underlying service (for example, one live and one mock for
Anthropic) MUST accept identical `request` shapes and MUST return `response`
shapes that are structurally interchangeable. This is the property that
makes `Mock` swappable for `Anthropic` at test time.

## Mock Providers

A **mock provider** is a provider implementation that replays a recorded
conformance fixture instead of performing the operation for real. Mock
providers exist so that:

- implementations can be tested offline, without API keys or network access;
- the concrete wire shape of each provider is committed to the repository
  and reviewable as part of the specification;
- implementers in any language can validate their provider against the same
  recorded request/response pairs that the reference implementation uses.

A mock provider MUST honor R1–R6. Additionally, in **strict mode** (the
default), a mock provider MUST raise a fixture error if the incoming
`request` does not deep-equal the recorded request after JSON normalization.
Strict mode is what makes a mock a drop-in substitute for the real provider
for one specific canonical call; non-strict mode lets the fixture serve as
a generic response-shape source.

## Informative: reference implementation shape

In the Ruby reference implementation, the contract is expressed as a duck
type: any object that responds to `#call(request_hash)` and returns a
response hash (or raises `Harnas::Providers::Error` or its subclasses) is a
provider. No base class or mixin is required. Concrete implementations live
under `reference/lib/harnas/providers/`:

- `Harnas::Providers::Anthropic` — live Anthropic Messages API
- `Harnas::Providers::OpenAI` — live OpenAI Chat Completions API
- `Harnas::Providers::Gemini` — live Google Gemini generateContent API
- `Harnas::Providers::Mock` — fixture replay

This arrangement is informative; conforming implementations in other
languages MAY use any mechanism idiomatic to the host language (interfaces,
traits, protocols, structural typing) so long as R1–R6 hold.
