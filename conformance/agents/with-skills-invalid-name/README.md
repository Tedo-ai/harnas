# with-skills-invalid-name

Exercises the negative path for the `load_skill` built-in. The provider
requests `load_skill(name="foo-bar")`; conformant implementations reject
the name because it does not match `^[a-z][a-z0-9_]*$` and record the
failure as an ordinary `:tool_result` error.

