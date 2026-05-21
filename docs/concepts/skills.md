# Skills

A **skill** is a named, lazily-loaded block of context. The agent's system
prompt advertises which skills exist; the agent loads a skill's full body
on demand by calling the `load_skill` built-in.

## Why skills exist

Agent system prompts get heavy fast. Every domain convention, every coding
standard, every workflow rule that "the agent should know" wants to live in
the system prompt — until the prompt is 30,000 tokens of mostly-unused
context.

Skills invert this. The system prompt advertises what skills are available
in one line each:

```
## Skills

- `git_workflow`: Branching, commit, and PR description conventions for
  this repo
- `python_style`: Project Python conventions and linting rules
- `code_review`: Internal code review checklist
```

The agent reads this index. When a user asks "help me write a PR
description," the agent recognizes the `git_workflow` skill is relevant,
calls `load_skill({ name: "git_workflow" })`, and gets the full body as a
tool result. Context is loaded only when needed.

## How they work

Skills live as markdown files in a configured directory (defaults to
`skills/` relative to the agent's working directory). Each file optionally
has YAML frontmatter:

```markdown
---
name: git_workflow
description: Branching, commit, and PR description conventions for this repo
---

Use short topic branches off `main`.

Commit messages: present tense, concise, no Co-Authored-By unless the user
asks.

PR descriptions should include a Summary section and a Tests section.
```

At session start, the harness scans the skills directory, builds the
canonical `## Skills` index, and appends it to the system prompt. The
manifest declares the `harnas.builtin.load_skill` tool. The agent does the
rest.

## What `load_skill` returns

The skill's full body, with frontmatter stripped (unless configured
otherwise). If the agent asks for an unknown skill, it gets a clear error
in the tool result; no crash.

## What skills are NOT

- They're not RAG. Skills are static markdown files curated by humans, not
  retrieval results from a vector store.
- They're not multi-turn. The agent loads a skill once and works with the
  content; it doesn't navigate or paginate skills mid-call.
- They're not tools. A skill loads instructions; a tool performs an action.

## When to use skills

- You have repeated context that applies to *some* sessions but not all.
- You have multiple distinct conventions that compete for system-prompt
  space.
- You want users to be able to add new context without redeploying the
  agent (drop a markdown file into the skills directory).

## When NOT to use skills

- The context applies to *every* session — put it in the system prompt
  directly.
- The context is dynamic per-call (depends on the user's request) — that's
  what tools or projections are for.
- The "skill" is really a workflow with side effects — that's a tool.

## See also

- [`informative/skills.md`](../../informative/skills.md) — the formal spec
- [Tools and built-ins](./tools-and-built-ins.md) — including `load_skill`
- [MCP](./mcp.md) — for dynamically discovered external tools (related but distinct)
