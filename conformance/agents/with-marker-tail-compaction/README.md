# with-marker-tail-compaction

Exercises the compaction family: a `MarkerTail` strategy with
`max_messages=4, keep_recent=2` runs on `:pre_projection` through
a 4-prompt conversation.

After the third turn, the Log reaches 5 visible message events and
the strategy's trigger condition (`messages.size > 4`) fires.
`:compact` event replaces the first 3 events with the fixed marker
`[snipped 3 earlier messages]`. Later turns continue normally.

Conformance-relevant properties checked by this fixture:

- Strategy installation via manifest actually affects the Log
- `:compact` Mutation Events carry the normative marker string
  (from `spec/strategies/compaction/marker-tail.md`)
- Tool-pair safety (`Helpers.tool_pair_safe_range`) doesn't trip —
  there are no tool_use/tool_result pairs here
- Idempotency — the strategy doesn't re-compact on subsequent turns
  (compacted events are excluded from its trigger count)
