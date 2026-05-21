# Ecosystem

Harnas is the substrate. These are the products and integrations built on top
of it.

## The stack

```
  ┌──────────────────────────────────────────────────────────────────┐
  │  Products:   AgentStaple  ·  Editorial Rails  ·  vp-agent  ·     │
  │              OpenStaple (planned)                                 │
  ├──────────────────────────────────────────────────────────────────┤
  │  Integrations:  harnas-rails (planned)  ·  Custom integrations    │
  ├──────────────────────────────────────────────────────────────────┤
  │  Reference impls:  harnas-go · harnas-ruby · harnas-python ·     │
  │                    harnas-ts (in dev)                             │
  ├──────────────────────────────────────────────────────────────────┤
  │              Harnas spec + conformance fixtures                   │
  └──────────────────────────────────────────────────────────────────┘
```

## Products

### AgentStaple

A human-facing coding assistant. TUI for interactive use, web UI for richer
browsing, skills directory for context loading, approval rules for safe
edits, YOLO mode for trusted runs. Built on harnas-go.

- **Status:** Active development. Editing safety slice and interactive TUI
  approval prompt shipped.
- **Who it's for:** Individual developers using Harnas as their daily-driver
  coding agent.

### Editorial Rails pipeline

A production agent running inside a Rails 7.0 app, processing editorial
stories. The agent connects to an MCP server for domain-specific tools,
processes one story per run, and writes results back via the same MCP server.
Built on harnas-ruby.

- **Status:** Shipped to production. Actively processing real editorial
  workloads.
- **Who it's for:** Operators running agent workloads inside existing Rails
  applications. Patterns from this integration will inform the future
  `harnas-rails` engine.

### vp-agent

A CLI binary for the `vp spawn` orchestration system. Drop-in fourth harness
alongside `codex`, `claude-code`, and `opencode`. Accepts a prompt as a CLI
argument, runs to completion, exits with a documented code. Built on
harnas-go.

- **Status:** In development by the vp spawn team. Consumes harnas-go as a
  library.
- **Who it's for:** Orchestration systems that dispatch single-shot agents
  and consume their output programmatically.

### OpenStaple

Multi-agent orchestration. Parent agents spawn child agents. Task pipelines
with atomic claiming. Subagent events, parent/child sessions, heartbeats,
container-per-agent isolation. The product equivalent of "I want to run
twenty AgentStaples in parallel and have them coordinate."

- **Status:** Planned. Substrate prerequisites have landed through v0.18.0;
  product work starts when the harness is mature enough.
- **Who it's for:** Users running multi-agent workloads — research swarms,
  parallel CI agents, orchestrated pipelines.

## Integrations

### harnas-rails (planned)

A Rails engine that provides the two-table persistence schema
(`harnas_sessions` + `harnas_events`), a base ActiveJob for asynchronous
agent runs, an MCP client wrapper, and a Rails-idiomatic session API.
Extracted from the editorial Rails pipeline's plumbing once the pattern is
proven.

- **Status:** Design complete; extraction will happen after the editorial
  pipeline has had a few months of production use.

### Custom integrations

Anyone can build a product on Harnas in any of the supported languages. The
substrate doesn't care what's on top — your CLI, your web service, your
messaging bot, your batch job. The integration cost is small: one runtime
builder, your own tool handlers, your own persistence if you don't want
JSONL.

## How they relate

- **AgentStaple, the editorial Rails pipeline, vp-agent, and OpenStaple are
  all peers.** They consume harnas-* libraries; they don't depend on each
  other.
- **harnas-rails** (when it exists) will sit between Rails apps and
  harnas-ruby, providing the ergonomic Rails-side glue.
- **All four reference implementations** target the same spec. Choosing a
  language is a deployment decision, not a feature decision.

## Where you fit

- **Building an agent for an existing app?** Pick the language your app is in,
  consume the matching harnas implementation as a library, register your
  tools, run.
- **Building a CLI agent?** harnas-go has the smallest deployment footprint.
  vp-agent is the reference pattern.
- **Building a Rails-integrated agent?** Use harnas-ruby today; harnas-rails
  will streamline the integration when it ships.
- **Building something nobody has built yet?** The substrate doesn't have an
  opinion. If it's a sound agent shape, Harnas can host it.
