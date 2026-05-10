# MCP Mapping Convention

This document is informative. It describes a recommended mapping from
Model Context Protocol (MCP) primitives to Harnas primitives for
implementations and downstream agents that consume MCP servers.

The convention does not make MCP part of the Harnas core. MCP transport,
authentication, server configuration, and lifecycle management remain
implementation concerns.

## MCP Tool to Harnas Tool

Discovery happens at Session start:

1. The client connects to an MCP server.
2. The client sends `tools/list`.
3. The server returns a catalog of tools with `name`, `description`,
   and `inputSchema`.
4. The Harnas runtime registers one Harnas Tool per discovered MCP
   tool.

Recommended registration shape:

- Name: `<server>.<tool>`, for example `fs.read_file` or
  `github.list_issues`. Namespacing avoids collisions across servers
  and with built-in tools.
- Description: copied from the MCP tool catalog.
- Input schema: copied from MCP `inputSchema`.
- Handler: a closure that marshals Harnas tool arguments to MCP
  `tools/call`, sends the request to the server, and returns the
  result.

Discovered tools SHOULD be added to the Session's manifest snapshot
metadata before the Session starts. That keeps saved Sessions
inspectable and makes save/load behavior predictable.

If a server becomes unreachable mid-session, tool dispatch should use
ordinary Harnas tool-failure behavior: append a `:tool_result` Event
with `error` set. No MCP-specific Event type is needed.

## MCP Resource to Harnas Tool

An MCP resource can be exposed as a Harnas Tool that returns resource
content. A typical naming pattern is:

```text
<server>.read_<resource_name>
```

Small, always-needed resources MAY instead be loaded into the system
prompt at Session start. Implementations choose which shape fits their
surface.

## MCP Prompt to Skill

MCP prompts map naturally to the skills convention in
[`skills.md`](skills.md).

Each MCP prompt can appear as an entry in the skills index. The
corresponding loader fetches the body via MCP `prompts/get` rather than
reading from disk. From the model's perspective, the shape is the same:
call `load_skill(name)`, receive Markdown content, use it in the turn.

## Server Lifecycle

Discovery SHOULD happen at Session start and remain frozen for that
Session. MCP notifications such as `resources/changed` are useful for
surfaces, but this convention does not require agents to auto-refresh
tools, resources, or prompts mid-session.

Freezing discovery keeps Session behavior reproducible and matches the
general Harnas rule that configuration is bound when the Session starts.

## Out of Scope

This convention does not define:

- Streaming `tools/call` responses. Use buffered calls.
- Authentication or authorization. Those are per-server and
  per-implementation concerns.
- Server configuration schemas. Implementations and agents may use TOML,
  JSON, YAML, environment variables, or another local convention.

