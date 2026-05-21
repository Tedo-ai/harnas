# Adopter Helper Surfaces

Status: informative. This document describes helper APIs the reference
implementations ship for downstream agents. These helpers are not normative
spec primitives; implementations may name them differently or omit them.

Real downstream agents tend to repeat the same glue around the Harnas
substrate. The helpers below capture the parts that are broadly reusable while
leaving product policy, UI shape, and orchestration in the downstream agent.

## Runtime assembly

The runtime helper is the common "create or resume a runnable Session" path:

- load a Manifest
- build the provider/projection/ingestor/registry bundle
- optionally load an existing Session JSONL
- merge caller metadata into the Session
- expose an Agent or AgentLoop using the assembled parts
- save the Session again

This reduces boilerplate and makes provider/projection/ingestor pairing harder
to get wrong.

## Transcript projection

The transcript helper projects a Log into UI-neutral semantic items:

- user messages
- assistant messages, including reasoning when present
- tool uses and tool results
- provider/runtime errors
- optional annotations
- compaction/revert/summary bookkeeping

It does not prescribe visual treatment. A web UI, terminal UI, and JSON
inspector can render the same transcript items differently.

## Dynamic tool snapshots

Agents that discover tools dynamically, for example from skills or MCP servers,
should snapshot the resulting descriptors before a Session starts. The helper
returns the registry's public descriptors plus optional skills/MCP metadata for
storage in Session metadata.

The purpose is replay cleanliness: a saved Session should say which dynamic
tools were available when the run began, even if the external source changes
later.

## Attachment storage

Agents that accept images, PDFs, or other binary inputs need a place to
store bytes outside the Log while keeping the Log replayable. The
reference implementations expose an AttachmentStore-style helper with
this language-neutral shape:

```text
AttachmentStore {
  put(bytes, media_type) -> AttachmentReference
  get(uri) -> (bytes, media_type)
  delete(uri) -> void
  exists(uri) -> bool
  list_referenced(log) -> [uri, ...]
}

AttachmentReference {
  uri: string
  media_type: string
  byte_size: int
  sha256: string
}
```

Attachment URIs use the `attachment://<id>` scheme. The id portion is
opaque: consumers must not parse it or assume it is a hash, UUID, or
filename. Only the configured store resolves the URI.

Runtime helpers should accept an optional `attachment_store` parameter.
If none is supplied, local CLI-style runtimes use a filesystem-backed
store rooted next to the Session file. Provider Projections receive the
store as a dependency so they can resolve `source.kind: "ref"` content
blocks at projection time. Future ingestors that produce attached
assistant content use the same store to persist bytes and emit
`attachment://` references.

## Cross-session projections

Delegating agents create multiple persisted Sessions connected by
`agent_spawn` and `agent_result` edges. Reference implementations should
ship helpers that compute the common operator views from those Session
Logs:

- `delegation_tree(session_id)` for recursive parent/child structure
- `descendant_timeline(session_id)` for a timestamp-ordered event stream
  across the session and its descendants
- `open_children(session_id)` for spawn ids without terminal results
- `descendant_usage(session_id)` for aggregate token usage

These helpers load child Sessions through the host application's
persistence backend. Filesystem runners usually keep children alongside
the parent Session file; database-backed adopters usually resolve by
foreign key. The helpers are views only: they do not create a global Log
and they do not copy child internals into the parent.

## Dependency-light embedding

Keep the core implementation dependency-light. The agent runtime should embed
into any host application -- a Rails app, a Sinatra app, a background job, a CLI
script -- without conflicting with the host's web stack. Web inspector,
dashboard, and operator UI dependencies must be optional. A consumer who does
not use the web inspector should never need to install a web server.

## Still downstream for now

The following are intentionally not pulled into core yet:

- MCP transport adapters
- approval UI flows
- product-specific introspection tools
- artifact runtime conventions
- product-specific subagent orchestration policies

These need more cross-agent evidence before becoming reference helpers or
normative spec text.
