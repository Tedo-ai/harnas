# Execution Evidence

This document is informative and provisional Unreleased v0.20 draft
material. It defines a shared vocabulary for recording what an
implementation or host environment says it did around tool execution.
The vocabulary is intentionally small so multiple adopters can describe
sandboxing and process containment without minting parallel schemas. The
shape may change when a second consumer exercises it.

Execution evidence is a fact recorded by the substrate. It is not a
presentation hint and it is not proof that an operating system isolation
mechanism worked. A Log entry can record that the host launched a tool
inside a claimed sandbox or contained process group; it cannot attest that
the kernel enforced that claim.

## Durable Shape

Implementations SHOULD record execution evidence as either:

- an `:annotation` Event, when the evidence describes a runtime action
  adjacent to a tool call; or
- metadata on `:tool_result`, when the evidence is naturally part of the
  tool result.

The recommended annotation payload shape is:

```json
{
  "kind": "execution_evidence",
  "tool_use_id": "toolu_123",
  "backend": "seatbelt",
  "enforced": {
    "filesystem": true,
    "network": false
  },
  "contained": true,
  "detail": "filesystem profile applied; process tree contained"
}
```

`tool_use_id` references the canonical `:tool_use.payload.id` when the
evidence is tied to a specific tool invocation.

`backend` is an open string. Implementations MAY use well-known names
such as `seatbelt`, `landlock`, `job_object`, `container`, or
`namespace`, but consumers MUST tolerate unknown backend names.

`enforced` is a map of isolation axes that the host claims were enforced.
Known axes include `filesystem` and `network`. Future axes can be added
without changing the top-level shape.

`contained` means the process lifecycle was bounded or managed, but does
not imply that filesystem or network access was blocked. For example, a
Windows Job Object may contain a process tree without enforcing a
filesystem sandbox.

`detail` is optional diagnostic text. It MUST be sanitized: no secret
values, request headers, full host-specific paths, usernames, or other
deployment-private data.

## Presentation

Presentation is deliberately not part of this vocabulary. Whether a
surface can render a card, badge, timeline item, or warning is a product
and UI concern. Harnas records execution facts; renderers decide how to
present them.

## Redaction

Execution evidence follows the same redaction rule as
`credential/proxy`: names, classes, counts, and references are allowed;
secret values are not. Implementations MUST NOT append credential values
to the Log or emit them through Observation as part of execution
evidence.
