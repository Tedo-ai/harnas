# with-session-isolation-repeat-gemini

Runs the same Gemini text-plus-tool fixture twice in one implementation process.

The lock is not a new provider shape; it is process isolation. The second run
must produce the same conformance Log as the first run. Implementations must not
let per-session counters, cached provider state, tool ids, or other mutable
runtime state leak from one Session into the next.
