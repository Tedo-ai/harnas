# streaming-minimal-chat

Exercises the canonical streaming text path. The scripted stream emits
every delta Event verbatim, then the consolidated `:assistant_message`.

The expected Log proves that streaming conformance is delta-visible:
implementations must preserve the exact delta sequence, not merely the
final assistant text.
