# Skills Convention

This document is informative. It describes a recommended convention for
Harnas implementations and downstream agents that want to support a
"skills" pattern: named Markdown modules that are loaded into context on
demand.

The convention is intentionally small. A skill is ordinary Markdown with
frontmatter, exposed to the model through a normal Harnas Tool. The Log
records the tool call and tool result exactly like any other tool use;
the specification does not add a new Event type for skills.

## Skill Files

Skill files SHOULD be Markdown files with YAML-style frontmatter:

```markdown
---
name: git_workflow
description: Branching, commit, and PR description conventions for this repo
---

Use short topic branches named after the work...
```

Recommended frontmatter fields:

- `name` (required): string, `snake_case`, matching the filename minus
  `.md`. The reference `load_skill` built-in rejects names not matching
  `^[a-z][a-z0-9_]*$`; custom skill loaders SHOULD enforce the same
  rule to prevent path traversal and keep names interoperable.
- `description` (required): one-line string used in the system-prompt
  index.
- `triggers` (optional): list of strings, useful as hints for
  pre-routers or other surfaces. The `load_skill` tool does not need to
  interpret them.
- `category` (optional): string for grouping larger skill sets.

The body is plain Markdown. This convention imposes no length limit.

## `load_skill` Tool

Implementations that expose skills SHOULD provide a tool shaped like:

```json
{
  "name": "load_skill",
  "description": "Load the body of a named skill",
  "input_schema": {
    "type": "object",
    "properties": {
      "name": { "type": "string" }
    },
    "required": ["name"]
  }
}
```

The handler returns the requested skill body as a plain string. By
convention, leading frontmatter is stripped from the returned body
because the frontmatter has already been represented in the system
prompt index.

Skills with no body return an empty string. This is not an error
condition.

Unknown skill names and read errors should use ordinary Harnas tool
failure behavior: the `:tool_result` Event records the error.

## Agent Shape

A skills-enabled agent SHOULD use a two-part shape:

1. The system prompt includes a skills index listing every skill as
   `name: description`.
2. The agent calls `load_skill(name)` when it judges a skill relevant,
   receives the body, and uses that body in the current turn.

The reference implementations ship a `BuildSkillsIndex` helper (Ruby:
`Harnas::Skills.build_index`; Python: `harnas.skills.build_index`; Go:
`harnas.BuildSkillsIndex`) that emits this canonical system-prompt
section:

```markdown
## Skills

You have access to local skills. The skill index below is enough to answer what skills are available. Do not call `load_skill` just to list skills. Call `load_skill` only when a user request matches a skill and you need its full instructions.

- `git_workflow`: Branching, commit, and PR description conventions for this repo
- `pdf_extract`: Extract structured data from PDFs
- `sql_query`: Write and explain SQL queries
```

Implementations that publish a skills index in the system prompt SHOULD
include text discouraging the model from calling `load_skill` for
listing purposes. Without this guard, models tend to call `load_skill`
once per indexed skill in response to "what skills do I have?".

Implementations MAY include optional frontmatter fields such as
`triggers`, `category`, or future additions in index entries beyond
`name: description`. The model SHOULD treat unrecognized text as
informational.

## Replay

Skill bodies are normally read from disk by the handler at dispatch
time. Implementations MAY snapshot skill bodies for byte-stable replay,
but this convention does not require it.

Consumers should treat skill files as Session dependencies, similar to
files read through a `read_file` tool: changing the file between the
original run and a later replay can change behavior.

## Log Example

A typical skill load remains an ordinary tool round-trip:

```text
seq=0  user_message       "help me write a PR description"
seq=1  assistant_message  ""  (stop_reason=tool_use)
seq=2  tool_use           load_skill(name="git_workflow")
seq=3  tool_result        <body of git_workflow.md, frontmatter stripped>
seq=4  assistant_message  "Here's a PR description following the git_workflow conventions: ..."
```
