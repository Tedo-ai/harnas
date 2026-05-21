# with-subagent-orphan

Exercises an open child edge. The parent records `agent_spawn` but no
terminal `agent_result`, so `open_children` must report the spawn and
the delegation tree must not invent a terminal result.
