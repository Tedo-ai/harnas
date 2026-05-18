# Worktree-Per-Agent Convention

Status: informative. Harnas does not require a source-control workflow, but
coding agents are easier to supervise when each run works in its own branch and
worktree. A host application can create a worktree per Session, let the agent
modify files there, and keep the user's main checkout untouched until review.

Example sequence:

```sh
git worktree add .agent-runs/ses_123 -b agent/ses_123
cd .agent-runs/ses_123
# run the Harnas agent here
git diff
git checkout main
git merge agent/ses_123   # or discard the worktree/branch
```

On success, the operator reviews and merges the branch. On failure, the host can
remove the worktree and delete the branch without cleaning up partial edits in
the main checkout.

