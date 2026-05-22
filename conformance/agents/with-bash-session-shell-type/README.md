# with-bash-session-shell-type

Verifies that the `bash_session` tool descriptor carries an effective
`shell_type` in its config. Unix conformance runners resolve the default
`shell_type: "auto"` value to `posix`; Windows is compile-only for now.
