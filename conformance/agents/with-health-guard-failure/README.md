# with-health-guard-failure

Verifies `guard/health` refuses the next provider turn when a configured
health-check command fails after tool execution.

The first provider turn requests a deterministic conformance tool. After the
tool result is appended, the health guard runs before the next provider call,
executes `exit 1`, appends a terminal `:runtime_error`, and prevents a second
provider request.

