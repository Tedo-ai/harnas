# MCP (Model Context Protocol)

Harnas integrates with MCP servers as a way to consume tools that already
exist outside the agent's process — typically a separate service maintained
by a different team, written in a different language, or shared across
multiple agent products.

## When MCP is the right answer

Use an MCP adapter when:

- You're connecting to an existing standalone MCP server that you didn't
  build and don't control. (The editorial Rails pipeline's `editorial-ai`
  server is a textbook case.)
- The tool surface is exposed across a process or language boundary, and
  you want consistent semantics regardless of which client connects.
- The tool surface is maintained as a separate product and updated
  independently of your agent.

## When MCP is the wrong answer

If you're building an agent into your own application (a Rails app, a Go
service, a Python pipeline), and the "tools" the agent needs are just
things your application already does — fetch a record, call a service,
trigger a job — **don't go through MCP**. Register those operations as
native tool handlers in the manifest.

MCP is a cross-boundary protocol. Going through it when both sides are in
the same process means:

- JSON serialization round-trips for every call
- Loss of native object identity (ActiveRecord rows become hashes)
- Loss of transaction context, request context, and other in-process state
- A separate process or HTTP endpoint to maintain alongside the agent

For in-process integrations, native tool handlers are the right pattern.
For cross-process or cross-vendor integrations, MCP is the right pattern.

## How Harnas consumes MCP

The adapter ships in `harnas-go`, `harnas-ruby`, and `harnas-python` (TS
to follow). API surface is identical across implementations — adjust for
language idiom only.

**Two transports:**

- **HTTP** — JSON-RPC 2.0 over HTTP POST. Used when the MCP server is a
  long-running service reachable over the network.
- **stdio** — JSON-RPC over a spawned subprocess's stdin/stdout. Used when
  the MCP server is a local executable.

**Public surface (Ruby example):**

```ruby
mcp = Harnas::MCP.connect(
  url: "http://localhost:3001",
  server_name: "editorial-ai",
  headers: { "Authorization" => "Bearer #{token}" }
)

runtime = Harnas::Runtime.build(
  manifest: manifest_hash.merge("tools" => mcp.tools + other_tools),
  tool_handlers: mcp.tool_handlers
)
```

`mcp.tools` returns translated Harnas tool descriptors (with names
namespaced as `<server_name>.<tool_name>`). `mcp.tool_handlers` returns
the dispatch lambdas. Both go into the manifest and runtime.

## What the adapter handles

- JSON-RPC `initialize` handshake on first use (lazy — no work happens
  until `tools()` is called).
- `tools/list` to discover available tools.
- Tool descriptor translation: MCP's `inputSchema` becomes Harnas's
  `input_schema`; names are namespaced; the `mcp_passthrough.<server>`
  handler sentinel routes calls back through the MCP client.
- `tools/call` for every tool invocation.
- Content flattening: MCP returns typed content arrays (text, image,
  resource); the adapter joins text, summarizes binary content as
  placeholders, and returns a single string for the agent.
- Degraded startup: if the MCP server fails to respond, the adapter logs
  a warning, returns an empty tool list, and marks itself degraded. The
  agent runs without those tools rather than crashing.

## What the adapter does not do

- It doesn't manage credentials. Use the [`credential/proxy`](./strategies-and-hooks.md)
  strategy or pass `headers:` explicitly.
- It doesn't reconnect automatically. A stdio subprocess that exits is
  not restarted.
- It doesn't proxy MCP resources or prompts (the other MCP primitives).
  Only tools — that's the only primitive useful for agent loops.
- It doesn't run an MCP server. Harnas is a client, not a host. If you
  want to expose your agent's tools to OTHER MCP clients, that's a
  product-level concern.

## Multiple servers

You can connect to multiple MCP servers in the same agent. Pass each
client's `tools` and `tool_handlers` into the runtime:

```ruby
mcp_a = Harnas::MCP.connect(url: editorial_url, server_name: "editorial-ai")
mcp_b = Harnas::MCP.connect(url: sales_url,     server_name: "sales-mcp")

runtime = Harnas::Runtime.build(
  manifest:      manifest_hash.merge("tools" => mcp_a.tools + mcp_b.tools),
  tool_handlers: mcp_a.tool_handlers.merge(mcp_b.tool_handlers)
)
```

Names don't collide because each tool is namespaced by `server_name`.

## See also

- [`informative/mcp.md`](../../informative/mcp.md) — the formal spec
- [Strategies and Hooks → credential/proxy](./strategies-and-hooks.md) — for authenticated MCP servers
- [Tools and built-ins](./tools-and-built-ins.md) — for native (non-MCP) tools
