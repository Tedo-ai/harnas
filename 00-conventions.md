# 00 — Conventions

This document defines the conventions used throughout the Harnas specification.
It is itself normative: later sections rely on the terms and rules established here.

## RFC 2119 Keywords

The key words **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, **MAY**,
**REQUIRED**, **RECOMMENDED**, and **OPTIONAL** in this specification are to be
interpreted as described in [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119).
These keywords appear in uppercase when used with this meaning and in lowercase
when used as ordinary English.

## Normative vs Informative

Normative statements are requirements that any conforming implementation of
Harnas must honor. Informative content is explanation, motivation, or example
that helps the reader but does not impose requirements.

In this specification:

- Numbered requirements (e.g. **R1**, **R2**) within a section are normative.
- JSON Schema files under `spec/schemas/` are normative.
- Prose paragraphs outside numbered requirements are informative unless they
  contain an RFC 2119 keyword, in which case the sentence containing that
  keyword is normative.
- Code examples, including all files under `reference/`, are informative.

When normative text and informative text appear to conflict, normative text
governs.

## Vocabulary

The following terms have specific meanings throughout this specification.
Other documents in this specification MUST use these terms only in the senses
defined here.

- **Harness** — the coordinator defined by this specification. A harness
  receives input from a surface, consults one or more providers and tools,
  and produces responses. The harness is the subject of this document.

- **Provider** — an external system that accepts a conversation and returns a
  model-generated response. A provider is typically an LLM API, but the
  specification does not require that providers be language models.

- **Tool** — a named, invocable capability that a provider may request the
  harness execute on its behalf. Tools have declared inputs and outputs and
  are executed by the harness, not by the provider.

- **Session** — one coherent interaction with a harness. A session has
  exactly one Log and a stable identity for the lifetime of the
  interaction.

- **Event** — a single, immutable entry in a Log. Carries a payload
  describing one observation, action, request, response, or mutation.

- **Log** — the append-only, monotonic sequence of Events that constitutes
  a Session. Events are never modified, removed, or reordered after they
  are appended.

- **Mutation** — an Event whose effect is to reshape what later Projections
  produce, by referencing earlier Events (by their stable identity) and
  supplying replacement content. Mutations are themselves Events, and MAY
  be mutated by later Mutations.

- **Projection** — a pure, deterministic function from a Log to a derived
  view, typically the request body sent to a provider on a given turn.
  Different Projections of the same Log MAY exist concurrently for
  different consumers (provider, UI, audit).

- Work in progress: **Surface** — the environment in which a harness runs and through which it
  receives input and delivers output. Examples include a command-line
  interface, a chat application, an IDE extension, and an automated pipeline.
  The specification describes behavior that adapts to the surface.

- Work in progress: **Situation** — the runtime conditions under which a harness operates,
  including trust level, interactivity, resource budgets, and policy
  constraints. A harness MAY modify its behavior based on the situation.

## Schemas and Reference Code

JSON Schema files under `spec/schemas/` are the normative definitions of all
data structures used in this specification. Prose descriptions of these
structures in other specification documents are informative clarifications of
the schemas; where prose and schema disagree, the schema governs.

The Ruby code under `reference/` is a reference implementation of Harnas. It
is informative and does not constrain other implementations. A conforming
implementation MAY differ from the reference implementation in any way that
does not violate a normative statement.

## Specification Layers

Harnas code in any language falls into three distinct layers. Consumers,
implementers, and strategy authors all benefit from treating them as
separate concerns.

### Layer 1 — Harness code

Implements the atomic operations of the specification: `Log`,
`Projection`, `Provider`, `Ingestor`, `Hooks`, `Actions`, `Mutations`,
`Session`, `Events`, `Tools` (see `17-composition-rules.md` R2 for the
full enumeration). The specification describes this layer in full, in
prose and schemas. Behavior is normative; implementation is each
language's concern.

### Layer 2 — Canonical strategy code

Implements a named strategy from `spec/strategies/`. Each canonical
strategy's spec stub contains:

- **A "Composed of" declaration** (Hook × Predicate × Action) — normative.
- **An "Algorithm" pseudocode section** — normative, language-neutral.
  Any implementation whose observable behavior diverges from the
  pseudocode (different triggers, different selection, different
  summary strings, different decision outcomes) is not a conformant
  implementation of that strategy.
- **Configuration parameters with defaults** — the defaults are
  normative. A strategy MAY expose parameters that let callers
  override normative text (e.g. marker strings, prompt templates,
  reason phrases), but the default values MUST match the spec so
  two conformant implementations produce byte-identical behavior
  when used with defaults.

Implementations of canonical strategies are informative. The Ruby
versions under `reference/lib/harnas/strategies/` are one port; a
Python or Go port following the same pseudocode is equally
conformant.

### Layer 3 — User strategy code

An organization's own strategy, not in the specification. Lives
outside the specification, outside the reference implementation,
and outside the canonical catalog. User strategies MUST honor
`17-composition-rules.md` R1 (build from atomic operations; no
harness-internal escape-hatch callables), but are otherwise
unconstrained. The specification explicitly reserves this layer
as the primary product surface: Harnas's value to an organization
is the strategies *it* builds on top, fit to its workflow.

### Separability

**R1.** Implementations MUST make the three layers separable. A
consumer MUST be able to use Layer 1 without adopting any Layer 2
strategies, and MUST be able to use either without depending on
any specific Layer 3 strategies.

In the reference implementation this separability appears as:

- `require "harnas"` loads Layer 1 only.
- `require "harnas/strategies/<family>/<name>"` opts into a single
  Layer 2 strategy.
- Layer 3 strategies live in the consumer's own code tree; they
  `require` Harnas but Harnas does not know about them.

## Versioning

This specification is versioned using [Semantic Versioning](https://semver.org)
applied to the specification as a whole. The current version is **0.8.0**.

All normative statements are subject to change in any pre-1.0.0 release.
Breaking changes to normative statements after 1.0.0 will accompany a major
version increment. The current specification version is recorded in
`spec/VERSION`.
