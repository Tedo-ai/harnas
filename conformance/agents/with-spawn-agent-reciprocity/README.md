# with-spawn-agent-reciprocity

Verifies the optional `harnas.builtin.spawn_agent` convenience tool creates
the reciprocal child Session metadata promised by the subagent spec.

After the parent calls `spawn_agent({ "task": "test" })`, the implementation
must have an in-memory child Session keyed by the returned
`child_session_id`. The child header must point back to the parent session,
carry the same `spawn_id`, include `spawned_by_event_id`, and contain an
initial `user_message` with the task content.

The expected parent Log keeps generated ids as wildcards in ordinary log
comparison. The conformance runner performs the structural reciprocity check
using the generated ids from the actual parent Log.
