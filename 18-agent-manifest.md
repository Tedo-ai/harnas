# 18 — Agent Manifest

This document specifies the **Agent Manifest**: a declarative,
language-neutral JSON format for describing a Harnas agent. A
manifest fully determines an agent's behavior at Layers 1 and 2
of the specification (see `00-conventions.md` §"Specification
Layers"); two conformant implementations loading the same
manifest against the same scripted inputs MUST produce
byte-identical Logs.

The manifest is the artifact that makes Harnas language-neutral
in practice, not just in principle. Conformance fixtures under
`spec/conformance/` reference manifests; benchmark scenarios
reference manifests; organizations author their agents as
manifests and run them in whatever language their runtime
supports.

This specification defines **Manifest v0.1** — a minimum viable
format covering provider, tools, canonical strategies from the
shipped families (Compaction, Permission), and an optional
system prompt. Additional fields (`stop_conditions`, `scope`,
`effect`) are enumerated in §"Forthcoming in v0.2+".

## Document shape

**R1.** A manifest MUST be a single JSON document whose top level
is an Object. The Object MUST carry a `harnas_version` field
identifying the manifest spec version. v0.1 is the first
supported version.

**R2.** A manifest MUST validate against the JSON Schema at
`spec/schemas/agent-manifest.schema.json`. Where prose in this
document and the schema disagree, the schema governs.

## Fields (v0.1)

### `harnas_version` (required)

String. Identifies the manifest spec version. v0.1 accepts
exactly the string `"0.1"`.

### `name` (required)

String. A non-empty human-readable identifier for the agent.
Does not affect behavior; used for logging and display.

### `system` (optional)

String. A system prompt the runtime injects into every provider
request. If present, it MUST be non-empty.

**R2b.** When `system` is present, a runtime MUST project it into
the provider-specific system-message slot:

| Provider | Projection behavior |
|---|---|
| `anthropic` | Top-level `system` field on the request body. |
| `openai` | A `{ "role": "system", "content": <text> }` message prepended to `messages[]`. |
| `gemini` | A top-level `systemInstruction: { parts: [{ text: <text> }] }` field on the request body. |
| `mock` | Uses the Anthropic shape (the mock uses the Anthropic projection pair). |

**R2c.** The system prompt is not an Event. It does not appear in
the Log. It is a static attribute of the projection: two
consecutive turns of the same Session receive the same system
prompt unless the manifest is reloaded. If an application needs
per-turn system-prompt variation, it SHOULD model that variation
as user-message events or as a canonical strategy, not as a
mutation of the `system` field.

### `provider` (required)

Object. Selects the Layer 1 Projection + Provider + Ingestor
triplet and the model-specific parameters.

| Field | Type | Required | Description |
|---|---|---|---|
| `kind` | String | yes | One of `"anthropic"`, `"openai"`, `"gemini"`, `"mock"` |
| `model` | String | yes* | Model identifier for the provider |
| `max_tokens` | Integer | yes | Positive integer; upper bound on response length |

\* `mock` provider does not require `model`; it is ignored if present.

A runtime MUST resolve `kind` to the matching Projection, Provider,
and Ingestor from Layer 1 of its implementation. If the runtime
does not support the requested `kind`, it MUST reject the manifest
at load time with a clear error.

### `tools` (required, possibly empty)

Array of Objects. Declares the tools the agent may invoke. Each
tool Object:

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | String | yes | Non-empty, unique within the `tools` array |
| `handler` | String | yes | Symbolic reference to the implementation; the runtime resolves against its handler map |
| `description` | String | yes | Tool description, passed to the provider |
| `input_schema` | Object | yes | JSON Schema describing the tool's argument shape |

**R3.** A runtime MUST resolve every `handler` string to a
callable implementation via a handler map supplied by the
consumer. If any `handler` is unresolved at load time, the
runtime MUST reject the manifest.

**R4.** Tool handlers are a Layer-3 concern (they live in the
consumer's code). The manifest specifies only the symbolic
reference; the consumer provides the implementation. This
preserves the language-neutrality of the manifest.

### `strategies` (required, possibly empty)

Array of Objects. Declares the canonical strategies (Layer 2) to
install. Each strategy Object:

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | String | yes | Canonical strategy name, e.g. `"Compaction::MarkerTail"` |
| `config` | Object | no | Configuration passed to the strategy; MUST match the strategy's Configuration section in its spec stub |
| `on_error` | String | no | Hook invocation error policy; one of `"isolate"` (default) or `"fail_turn"` |

**R5.** A runtime MUST resolve every `name` to the canonical
strategy declared at `spec/strategies/<family>/<name>.md`. Names
use `Family::Name` format matching the spec stub directory
structure and the strategy's pseudocode. If the runtime does not
support a requested strategy, it MUST reject the manifest at
load time.

**R6.** Where a strategy's Configuration declares a parameter
typed as a *callable* (e.g. `HumanApproval.prompt`), the
corresponding manifest `config` field MUST be a String carrying a
symbolic reference. The runtime resolves it against a
handler map the consumer supplies at load time. This preserves
R3 of `17-composition-rules.md`: external-world callables are
permitted, but only by symbolic reference in the manifest so the
manifest itself remains portable.

User strategies (Layer 3) are not installable via the manifest
in v0.1. They install in the consumer's code, alongside the
manifest-loaded agent.

### `hooks` (optional)

Array of Objects. Declares arbitrary Hook Handlers to install at
Session start. Each hook Object:

| Field | Type | Required | Description |
|---|---|---|---|
| `point` | String | yes | Canonical Hook Point from `14-hooks.md`, e.g. `":post_tool_use"` |
| `handler` | String | yes | Symbolic reference to the handler implementation |
| `config` | Object | no | Configuration passed to the handler at install time |
| `on_error` | String | no | Hook invocation error policy; one of `"isolate"` (default) or `"fail_turn"` |

**R6b.** A runtime MUST resolve every hook `handler` string to a
callable implementation via its implementation-defined
handler-resolution mechanism. If any hook handler is unresolved at load
time, the runtime MUST reject the manifest with a clear error.

**R6c.** Hook install-time failures (unresolvable handler names,
invalid configuration, or the handler install step raising) fail
manifest loading regardless of `on_error`. Invocation-time failures are
governed by `14-hooks.md` R9.

## Loading semantics

**R7.** A runtime's `load` operation MUST be a pure function of
(manifest, tool_handlers, strategy_handlers, hook_handlers) → (session,
projection, provider, ingestor, strategies_to_install, hooks_to_install). The load
MUST NOT call any Provider, perform any network I/O, or register
any Hooks beyond what the strategies themselves register on
`install`.

**R8.** Installing manifest-specified strategies on the Hooks
registry is a separate, explicit step from loading. A conformant
runtime MUST expose load and install as either separate calls or
an opt-in flag, so the loaded manifest can be inspected without
side effects.

### Manifest immutability

A Manifest is bound to a Session at Session creation. Subsequent
changes to the Manifest source — file edits, configuration UI changes,
environment overrides — do not affect existing Sessions. They apply
only to new Sessions. To apply a new configuration to an in-progress
conversation, fork the Session with the new Manifest. This invariant
preserves replay determinism: any saved Session is reproducible against
its original Manifest, regardless of subsequent edits.

## Example (v0.1)

```json
{
  "harnas_version": "0.1",
  "name": "research_agent",

  "provider": {
    "kind": "anthropic",
    "model": "claude-opus-4-7",
    "max_tokens": 4096
  },

  "tools": [
    {
      "name": "web_search",
      "handler": "acme.tools.websearch.search",
      "description": "Search the web for a query and return titles + URLs",
      "input_schema": {
        "type": "object",
        "properties": { "q": { "type": "string" } },
        "required": ["q"]
      }
    }
  ],

  "strategies": [
    { "name": "Compaction::MarkerTail",
      "config": { "max_messages": 20, "keep_recent": 10 } },
    { "name": "Permission::DenyByName",
      "config": { "names": ["shell"] } }
  ],

  "hooks": [
    {
      "point": ":post_tool_use",
      "handler": "acme.audit.ToolUseLogger",
      "config": { "endpoint": "https://audit.example.test/events" },
      "on_error": "isolate"
    }
  ]
}
```

## Forthcoming in v0.2+

The following fields are reserved for future manifest versions.
v0.1 consumers encountering them MUST reject the manifest.

- **`stop_conditions`** — a declarative tree describing when the
  agent loop terminates. Requires a canonical Termination strategy
  family (not yet in the catalog).
- **`scope`** (on permission strategies) — per-tool scoping so
  e.g. `HumanApproval` only fires for specific tool names. Requires
  scope-aware permission strategies.
- **`effect`** / capability metadata on tools — requires a
  canonical Capability event family.

## Versioning

**R9.** The manifest shape is versioned with the `harnas_version`
field. A conformant runtime MUST reject a manifest whose version
is not in its supported-versions list. Major-version changes are
breaking; minor-version additions MUST be backward-compatible
within a major version (unknown fields added in minor versions
MUST NOT be required by v0.1 runtimes).

## Why this document exists

[informative]

A spec that fully specifies machinery (Layer 1) and canonical
strategies (Layer 2) but has no way to describe a full agent in
its own vocabulary isn't language-neutral in practice. Every
consumer would describe their agents in their language's native
constructs, and cross-language conformance would be a manual
comparison between two programs.

The manifest closes that gap. An agent is one JSON file. Two
conformant runtimes load it and behave identically (given
identical scripted inputs). Conformance becomes a file diff;
benchmarks become file-driven scenarios; organizations swap
runtime languages without rewriting their agents.

v0.1 is deliberately small — just enough to describe the agents
we can already build with shipped Layer 2 strategies. Future minor
versions may add optional fields, but conformant runtimes must ignore
unknown fields they do not understand unless the manifest version is
outside their supported range.
