# Harnas

Harnas is the substrate underneath an AI agent: a specification, plus reference
implementations in Go, Ruby, Python, and TypeScript, for how an agent loop, its tools, its
providers, and its persistence layer fit together.

It is not a framework. Harnas does not have an opinion about your CLI, your UI,
your authentication model, your deployment target, your billing system, or the
shape of your product. Those are yours. Harnas gives you the agent loop, the
typed event log, and the projection model. Everything you build on top is yours.

## The architecture

At the center is the Log: an append-only sequence of typed events. Every user
message, assistant response, tool call, tool result, provider error, and
runtime observation is an event. The Log is the only durable state Harnas
requires.

Everything else is a Projection — a derived view computed from the Log on
demand. The provider request body sent to Anthropic, the UI transcript shown
to a human, a token usage summary, a diff between two sessions: these are all
projections of the same underlying Log.

The invariant: the Log is the truth. Projections are views. Two consumers
reading the same Log derive the same projection given the same options.

## The discipline

Harnas is conformance-first. Every reference implementation passes the same
versioned conformance suite. Spec changes start as a failing fixture in the
spec repo, then propagate to every implementation. A feature that lands in one
implementation but not the others is a bug, not progress.

Built-ins are scarce on purpose. Every tool Harnas ships — `read_file`,
`write_file`, `edit_file`, `bash_session`, `fetch_url`, `load_skill` — earned
its place by being something agents demonstrably need that shell commands
can't reasonably replace. The bar for adding a built-in is higher than the
bar for keeping it out.

Providers are direct HTTP, not SDK wrappers. Harnas talks to Anthropic,
OpenAI, Gemini, and Ollama using their wire formats directly. The wire format
is the contract; an SDK layer would mean implementations could quietly drift
as their respective SDKs evolved. Direct HTTP keeps conformance meaningful.

## What's built on it

- **AgentStaple** — a human-facing coding assistant with TUI, web UI, skills,
  and approval rules.
- **An editorial Rails pipeline** — a production agent in a Rails app,
  processing editorial stories via an MCP server.
- **vp-agent** (in development) — a CLI binary for orchestrated agent spawns.
- **OpenStaple** (planned) — a multi-agent orchestration product.

Each is its own product with its own opinions. Harnas is the shared substrate
underneath.

## The promise

If Harnas is a sound substrate for your AI agent, then:

- Porting between languages is straightforward — the Log is portable, the
  spec is the same.
- Switching providers means writing one projection and one ingestor, not
  refactoring the agent.
- Replaying a session is reading the Log.
- Forking a session for retry is reading the Log up to a point.
- Auditing what an agent did is reading the Log.
- Integrating with another agent product is exchanging Logs.

There is one source of truth. Everything else is a projection.
