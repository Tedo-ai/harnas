# Harnas

A spec-first, language-portable specification for LLM agent harnesses.
*(Pronounced HAR-nahs — Dutch for "harness".)*

This repository is the **specification itself**. Implementations live
in their own repositories; passing the conformance fixtures here is
what makes an implementation Harnas-conformant.

**Version 0.8.0** (released 2026-05-03). See
[`CHANGELOG.md`](CHANGELOG.md) for normative additions and fixture
coverage.

## What Harnas specifies

The coordination layer between a language model (or any provider that
answers model-shaped requests) and the surface a user or operator
interacts with. It sits above provider-specific APIs and below
application-level concerns like UI, orchestration, and policy.

The architectural commitment is small but specific: an **append-only
Log of typed Events** is the source of truth; provider request bodies
are pure **Projections** of that Log; provider responses are
**Ingested** back as more Events; reshaping (compaction, retraction,
supersession) happens via first-class **Mutation Events** that
reference earlier ones rather than modifying them.

## Reading order

1. [`00-conventions.md`](00-conventions.md) — RFC 2119 keywords,
   normative vs informative text, vocabulary, versioning.
2. [`01-overview.md`](01-overview.md) — the architectural frame: the
   layer picture, scope and out-of-scope, and the
   Log + Projections + Mutations model.
3. [`02-provider-contract.md`](02-provider-contract.md) — the
   wire-format contract every provider must honor.
4. [`04-tools.md`](04-tools.md), [`05-compaction.md`](05-compaction.md),
   [`07-permission.md`](07-permission.md) — Tools, Compaction,
   Permission contracts.
5. [`13-observation.md`](13-observation.md), [`14-hooks.md`](14-hooks.md),
   [`15-streaming.md`](15-streaming.md), [`16-actions.md`](16-actions.md),
   [`17-composition-rules.md`](17-composition-rules.md) — observation
   bus, hooks, streaming semantics, actions, composition rules.
6. [`18-agent-manifest.md`](18-agent-manifest.md) — declarative JSON
   manifest format. Two conformant implementations loading the same
   manifest must produce byte-identical Logs.
7. [`19-jsonl-persistence.md`](19-jsonl-persistence.md) — canonical
   Session JSONL persistence format for cross-language save/load.
8. [`20-production-embedding.md`](20-production-embedding.md) —
   recommended production embedding shape for web apps and services.
9. [`strategies/`](strategies/) — per-strategy spec stubs (compaction
   and permission shipped in 0.1; more in 0.2+).
10. [`conformance/`](conformance/) — fixtures any conformant
   implementation must reproduce byte-for-byte.

## Implementations

| Language | Repo | Status |
|---|---|---|
| Ruby     | [Tedo-ai/harnas-ruby](https://github.com/Tedo-ai/harnas-ruby) | Reference implementation. 24/24 agent conformance, reasoning capture/round-trip, Observation-only streaming deltas, round-trip persistence matrix, live providers (Anthropic, OpenAI, Gemini), 8 builtin tools, 4 compaction strategies, full feature set. |
| Python   | [Tedo-ai/harnas-python](https://github.com/Tedo-ai/harnas-python) | 24/24 agent conformance, reasoning capture/round-trip, Observation-only streaming deltas, round-trip persistence matrix, live providers (Anthropic, OpenAI, Gemini), builtin tools, middleware, compaction, permissions, and CLI surface. |
| Go       | [Tedo-ai/harnas-go](https://github.com/Tedo-ai/harnas-go) | 24/24 agent conformance, reasoning capture/round-trip, Observation-only streaming deltas, round-trip persistence matrix, live providers (Anthropic, OpenAI, Gemini), builtin tools, middleware, compaction, permissions, and CLI surface. |

A second implementation that passes every fixture under
[`conformance/agents/`](conformance/agents/) is, by the spec's
definition, conformant on those cases. The Ruby, Python, and Go
implementations are the existence proof that Harnas is genuinely
portable; new ports in any language are welcome.

## License

[MIT](LICENSE).
