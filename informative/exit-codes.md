# Exit code taxonomy

This note records the recommended exit-code convention for Harnas CLIs.
It is informative rather than normative: implementations may expose
additional commands with command-specific status codes, but `harnas run`
and `harnas chat` should use the table below so shell integrations can
distinguish invocation problems from agent failures.

| Code | Meaning |
| ---: | --- |
| 0 | Agent completed successfully. |
| 1 | Agent error: task failed, provider error, timeout, anti-loop guard, or budget exceeded. |
| 2 | Invocation error: bad manifest, missing file, invalid flag, or malformed arguments. |
| 3 | Approval gate rejected by a human. Reserved for `informative/approval-gates.md`. |
| 4 | Sandbox violation: blocked write path. |

## Notes

- Manifest parse failures, missing manifest files, invalid flags, and
  other errors before an agent run starts should exit 2.
- Provider failures after retries are exhausted should exit 1.
- Guard-initiated agent stops such as timeouts, repetition guards, and
  cost-budget guards should exit 1.
- Tool-boundary sandbox write denials that terminate the run should
  exit 4.
- Human approval rejection is reserved as exit 3. Implementations that
  do not expose an approval-gate CLI path should leave it unused.
