# with-event-id-preservation-roundtrip

Verifies that event identities survive Session save/load.

The fixture drives one turn, saves and reloads the Session through the
implementation's Session JSONL persistence, then drives a second turn. The
conformance runner must compare the pre-save event ids with the loaded event
ids and fail if any identity was regenerated.

This locks the v0.18.1 invariant that `event_id` is the canonical
cross-session reference and is not re-minted on load.
