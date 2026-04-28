# ToolOutputCap

**Family:** Compaction

**Selection:** Targeted (`:tool_use` / `:tool_result` pairs whose
result payload exceeds a byte threshold).
**Replacement:** PrefixWithNote (the summary carries a leading slice
of the original output plus a note recording the original and capped
sizes and the tool name).
**Trigger:** PayloadSize (strict `output.bytesize > max_bytes`).

**Purpose:** Bound the context cost contributed by a single
oversized tool result without waiting for an overall message-count
or token-count threshold to trip a whole-conversation compactor.
Empirical surveys of production harnesses name oversized tool
outputs as the single largest driver of runaway context cost; this
strategy is the canonical targeted trim.

## Composed of

- **Hook:** `:pre_projection`
- **Predicate:** any effective `:tool_result` whose
  `payload[:output].bytesize` exceeds `max_bytes`
- **Action:** `Actions::Compact` with `replaces` set to the
  `[tool_use_seq, tool_result_seq]` pair, sorted

## Algorithm (normative)

```
algorithm ToolOutputCap(max_bytes, prefix_bytes,
                        summary_format = DEFAULT):

  REQUIRES: max_bytes > 0
  REQUIRES: 0 <= prefix_bytes <= max_bytes

  install handler at hook :pre_projection

  on :pre_projection(session):
    effective := Mutations.apply(session.log)
    use_index := { payload.id -> seq for :tool_use in session.log }

    for result in filter(effective, e.type = :tool_result):
      if bytesize(result.payload.output) <= max_bytes:
        continue

      use_seq := use_index[result.payload.tool_use_id]
      if use_seq is undefined:
        continue  // defensive — a tool_result without a tool_use
                  // is structurally invalid but must not crash

      tool_name := tool_use_with_seq(session.log, use_seq).payload.name
      prefix    := byte_bounded_slice(result.payload.output, prefix_bytes)
      summary   := render(summary_format,
                          TOOL     = tool_name,
                          CAP      = max_bytes,
                          ORIGINAL = bytesize(result.payload.output),
                          PREFIX   = prefix)

      Actions.Compact(session,
                      replaces: sort([use_seq, result.seq]),
                      summary:  summary)
```

`byte_bounded_slice(s, n)` MUST return at most `n` bytes of `s`
without splitting a multibyte character. In the reference
implementation this is `s.byteslice(0, n).scrub("")`.

**Normative defaults:**

- `max_bytes`: `4096`.
- `prefix_bytes`: `1024`.
- `summary_format`: the literal string
  `[tool `$TOOL` output capped at $CAP bytes (original $ORIGINAL bytes)]\n$PREFIX`.
  The tokens `$TOOL`, `$CAP`, `$ORIGINAL`, and `$PREFIX` MUST be
  substituted verbatim. Implementations exposing a `summary_format`
  parameter MUST use this exact string as the default.

## Idempotence

The strategy depends only on events visible in `Mutations.apply(log)`.
Once a tool pair is compacted, its two seqs are shadowed by the
resulting `:compact` mutation and no longer appear in the effective
stream; subsequent `:pre_projection` invocations therefore do not
re-compact the same pair. Re-installing the strategy on an already-
compacted Log is a no-op.

## Semantic trade-off

The current `:compact` Mutation synthesizes a `:summary` event in
place of the lowest replaced seq, which projects as a `role: user`
message (or equivalent per-provider user-role shape). Compacting a
tool-call pair therefore collapses the assistant's tool_use and the
harness's tool_result into a single user-role summary in the
projected request body.

For genuinely oversized outputs (e.g., tens of kilobytes from a
file read or a web scrape), this is often the desired behavior: the
model does not need to re-see a multi-kilobyte payload on every
subsequent turn. For deployments that require tool-chain-preserving
truncation — where the assistant's tool_use must remain visible to
the model alongside a *shortened* tool_result — a different mutation
family (a future `:tool_output_truncate` whose applier replaces a
`:tool_result`'s output in place) is the right vehicle. No such
mutation is specified in 0.1.

## Failure modes

- **Missing matching `:tool_use`.** A `:tool_result` whose
  `tool_use_id` does not appear as the `id` of any `:tool_use` in
  the Log is structurally invalid and SHOULD NOT occur; if it
  does, the strategy MUST skip that event rather than raise.
- **Empty output.** `bytesize == 0` never triggers; `max_bytes` is
  a strict lower exclusive bound.
- **Multibyte output near the boundary.** The prefix slice MUST
  preserve valid UTF-8; implementations using byte-oriented
  slicing MUST scrub invalid trailing partial characters.
- **Concurrent installation with whole-conversation compactors.**
  ToolOutputCap may compact a pair that a MarkerTail/TokenMarkerTail
  would also have compacted on the same pass. The order in which
  `:pre_projection` handlers run is registration order; the first
  one to append a `:compact` shadows events from the second's
  perspective, making the second a no-op for the already-compacted
  seqs. Both outcomes are conformant.

## Tuning

| Parameter      | Purpose                                    | Typical range |
|----------------|--------------------------------------------|---------------|
| `max_bytes`    | Threshold above which a result is capped   | 1024 – 16384  |
| `prefix_bytes` | Leading bytes preserved in the summary     | 128 – 4096    |

Larger `prefix_bytes` preserves more of the tool's immediate
response to the model; smaller values aggressively reclaim tokens
at the cost of obscuring what the tool actually returned.
