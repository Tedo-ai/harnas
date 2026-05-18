# with-repetition-guard-rejections

Verifies `guard/repetition` detects approval-denial loops. The fixture
combines `Permission::DenyByName` with `guard/repetition` configured with
`max_consecutive_rejections: 3`.

The provider proposes the same denied tool call three times. On the third
denial, `guard/repetition` appends a terminal `:runtime_error` with
`trigger: "consecutive_rejections"` and the AgentLoop stops before any fourth
provider turn.

