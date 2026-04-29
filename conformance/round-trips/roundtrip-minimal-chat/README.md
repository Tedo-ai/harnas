# roundtrip-minimal-chat

Runs one turn, persists the Session as JSONL, loads it in a second
implementation, and continues for one more turn.

This fixture verifies that Session persistence is a cross-language wire
contract, not just an implementation-local convenience.

The phase-2 provider script asserts the provider request after load, so
the fixture also verifies behavioral compatibility of projection after
cross-language persistence.
