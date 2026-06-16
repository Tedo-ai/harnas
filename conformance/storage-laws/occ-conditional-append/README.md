# occ-conditional-append

Storage Adapter law fixture for §21 S9.

The runner creates a fresh adapter instance, then executes
`law.json` in order:

1. append a first EventDraft with `expected_next_seq: 0`; it must
   succeed and assign `seq: 0`;
2. try to append a second EventDraft with stale `expected_next_seq: 0`;
   it must reject with reason `storage_conflict`, report
   `current_next_seq: 1`, and write no Event;
3. append that same second EventDraft with `expected_next_seq: 1`; it
   must succeed and assign `seq: 1`;
4. read the stream back and verify only the two successful rows exist,
   in order.

This fixture is intentionally adapter-level rather than agent-level. It
must run against every adapter an implementation exposes: memory, file,
and future database adapters.
