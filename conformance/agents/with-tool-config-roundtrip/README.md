# with-tool-config-roundtrip

Exercises opaque manifest tool `config` preservation and handler
availability.

The fixture declares a tool with nested JSON config, runs one tool
turn, saves and reloads the Session, verifies the loaded Session's
manifest snapshot contains byte-identical tool config, then runs a
second tool turn. The conformance handler echoes the config it
received so the durable Log proves the handler saw the same value both
before and after the save/load boundary.

Conformance-relevant properties checked by this fixture:

- Manifest tool `config` accepts nested JSON objects, arrays, and
  primitives
- The runtime makes the opaque config available to the resolved handler
- Session JSONL preserves the manifest snapshot through save/load
- Continued execution after reload receives the same tool config
