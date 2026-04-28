# 01 — Overview

This document establishes the architectural framing every later section
builds on, declares what is in scope and what is not, and points to where
each concern is specified in detail. It is the entry point to the
specification.

## What Harnas Is

Harnas specifies the coordination layer between a language model (or any
provider that responds to model-shaped requests) and the surface a user or
operator interacts with. It sits above provider-specific APIs and below
application-level concerns like UI, orchestration, and policy. The same
specification can be implemented in any language; the Ruby code under
`reference/` is one implementation and is informative only.

## The Layer Picture

[informative]

A complete agentic system layers roughly as follows:

    +------------------------------------------------------+
    |  Surface       (CLI, IDE, chat app, autonomous loop) |
    |  Orchestrator  (multi-agent coordination, policy)    |
    +------------------------------------------------------+
    |  HARNAS        (this specification)                  |
    |    Session, Log, Events, Projections                 |
    |    Provider contract, Tool contract                  |
    |    Compaction, deferred tools, cache, capabilities   |
    +------------------------------------------------------+
    |  Provider runtimes (Anthropic, OpenAI, Gemini, ...)  |
    |  Tool runtimes     (in-process, sandbox, MCP)        |
    |  Transports        (HTTP, SSE, stdio, WebSocket)     |
    |  Storage           (memory, file, database)          |
    +------------------------------------------------------+

Harnas does not specify what is above or below it. It specifies the
contracts at both seams (what providers expose downward, what surfaces
consume upward) and the internal model — the Session, the Log, and the
Projection — that connects them.

## The Provider call is the one irreducible primitive

[informative]

Every other primitive in Harnas — Log, Projection, Ingestor,
Actions, Hooks, Mutations, Strategies — wraps, shapes, or reacts to
a single non-configurable operation: `Provider.call(request) ->
response`. That one call, defined in `02-provider-contract.md`, is
the actual LLM API request; everything else in the specification is
decoration around it. Naming this plainly matters:

- **Harnas invents no primitives *above* the LLM API.** Messages,
  tools, tool_use / tool_result, stop reasons, streaming deltas —
  all come from the provider's native vocabulary. Harnas translates
  nothing; it names what is already there.
- **The fixed topology of the agent loop is the LLM API loop, not
  an abstraction on top of it.** Projection → Provider → Ingestor
  → (maybe dispatch tools) → repeat. The loop is a topology with
  slots, not a graph the user assembles.
- **Conformance testing has a sharp target.** Two conformant
  implementations, given the same Log, MUST produce identical
  request bodies to `Provider.call`. The rest of the spec is
  judged by what it produces *at that seam*.

Strategies, Hooks, Actions, and Mutations exist to compose around
the Provider call, not to replace it.

## Architectural Choice: Append-Only Log With Projections

The single most consequential decision in this specification is how the
state of an ongoing interaction is modeled. Harnas commits to an
append-only event log as the source of truth, with provider-bound views
materialized as projections, and reshaping operations expressed as
first-class mutation events.

**R1.** The state of a Harnas Session MUST be modeled as an append-only
**Log** of **Events**. Events are never modified, removed, or reordered
after they are appended.

**R2.** Each Event MUST have a stable identity assigned at append time.
This specification commits to monotonic per-Session sequence numbers as
the canonical identity scheme; content-addressable hashes are RECOMMENDED
as a secondary identity for cross-Session referencing and integrity
verification.

**R3.** The view of the Session sent to a provider on any given turn MUST
be a **Projection** of the Log. A Projection is a pure, deterministic
function of the Log. Different Projections of the same Log MAY exist
concurrently for different consumers (an API-bound Projection sent to the
provider, an audit Projection that includes everything, a UI Projection
that hides system internals).

**R4.** Reshaping the Session — what other systems call compaction,
truncation, summarization, retraction, or supersession — MUST be performed
by appending **Mutation** Events to the Log. A Mutation references the
events it transforms by their stable identity and supplies the replacement
content; the original events remain in the Log unchanged. Mutations are
themselves Events, and MAY be referenced by later Mutations (a compaction
MAY be reverted by appending a mutation that references it).

**R5.** Implementations MUST produce identical Projection outputs for
identical Log inputs. The algorithm by which a Projection is computed is
informative; the output is normative. Implementations are free to use
materialized views, incremental projection, caching, or any other
optimization, provided the output matches.

### Annotative Events

Beyond the *substantive* Event types that represent the agent's
conversation (`:user_message`, `:assistant_message`, `:tool_use`,
`:tool_result`) and the Mutation Events that reshape them
(`:compact`, `:revert`), the Log MAY contain **annotative Events**:
events appended by strategies, middleware, or surfaces to record
derived state they want persisted with the Session.

**R6.** The canonical annotative Event type is `:annotation`, with
payload shape `{ kind: String, data: Hash }`. The `kind` field
namespaces the annotation (e.g. `"stale_read_guard.hash"`);
implementations SHOULD use dotted identifiers prefixed by the
component that owns the annotation, so different components'
annotations never collide.

**R7.** Projections MUST NOT emit `:annotation` Events into the
request body sent to a Provider. They are part of the Log
substrate, not part of the agent's conversation.

**R8.** Annotative Events MAY be shadowed by compaction strategies
the same as any other Event. Components that write annotations
MUST be prepared for their annotations to disappear under
compaction and MUST NOT depend on them being present; absence of
an expected annotation is always a legal Log state.

### Provider error events

When a Provider call fails (HTTP error, timeout, malformed
response), the failure is appended to the Log as a
`:provider_error` Event with payload
`{provider, status, error_class, message, attempt, terminal}`.

**R9.** A `:provider_error` Event MUST be appended for each failed
Provider call. The event is annotative (R7 applies — projections
MUST NOT include it in the request body sent to a Provider).

**R10.** When a runtime retries a failed Provider call (per its
configured retry policy), each non-final failed attempt MUST be
recorded with `terminal: false`. The final failed attempt — the
one after which no further retry is attempted — MUST carry
`terminal: true`. A successful retry needs no further event;
the absence of a terminal `:provider_error` after non-terminal
ones means the call eventually succeeded.

**R11.** When the runtime terminates a Session because retries
were exhausted, it MUST end with reason `:provider_failed` and
the most recent `:provider_error` MUST carry `terminal: true`.

### Why this design

[informative]

This frame absorbs both philosophical camps that current production
harnesses split between — *transcript-centric pruning*, where the
conversation is treated as a malleable array, and *event-sourced ledger*,
where the conversation is treated as an append-only log. The Log is the
substrate of the event-sourced view; mutation Events are the substrate of
the transcript-centric view. Choosing the Log as the source of truth and
making mutations first-class events buys the following properties by
construction:

- **Crash recovery** — replay the Log up to the last durable sequence
  number.
- **Time travel and forking** — project the Log up to any sequence number;
  fork by branching at one.
- **Reversibility of compaction** — append a revert mutation; nothing is
  destroyed.
- **Audit trail** — the Log *is* the audit; no separate logging path is
  required.
- **Cache-stable prefixes** — events whose effects are settled (no future
  Mutation references them) are safe to cache; the Projection can compute
  this.
- **Inter-agent message passing** — events are the wire format between
  agents; one agent's append is another agent's read.
- **Capability security** — events carry signed capabilities; Projections
  reject unauthorized mutations.

Each of these properties is specified in its own section; this overview
declares only that the Log/Projection/Mutation model is the substrate they
all build on.

## Scope

[normative]

The following concerns are within the scope of this specification:

| Concern | Section |
|---|---|
| Conventions and vocabulary | `00-conventions.md` |
| This overview | `01-overview.md` |
| Provider wire-format contract | `02-provider-contract.md` |
| Core types: Event, Log, Session, Projection, Mutation | `03-core-types.md` (forthcoming) |
| Tool contract | `04-tool-contract.md` (forthcoming) |
| Compaction (as a Mutation family) | `05-compaction.md` (forthcoming) |
| Deferred tool discovery | `06-deferred-tools.md` (forthcoming) |
| Cache-aware Projection | `07-cache.md` (forthcoming) |
| Capability-based security | `08-capabilities.md` (forthcoming) |
| Inter-agent IPC | `09-ipc.md` (forthcoming) |

## Out of Scope

[normative]

The following concerns are explicitly NOT specified:

- **Model selection, training, or fine-tuning.** The provider contract
  treats models as opaque named identifiers.
- **Vector stores and retrieval-augmented generation.** Retrieval is a
  Tool concern; how a tool computes its results is out of scope.
- **UI rendering.** Surfaces are out of scope; what one looks like and
  how it is implemented is up to the surface.
- **Specific transport protocols.** The provider contract specifies
  wire-format shape, not how bytes get from A to B. HTTP, WebSocket,
  stdio, MCP-style, or in-process invocation are all valid.
- **Specific provider APIs.** Each provider's own documentation is the
  authority for its wire format; Harnas only specifies how to abstract
  over providers.
- **Specific tool implementations.** A Tool is a named invocable
  capability with a declared input/output contract; what the tool
  actually does is out of scope.
- **Policy-level permission and capability models.** The permission
  Strategy contract (`07-permission.md`) specifies the per-`:tool_use`
  allow/deny primitive and ships a HumanApproval canonical strategy.
  The specific authz policy an adopter layers on top — RBAC, ACL,
  capability tokens, deny-by-default sandboxing — is an adopter
  choice. Harnas provides the decision point; it does not prescribe
  the policy.
- **Task-level evaluation of agent quality.** The Benchmark harness
  (`06-benchmarks.md`) compares Strategy combinations on cost,
  latency, and compaction metrics for a fixed workload. Whether the
  underlying model-and-harness combination actually solves a given
  task well is a model-and-task concern above this specification;
  Harnas does not specify task-quality evaluation protocols.
- **Multi-agent orchestration.** Harnas specifies single-agent Session
  state. Patterns where one agent spawns, delegates to, or hands off
  to another are orchestrator-layer concerns. Sub-agent delegation
  MAY be expressed as a Tool whose return value is a Log fragment to
  splice, but this specification does not normatively bless that
  pattern in 0.1.
- **Runtime environment integration.** Bridges into IDEs, terminals,
  browsers, or filesystems are a Surface or Orchestrator concern.
  See *Adjacent specifications* below for how MCP composes with
  Harnas at this seam.
- **Cross-implementation telemetry export formats.** `13-observation.md`
  specifies the Observation bus normatively inside a Harnas
  implementation. Exporting those observations to external systems
  (OpenTelemetry, Honeycomb, Datadog, structured log files, …) is
  an adapter concern and is not specified here.

## Adjacent specifications

[informative]

Harnas does not attempt to cover every concern in the agent stack.
Several existing specifications address adjacent concerns and compose
with Harnas rather than compete with it.

- **MCP (Model Context Protocol).** MCP specifies how tools and
  context are exposed from external servers to a client. An MCP
  client can register the tools it discovers in a Harnas Tool
  Registry, after which those tools are projected into each
  provider's wire format alongside in-process tools with no further
  ceremony. MCP is concerned with how tools *get to* the harness;
  Harnas is concerned with what the harness *does with them* (when
  to offer them, when to invoke them, how to project tool results,
  how to compact them).
- **OpenTelemetry and similar trace formats.** The Observation bus
  in `13-observation.md` is the normative in-process emission point.
  Subscribers adapt those emissions to whatever external trace
  format a deployment requires; the adapter is out of scope here.

## Reading Order

1. [`00-conventions.md`](00-conventions.md) — RFC 2119, vocabulary,
   normative-vs-informative.
2. **This document** — the architectural frame.
3. [`02-provider-contract.md`](02-provider-contract.md) — the wire-format
   seam below Harnas.
4. [`conformance/README.md`](conformance/README.md) — fixtures, mocks,
   and the reference fixture set.

Sections 03 onward are forthcoming.

## Version

This specification is at version **0.1.0**. All normative statements
remain subject to change before 1.0.0.
