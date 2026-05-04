# with-strategy-events-sidecar

Exercises strategy Observation events as a sidecar assertion.

The Log shape mirrors `with-marker-tail-compaction`, but the fixture
also records `:strategy_started` and `:strategy_completed` Observation
events. Early `MarkerTail` invocations complete with `effect: "noop"`;
the invocation that appends `:compact` completes with
`effect: "mutated"`.

Conformance-relevant properties checked by this fixture:

- Strategy Observation events are emitted per hook invocation
- Completed events report the correct effect taxonomy
- Strategy Observation events are not appended to the durable Log
