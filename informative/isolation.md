# Isolation

[informative]

Harnas's sandbox strategies are tool-boundary guards inside the agent
process. For real isolation, run the agent in a container or namespace.

Strategies such as `sandbox/write`, `sandbox/network`, and
`credential/proxy` operate where Harnas can see the call: before a
registered tool handler runs. They can block path-scoped writes, refuse
host-scoped HTTP calls, and inject credentials without persisting secret
values. These guards are useful and auditable, but they are application
logic inside the same process as the agent.

They do not provide OS-level isolation. A shell command run through
`bash_session` or `run_shell` is arbitrary process execution. It can
write anywhere the process can write, connect anywhere the process can
reach, read environment variables visible to the process, and spawn
child processes. Harnas does not observe or interpose on those system
calls.

Production deployments that need containment should use operating
system isolation around the Harnas process. Containers such as Docker or
Podman are the standard answer: mount only the workspace paths the agent
needs, restrict the network, drop unneeded capabilities, and run as an
unprivileged user. Network namespaces plus a proxy can enforce
host-level network policy for shell commands as well as Harnas HTTP
tools. Git worktrees per agent run provide a cheap filesystem boundary
for code-editing agents: the agent works in a disposable branch and the
caller reviews, merges, or discards the diff. User namespaces and
dropped capabilities can provide finer-grained controls when containers
are too heavy.

Harnas does not bundle a container runtime, configure namespaces, or
ship a network proxy. Those are deployment concerns. The substrate
defines the agent Log, tools, strategies, and projections; operators
choose the process boundary appropriate for their risk.
