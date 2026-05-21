# with-subagent-success-basic

Exercises the minimal successful delegation shape: a parent records an
`agent_spawn`, the child session reciprocates the header link, and the
parent receives exactly one successful `agent_result`.

The projection assertions verify the delegation tree, that no children
remain open, and aggregate usage across the parent and child sessions.
