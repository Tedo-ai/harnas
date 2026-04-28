# DenyByName

**Family:** Permission

**Purpose:** Refuse every `:tool_use` whose tool name appears in a
configured deny-list. Pure name-match; does not inspect arguments.

## Composed of

- **Hook:** `:pre_tool_use`
- **Predicate:** `tool_use.payload[:name]` is in the configured deny-list
- **Action:** `Actions::Refuse(reason: <formatted>)` on match, otherwise
  `Actions::Allow`

## Algorithm (normative)

```
algorithm DenyByName(names,
                     reason_format = "tool $NAME is on the deny-list"):

  REQUIRES: names is a non-empty set of strings

  denylist := set_of(names)
  install handler at hook :pre_tool_use

  on :pre_tool_use(tool_use):
    name := tool_use.payload.name
    if name in denylist:
      reason := reason_format with "$NAME" replaced by inspect(name)
      return Actions.Refuse(reason: reason)
    else:
      return Actions.Allow()
```

**Normative defaults:**

- `reason_format`: the literal string `tool $NAME is on the deny-list`.
- `inspect(name)` produces the name wrapped in double quotes with
  standard string-escape semantics. For `name = shell`, `inspect`
  produces `"shell"`. Implementations MAY use a language-idiomatic
  inspect function as long as the result is: a double-quoted form of
  the name with backslash-escaped interior quotes and backslashes.

## Configuration

| Parameter | Type | Default | Description |
|---|---|---|---|
| `names:` | Array<String> | *(required, non-empty)* | Tool names to refuse |
| `reason_format` | String | *(see Algorithm)* | `$NAME` substitution |

The constructor raises `ArgumentError` when `names` is missing,
empty, non-Array, or contains a non-String element.

## Arbitrary choices

- **Match basis:** strict equality on the tool's `name` string. No
  glob, no regex, no namespace expansion. If you need pattern
  matching, write a custom strategy (still ~30 lines — it's just
  Ruby plus the shared Actions).
- **Argument awareness:** none. A tool named `shell` is denied
  whether it was asked to run `ls` or `rm -rf /`. For
  argument-aware gating use a custom strategy or stack DenyByName
  with a more specific one.
- **Reason text:** includes the matched tool name in human-readable
  form (`tool "shell" is on the deny-list`). The reason is surfaced
  in the appended `:tool_result` (`error: "denied by hook: <reason>"`)
  so the model sees *why* the call was refused.
- **Storage:** the deny-list is kept as a Set internally for O(1)
  lookup, but configured as an Array for ergonomic literals.
- **Composition:** any-deny-wins under R6 of `14-hooks.md`. Stacking
  multiple DenyByName instances unions the deny-lists.

## When to use

- You have a small, known set of categorically forbidden tools (e.g.
  destructive shell commands, network-egress tools in a sealed
  scenario).
- You want a zero-prompt, zero-LLM-call permission strategy that
  benchmarks at near-zero latency.
- You want a coarse first-pass filter and intend to stack a finer
  argument-aware strategy underneath.

## When NOT to use

- The forbidden behavior depends on arguments, not just the tool
  name. Use a custom strategy or stack with one.
- Tool names in your registry are dynamic / namespaced (e.g. MCP
  routing). Use a strategy that understands the namespacing instead.

## Implementation

`reference/lib/harnas/strategies/permission/deny_by_name.rb` — plain
Ruby, ~30 lines.
