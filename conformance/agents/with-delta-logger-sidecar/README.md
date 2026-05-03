# with-delta-logger-sidecar

Exercises the v0.8 streaming persistence split. The main Log contains only
the semantic user and consolidated assistant events, while an opt-in
Observation DeltaLogger sidecar records the streaming transport events.
