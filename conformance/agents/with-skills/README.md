# with-skills

Exercises the Layer 2 skills convention:

- the manifest system prompt contains the canonical `BuildSkillsIndex`
  output;
- `load_skill` is registered as `harnas.builtin.load_skill` with a
  fixture-local `skills_dir`;
- the second provider request sees the frontmatter-stripped skill body
  in the `role: "tool"` message; and
- both turns use `expect_request` so projection drift is caught.

