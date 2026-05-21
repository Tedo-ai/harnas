# with-subagent-failure

Exercises a child session that fails independently. The child keeps its
own `runtime_error` in its Log; the parent records a summarized failed
`agent_result` and can continue with a normal assistant message.
