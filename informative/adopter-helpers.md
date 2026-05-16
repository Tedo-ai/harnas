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

## Still downstream for now

The following are intentionally not pulled into core yet:

- MCP transport adapters
- approval UI flows
- product-specific introspection tools
- artifact runtime conventions
- subagent orchestration events

These need more cross-agent evidence before becoming reference helpers or
normative spec text.
