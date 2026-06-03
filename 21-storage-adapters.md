# 21. Storage Adapters

This section makes Session persistence pluggable: a Harnas Session can
be backed by the filesystem, a database, or any store, without
changing agent code. It builds on §19, which defines canonical JSONL
persistence, and §20, which permits equivalent event-row storage that
can be emitted as canonical Session JSONL.

The filesystem is one adapter; a database is another. The agent loop,
projections, and conformance do not change when the adapter changes.

## Status

The adapter laws and interface contract in this section are normative.
Recommended built-in adapters, packaging shape, contrib database
adapters, and examples are informative.

The storage laws are normative for persisted Session behavior and for
any adapter interface an implementation exposes. A reference
implementation may satisfy them with only its built-in file-backed
persistence. Exposing a host-supplied adapter seam, such as
`Session.open({storage})`, a `storage` subpath, or a database adapter,
is recommended for embeddability but not required for the public
conformance claim until the implementation chooses to expose one. The
file-backed default path is still storage and obeys the same append,
header, timestamp, and export laws.

## Event Construction

The Session/runtime owns event identity and event time. The adapter
owns durable ordering and persistence.

```text
EventDraft = { id, timestamp, type, payload }
EventRow   = { seq, id, timestamp, type, payload }
```

The Session mints `id`, `timestamp`, `type`, and `payload` as an
EventDraft. The draft has no `seq`; only the adapter can assign dense
durable order. The adapter appends the draft, assigns `seq`, persists,
and returns the full §19 EventRow.

Event ids are opaque. The storage law MUST NOT couple id format to
`seq`.

## Responsibilities

A Storage Adapter persists and reads back the Session header and Event
rows of §19. It is pure persistence: it does not interpret payloads,
compute projections, mutate Events, apply strategies, or make policy.

The append-only model (§5, §19) means an adapter never updates or
deletes an Event. Compaction is itself an appended `compact` Event. The
only mutable state an adapter persists is the Session header metadata.

## Interface

Names are illustrative; each language SHOULD adopt its own idiom.

```text
StorageAdapter:

  load_session() -> SessionHeader | nil
      The §19 header, or nil for a fresh Session.

  save_header(header) -> void
      Persist the header. MUST exist; see Header Persistence.

  append_event(draft: EventDraft) -> EventRow
      Append the draft, assign seq, persist, and return the full §19
      EventRow.

  events_since(cursor) -> [EventRow]
      Return full §19 EventRows strictly after cursor, in append order.
      The cursor is the last-seen seq; events_since(nil) returns all.
```

## Adapter Laws

**S1 — Header round-trip.** `save_header` followed by `load_session`
preserves all §19 header fields, including metadata and delegation
fields.

**S2 — Dense append order.** The adapter assigns `seq` values `0..n`
with no gaps and no reordering.

**S3 — Envelope preservation.** The draft's `id`, `timestamp`, `type`,
and `payload` round-trip unchanged after persistence. The adapter only
adds `seq`.

**S4 — Cursor semantics.** `events_since(nil)` returns all Events.
`events_since(k)` returns Events with `seq > k` in append order. Past
the last seq, it returns `[]`. The cursor is `seq`.

**S5 — Append-only.** Existing Events are never updated or deleted.
Compaction is represented only by appended `compact` Events.

**S6 — Canonical export.** A persisted Session can be emitted as
canonical §19 JSONL accepted by the existing round-trip fixtures.

**S7 — Acknowledged-append durability.** Once `append_event` returns
success, the Event is visible exactly once in later `events_since`,
load, or export, with stable `seq`, `id`, `timestamp`, `type`, and
`payload`.

**S8 — No silent corruption on load.** Loading a Log MUST NOT return a
torn, malformed, duplicate-seq, gapped, reordered, or invented Event.
If a defect is detected, including a torn final line from a crash
mid-append, the loader MUST either recover the valid prefix or fail
loudly with a storage error. It MUST NOT return partial or garbage data
as valid Events. Mechanisms such as fsync, atomic rename, WAL, record
framing, and database transactions are implementation choices, not
normative.

**S9 — Session scoping.** An adapter implementation used for multiple
Sessions in one process MUST keep each Session's Events isolated. Two
Sessions sharing one adapter implementation, with interleaved appends,
MUST each export only their own rows.

## Header Persistence

Every adapter MUST expose `save_header`. It MAY be a no-op only if the
implementation never mutates the header after creation. If a metadata
mutation is requested and the adapter cannot persist it, it MUST raise
a storage error rather than silently dropping the mutation.

## Non-goals

Harnas does not guarantee that an acknowledged append physically
survives a sudden power loss or OS/filesystem buffering. That is the
host filesystem's or database's responsibility (§20). S8 guarantees no
silent corruption on load; it does not promise fsync-level durability.
Stronger durability is an opt-in adapter capability added when a
consumer needs it.

Exactly-once retry on unknown outcome is also not guaranteed. With no
caller-supplied event id or idempotency key, a blind retry after a
crash-between-commit-and-ack may append a duplicate semantic Event with
a new id. Callers recovering from an uncertain append result should
read the Log before retrying. An optional idempotency-key extension MAY
be added when a consumer needs it.

## Conformance — The Law Helper

An adapter is conformant iff it satisfies S1-S9. The law helper tests
more than byte-identical export. Against the adapter directly, it
checks:

- a fresh store returns no header and an empty stream;
- header round-trips with metadata and delegation fields;
- append after reload continues `seq` without gaps;
- `events_since` boundaries: nil, `0`, a middle seq, and the last seq;
- timestamp preservation by creating a draft with a known `timestamp`,
  persisting it, reloading, and asserting the exact value survives;
- `id` stays stable across save/load;
- fork/read paths do not mutate the source Session;
- a truncated final line, injected garbage, duplicate seq, gap, or
  reorder yields the clean prefix or a loud storage error, never a
  partial row returned as valid;
- two Sessions on one adapter implementation stay isolated.

The agent-fixture `"<generated>"` timestamp wildcard asserts that a
timestamp exists. It does not prove timestamp preservation. Preservation
is tested by the law helper with known draft timestamps and by static
fixtures with concrete timestamps.

## Informative: Recommended Adapters And Packaging

- **File-backed (default).** Persists canonical §19 JSONL to a path.
  Every reference implementation SHOULD ship this; out-of-the-box
  behavior is unchanged.
- **In-memory.** Useful for tests and the law helper.
- **Database-backed (contrib).** Ships as a contrib package, not core,
  consistent with ADR 0005.
- **Packaging.** Implementations SHOULD expose the interface and
  built-ins so a host app can supply its own backend without a
  filesystem. A `storage` subpath or module is recommended. A Session
  SHOULD offer both file-backed convenience and explicit adapter forms,
  for example `Session.open({path})` and `Session.open({storage})`.

## What This Does Not Add

This section does not add a database schema, web transport, query
language, or migration system. Those remain application concerns (§20).
The Storage Adapter is the minimal seam that lets the Log live wherever
the host already keeps its data, while remaining emittable as canonical
§19 JSONL.
