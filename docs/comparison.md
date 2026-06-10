# Comparison

How Harnas compares to other agent frameworks and SDKs. This page is honest:
every project listed here does something well, and Harnas isn't the right
choice for every use case.

## The landscape

| Project | Type | Languages | Provider model | Persistence | Multi-impl conformance |
|---|---|---|---|---|---|
| **Harnas** | Substrate (spec + impls) | Go, Ruby, Python, TypeScript | Direct HTTP, all major providers | Append-only Log (JSONL) | 4 impls, same fixtures |
| LangChain / LangChain.js | Framework | Python, TS | Provider abstraction via wrappers | None built-in; bring your own | Independent Python and TS |
| OpenAI Agents SDK | SDK | Python (primary), JS | OpenAI-first | Limited | Single-vendor |
| Anthropic Claude Agent SDK | SDK | Python, TS | Anthropic-first | Limited | Single-vendor |
| Vercel AI SDK | Library | TS only | Provider abstraction | None built-in | Single language |
| Mastra | Framework | TS only | Provider abstraction | Built-in workflows | Single language |
| CrewAI | Framework | Python | Provider abstraction | Limited | Single language |
| AutoGen (Microsoft) | Framework | Python, .NET | Provider abstraction | Limited | Cross-language differs |

## What each does well

**LangChain / LangChain.js** is the most established and has the largest
community. If you need a vast catalog of pre-built integrations (every vector
DB, every tool, every chain pattern), LangChain has it. It's a framework —
it makes opinionated choices about how chains, memory, and tools compose.

**OpenAI Agents SDK** is the natural choice if you're committed to OpenAI's
models and want the official tooling. Tight integration with OpenAI's
function-calling and assistants APIs. Less compelling if you want provider
portability.

**Anthropic Claude Agent SDK** is the equivalent for Claude. Same shape:
tight integration with one vendor, less effort spent on provider abstraction.

**Vercel AI SDK** is excellent if you're building a TypeScript app (Next.js,
Cloudflare Workers, anything Vercel-ish) and want streaming-first provider
abstraction with React hooks. It's a library, not a substrate — it doesn't
try to be everything.

**Mastra** is more substrate-like, TypeScript-only, with built-in workflow
primitives. If you're TS-only and want a modern alternative to LangChain.js,
worth a look.

**CrewAI / AutoGen** are multi-agent-first frameworks. If your use case is
explicitly multi-agent orchestration, they have purpose-built abstractions.

## What Harnas does differently

**It's a substrate, not a framework.** Harnas doesn't have a "chain"
abstraction, doesn't have an opinion about memory, doesn't try to give you UI
components or prompt templates. It gives you the agent loop, the typed event
Log, the projection model, and a few primitives (strategies, hooks, tools).
You build your product on top.

**Conformance across language implementations.** Same spec, same fixtures,
same versioned protocol. Port your agent between Go, Ruby, Python, and
TypeScript by exchanging Logs. No other framework on this list takes this
discipline.

**The Log is the source of truth.** Every event — user message, tool call,
tool result, provider error — is in the append-only Log. Everything else
(transcripts, provider request bodies, cost summaries) is a projection.
Replay, fork, audit, and time-travel are built-in consequences of the
architecture, not bolt-ons.

**Direct HTTP providers, no SDK wrappers.** Harnas talks to Anthropic,
OpenAI, Gemini, and Ollama using their wire formats directly. No transitive
SDK dependencies; no implementation drift from SDK version differences.

**Built-ins are scarce on purpose.** Six built-in tools (`read_file`,
`write_file`, `edit_file`, `bash_session`, `fetch_url`, `load_skill`).
Everything else is your product's responsibility. The bar for adding a
built-in is higher than the bar for keeping it out.

## When Harnas is the right choice

- You need agents that run in multiple languages (Go service, Rails app,
  Python pipeline, Node CLI).
- Replay, fork, and audit matter for your product.
- You want provider portability without SDK lock-in.
- You prefer a small, sharp substrate over a large opinionated framework.
- You're willing to write product-specific code instead of consuming
  pre-built integrations.

## When Harnas is not the right choice

- You want a large catalog of pre-built tools, vector DBs, and chain patterns
  — LangChain is a better fit.
- You're TypeScript-only and need first-class React hooks for chat UIs —
  Vercel AI SDK is a better fit.
- You're building a chatbot with character personalities for Discord or
  Telegram — Eliza or similar is a better fit.
- You want to write the least possible code by stitching together pre-built
  abstractions — frameworks generally beat substrates here.

## The substrate vs framework choice

The deepest difference is philosophy. Frameworks help you go fast initially
by providing abstractions. They cost you later when those abstractions don't
fit and you can't easily get below them.

Substrates require more upfront work — you write your own tool dispatch,
your own approval flow, your own UI. They pay off when you need to do
something the framework didn't anticipate, because there's nothing in the way.

Harnas is the latter. If that tradeoff appeals to you, the rest of this site
is for you.
