# 17 — Composition Rules

This document specifies the **composition rules** for Harnas
strategies: the constraint that every strategy in the catalog is
built using only the atomic operations this specification defines,
and the one legitimate exception for external-world boundaries.

## The core rule

**R1.** A Strategy MUST be implementable using only the atomic
operations of the Harnas specification (enumerated in R2). A
Strategy MUST NOT accept a callable, block, or function parameter
whose purpose is to perform work that is expressible as a
composition of those atomic operations.

**R2.** The atomic operations of the Harnas specification are:

| Operation | Reference | What it does |
|---|---|---|
| `Log.append(event)` | `01-overview.md` | Append an Event to a Log |
| Log iteration | `01-overview.md` | Read Events in order from a Log |
| `Mutations.apply(log)` | `01-overview.md` | Resolve mutation Events into an effective Event sequence |
| `Projection.call(log)` | `01-overview.md`, `02-provider-contract.md` | Pure function: Log → provider-shaped request |
| `Provider.call(request)` | `02-provider-contract.md` | Send a request to a Provider, return the raw response |
| `Ingestor.call(response)` | `02-provider-contract.md` | Pure function: raw response → Array of Event args |
| `Hooks.on` / `Hooks.invoke` / `Hooks.off` | `14-hooks.md` | Register, fire, and remove Hook Handlers |
| Actions (`Compact`, `Revert`, `Allow`, `Refuse`) | `16-actions.md` | Canonical discrete effects Hook Handlers produce |

A Strategy that wants to do anything expressible in terms of R2
MUST express it using R2. Anything that cannot be expressed using
R2 is either (a) an external-world boundary (see R3) or (b) evidence
of a gap in R2 that a future spec version should close.

## External-world boundaries

**R3.** A Strategy MAY accept a callable parameter if and only if
the callable's purpose is to interact with a system that is outside
the Harnas specification. External systems include:

- a human (keyboard, clickable UI, voice)
- the local filesystem (reading config, writing audit trails outside
  the Log)
- a non-Provider network service (a policy server, a classifier
  endpoint that is not modeled as a Harnas Provider, an OS-level
  sandbox probe)
- a clock or source of randomness that cannot be expressed through
  the existing Log

A callable parameter used for any work that *could* be expressed
through R2 violates R1, regardless of whether the author considers
it "configuration."

## Rationale

[informative]

Without R1, strategies become escape hatches. SummaryTail takes a
`summarizer:` callable; HumanApproval takes a `prompt:` callable;
a caching strategy takes a `key_builder:` callable; a retry strategy
takes a `backoff:` callable — and suddenly the strategy catalog
isn't a vocabulary of compositions, it's a collection of shells
around user-supplied work. Cross-language implementers can't port
what the spec doesn't specify. Benchmarks can't compare strategies
whose bodies are user lambdas.

With R1, the spec is a **complete, composable API**: every strategy
is built out of R2, and the few things that genuinely need an escape
hatch (human input, filesystem, sandbox probe) are narrow, named,
and classified by R3. A reader who wants to know what a strategy
does reads its code and follows R2 names.

## How to apply R1 during strategy authoring

[informative]

When writing a new strategy, ask for each parameter:

1. *Is this data the strategy needs to make decisions (thresholds,
   names, ratios)?* → configuration. No R1 concern.
2. *Is this a callable performing work that uses a Provider,
   Projection, Log, Hook, or Action?* → R1 violation. Replace with
   the actual primitive(s), or propose a missing primitive for the
   next spec version.
3. *Is this a callable whose body reaches into the external world
   (reads a keyboard, hits a classifier URL, queries the filesystem)?*
   → R3 exception. Document the external boundary in the strategy's
   spec stub.

Example: SummaryTail needs to summarize conversation text with an
LLM. The spec already has Projection (build a request), Provider
(call an LLM), and Ingestor (parse the response). A `summarizer:`
callable that bundles those is an R1 violation — replace the
callable with `projection:`, `provider:`, and `ingestor:`
parameters directly. The strategy then uses R2 primitives
throughout, with no escape hatch.

Example: HumanApproval asks a human whether to permit a tool call.
There is no Harnas primitive for "ask a human" because the human
is not modeled by the spec. The `prompt:` callable is an R3
exception; the spec stub records it as "external boundary: human
input."

## Family contracts invoke this rule

**R4.** Each Strategy family's specification (e.g. `05-compaction.md`,
`07-permission.md`, future families) MUST either restate R1 or
reference this document. Family-level specs MAY narrow R3 (e.g.
"permission strategies MAY take a human-facing callable; compaction
strategies MUST NOT") but MUST NOT loosen R1.

## Composing primitives: the sub-Log pattern

[informative]

Many strategies need to run a one-turn Provider interaction for
their own purposes (summarization, classification, self-critique).
The canonical in-spec pattern is to construct a **sub-Log**,
project it, call the Provider, ingest the response, and read the
result from the sub-Log:

```ruby
sub_log = Harnas::Log.new
seed_events.each { |e| sub_log.append(type: e.type, payload: e.payload) }
sub_log.append(type: :user_message, payload: UserMessage.new(text: prompt).to_h)

request  = projection.call(sub_log)
response = provider.call(request)
ingestor.call(response).each { |args| sub_log.append(**args) }

assistant_text = sub_log.reverse.find { |e| e.type == :assistant_message }.payload[:text]
```

The sub-Log is an ordinary Log, not a special primitive. Everything
in this pattern is R2. A strategy that follows this pattern uses the
same Projection/Provider/Ingestor machinery as the main AgentLoop,
so it composes cleanly with streaming, caching, retry, and any
other family that installs on the main Log.

## Versioning

**R5.** R1 through R4 are stable within a major spec version. New
entries MAY be added to R2 (new atomic operations) without a major
version bump; R2 entries MUST NOT be removed or changed without a
major bump.
