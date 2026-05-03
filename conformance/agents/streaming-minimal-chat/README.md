# streaming-minimal-chat

Exercises the canonical streaming text path. The scripted stream emits
Observation-only transport events, then the consolidated
`:assistant_message`.

The expected Log proves the v0.8 persistence rule: streaming transport
events are not durable Log entries; the consolidated semantic assistant
message is.
