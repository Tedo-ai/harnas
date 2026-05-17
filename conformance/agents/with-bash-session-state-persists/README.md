# with-bash-session-state-persists

Exercises the core `bash_session` invariant: shell state survives across
calls to the same `session_id`.

The first command exports `MYVAR` and changes directory to `/tmp`. The
second command, sent as a separate tool call with the same session id,
must see both the environment variable and the working directory.
