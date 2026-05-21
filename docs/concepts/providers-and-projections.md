# Providers and Projections

A **provider** is a connection to an LLM API (Anthropic, OpenAI, Gemini,
Ollama). Each provider has its own wire format. Harnas converts the
shared [Log](./log-and-events.md) into each provider's format using a
**projection**, and converts each provider's response back into the Log
using an **ingestor**.

## The four shipped providers

- **Anthropic** — Claude models (Haiku, Sonnet, Opus). Native reasoning
  support, tool use, system prompts.
- **OpenAI** — GPT models, plus OpenAI-compatible endpoints (OpenRouter,
  Together, Grok, Kimi, etc.). Same wire format.
- **Gemini** — Gemini Pro models. Native reasoning support, tool use, the
  Google-specific request shape.
- **Ollama** — local models. Uses the OpenAI-compatible wire format with
  a local base URL; no API key required.

Each is implemented as direct HTTP — no provider SDK. The wire format is
the contract.

## The projection / ingestor pair

For each provider:

- The **projection** walks the Log and produces a provider-shaped request.
  `OpenAIProjection` walks the Log and emits `messages: [...]` in OpenAI's
  shape. `AnthropicProjection` emits Anthropic's shape. `GeminiProjection`
  emits Gemini's `contents: [...]`.

- The **ingestor** takes a provider's response and produces canonical
  Harnas events to append to the Log. `OpenAIIngestor` takes an OpenAI
  response and emits the right combination of `assistant_message`,
  `tool_use`, and (if streaming) delta events.

The pair makes provider portability work. Switch providers by swapping the
projection and ingestor. The Log stays the same. Strategies, hooks, tools,
persistence — all unchanged.

## Why direct HTTP, not SDKs

The official SDKs from Anthropic, OpenAI, Google, etc. abstract the wire
format behind their own conventions: their own retry logic, their own
streaming abstractions, their own error types, their own version cadence.

If each Harnas implementation used its language's SDK, four problems
emerge:

1. **Drift across impls.** harnas-go would inherit the Go SDK's quirks,
   harnas-python the Python SDK's. Four implementations would gradually
   accumulate different bugs and behaviors despite passing the same
   conformance suite.

2. **Hidden retry semantics.** An SDK that silently retries on certain
   errors masks them from the Log. The Log should be the truth; an SDK
   adding behavior between Harnas and the wire violates that.

3. **Version coupling.** Bumping the Anthropic Go SDK to fix one bug might
   change request/response handling in ways that break parity with the
   Python impl.

4. **Transitive dependency bloat.** Provider SDKs pull in their own
   dependencies. A library should be thin.

Direct HTTP keeps the wire format as the only contract. All four impls
read and write the same bytes. Conformance is meaningful.

## What you write to add a provider

If a fifth provider becomes worth supporting:

1. Write the **projection**: a function from Log → provider request body.
2. Write the **ingestor**: a function from provider response → Log events.
3. Register both with the manifest provider system.
4. Pass the conformance fixtures that test the new provider's behavior.

That's it. No new event types, no changes to strategies or tools, no
changes to persistence. The substrate doesn't know which provider it's
talking to once the projection and ingestor are in place.

## Streaming

Each provider has both buffered and streaming variants. Streaming uses
SSE parsing over `fetch` (or each language's equivalent), emits transport
events to the Observation bus during the stream, and consolidates the
final result into the canonical `assistant_message` event when the stream
completes. Streaming transport events do NOT append to the Log — only the
consolidated final events do.

This keeps the Log clean for replay: a streaming session and a buffered
session produce the same Log if the model returned the same content.

## See also

- [The Log and Events](./log-and-events.md) — what projections operate on
  and what ingestors emit
- [Projections](./projections.md) — the broader concept
- [`informative/provider-implementation.md`](../../informative/provider-implementation.md)
  — the convention that all impls use direct HTTP
