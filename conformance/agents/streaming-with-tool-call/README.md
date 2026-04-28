# streaming-with-tool-call

Exercises a streaming tool-call round trip. The first streamed turn
emits tool-use delta Events and consolidated `:tool_use`; the runner
dispatches the conformance stub tool; the second streamed turn emits
the final assistant text.

The fixture records every delta Event in append order, plus the
consolidated Events that complete each stream.
