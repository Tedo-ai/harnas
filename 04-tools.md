# 04 — Tools

This document specifies the **Tool contract** — what a Tool is, how the
harness discovers and executes them, and how tool calls flow through
the event-sourced substrate (`01-overview.md`).

## Summary

A **Tool** is a named, invocable capability. The assistant requests
tool calls in its response; the harness executes them via a **Runner**
against a **Registry** of registered tools; each execution is recorded
as a `:tool_result` Event referencing the originating `:tool_use`
Event.

Tool calls flow as pairs of Events in the Log:

    :tool_use { id, name, arguments }     (from the assistant)
    :tool_result { tool_use_id, output?, error? }  (from the harness)

The agent loop continues until the assistant returns a response whose
stop_reason is not `:tool_use`.

## Tool Value

**R1.** A Tool MUST expose at minimum:

- `#name` — a non-empty String identifier unique within its Registry.
- `#description` — a String, shown to the model as part of the tools
  list in the projected request.
- `#input_schema` — a Hash describing the tool's input contract.
  Providers use this for function-calling schema validation; the
  reference implementation uses JSON Schema shape.
- `#config` — an optional JSON-serializable object carrying
  implementer-opaque configuration for the handler. When absent it is
  treated as `{}`.
- `#call(arguments)` — invoked by the Runner with the (symbol-keyed)
  arguments Hash; MUST return a String (the tool's output).

**R2.** Tools MAY raise `StandardError` from `#call`; the Runner MUST
catch such errors and record them as failure `ToolResult` events
rather than propagating them into the harness.

**R3.** A tool entry MAY declare an optional `config` object. The
runtime MUST treat `config` as implementer-opaque: it MUST NOT
interpret the value semantically, MUST preserve it through Session
save/load byte-identically as part of the Session's manifest snapshot,
and MUST make it available to the resolved handler at invocation. The
exact handler calling convention is implementation-defined. `config`
MUST be JSON-serializable.

## Registry

**R4.** A Harnas implementation MUST provide a Registry mechanism that
stores Tools by name and supports:

- registration (idempotent or erroring on duplicate — MAY differ by
  implementation)
- lookup by name
- enumeration of all registered Tools (for the Projection's tool list)

The reference implementation's `Tools::Registry` raises
`DuplicateToolError` on re-registration and `UnknownToolError` on
missing lookup.

## Tool Use and Tool Result Events

**R5.** A `:tool_use` Event's payload MUST contain:

- `id:` — a non-empty String; the correlation identifier assigned by
  the provider (or synthesized by the Ingestor when the provider does
  not supply one).
- `name:` — the tool's registered name (String, non-empty).
- `arguments:` — a Hash (the parsed input the assistant intended to
  pass). Keys SHOULD be symbol-keyed when produced by the Ingestor for
  consistency with other Event payloads.

**R6.** A `:tool_result` Event's payload MUST contain:

- `tool_use_id:` — a non-empty String referencing the `id` of the
  `:tool_use` Event this result fulfills.
- Exactly one of:
  - `output:` — a String containing the tool's successful output, or
  - `error:` — a String error message describing the failure.

**R7.** A `:tool_use` Event's payload `id` MUST be unique within a
Session. Implementations whose underlying provider does not supply
unique ids (for example, providers whose function-call parts carry
only a name) MUST synthesize ids that satisfy this requirement. The
`tool_use_id` field on `:tool_result` Events MUST refer to the same
id; correlation by id is the canonical way the AgentLoop pairs
`:tool_use` with `:tool_result`.

## Runner

**R8.** A Harnas implementation MUST provide a Runner that, given a
`:tool_use` Event and a Registry, executes the named tool and appends
a corresponding `:tool_result` Event to the Log. On any `StandardError`
raised during execution, the Runner MUST still append a `:tool_result`
Event, using the `error:` payload field. The Runner SHOULD emit the
canonical `:tool_invoked` observation event (see
`13-observation.md`) with outcome, duration, and (on failure) the
exception.

## Projection Responsibilities

**R9.** A Projection that supports tools MUST:

- Emit the provider-specific tool list (name, description, input
  schema) when the Session carries a non-empty Registry.
- Translate `:tool_use` Events into the provider's corresponding
  request content block type.
- Translate `:tool_result` Events into the provider's corresponding
  content block type, including a failure indicator when the result
  carries an `error:` field.

Per-provider wire shapes are provider-specific and are captured
normatively by the conformance fixtures under
`spec/conformance/fixtures/tool-echo/`.

## Ingestor Responsibilities

**R10.** An Ingestor that supports tools MUST, for each provider
response that contains tool-call data, emit zero or more `:tool_use`
Event-args in content-array order, alongside the `:assistant_message`
event. The `:assistant_message`'s `stop_reason` MUST reflect the
provider's turn-ending vocabulary: `:tool_use` when the turn ended
because the assistant requested tool calls, or the appropriate
normalized Symbol otherwise.

## The Agent Loop

[informative]

A concrete agent loop using the primitives above:

```
loop do
  request = projection.call(session.log)
  response = provider.call(request)
  ingestor.call(response).each { |e| session.log.append(**e) }

  last_assistant = session.log.reverse_each.find { |e| e.type == :assistant_message }
  break if last_assistant.payload[:stop_reason] != :tool_use

  pending = pending_tool_uses(session.log)
  break if pending.empty?
  pending.each { |tu| runner.run(tu, into_log: session.log) }
end
```

Termination is strictly on the neutral `stop_reason` vocabulary; an
implementation MAY add loop bounds (max turns, deadline) as additional
termination conditions. The `bin/smoke_tool.rb` reference script caps
at 5 turns by default.

## Conformance

The `tool-echo` case under `spec/conformance/fixtures/tool-echo/`
records a canonical two-turn round-trip (tool call + tool result +
terminal text) against each supported provider. Any Harnas
implementation SHOULD be able to replay these fixtures through its own
Mock provider and produce structurally equivalent Log contents.

## Manifest Tool Config

Manifest tool entries may carry `config` for implementer-specific
tool binding data:

```json
{
  "name": "send_email",
  "handler": "tedo.operations.invoke",
  "description": "Send an email via the configured operation.",
  "input_schema": { "type": "object", "properties": {} },
  "config": {
    "operation_key": "mailbox.send",
    "resource_binding": { "mailbox_id": "mailbox_123" },
    "idempotency_policy": "key_in_payload"
  }
}
```

The runtime stores and preserves this object, but does not define or
interpret its contents. Handler resolution and handler calling
conventions remain implementation-defined.

## Out of Scope

The following tool-related concerns are specified elsewhere:

- Tool *discovery* strategies (deferred loading, MCP routing, lazy
  expansion by name) — `14-hooks.md` via
  `:pre_projection` hook handlers.
- Tool *permission* policies (allow, deny, require approval) —
  `14-hooks.md` via `:pre_tool_use` hook handlers.
- Tool *concurrency* (parallel safety analysis, partition batching) —
  `14-hooks.md` via custom scheduling hook handlers.

All three are strategy concerns that plug into the Hooks layer rather
than being part of the tool contract itself.
