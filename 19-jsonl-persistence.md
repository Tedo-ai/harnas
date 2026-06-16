# 19. JSONL Persistence

This section defines the canonical Session JSONL persistence format.

**Status note.** J11 `content_hash` is staged for v0.20.0 and is bound
by `fixtures_version: 0.20.0`. It is present here for review and
reference-build work before the released `harnas_version` advances.

The format is intentionally small: one JSON object per line, UTF-8
encoded, newline-delimited, with a Session header followed by Event
rows in append order. It is the interchange format used by
cross-language round-trip conformance fixtures.

## Session Files

**J1.** A persisted Session file MUST be UTF-8 JSON Lines: one JSON
object per line, with `\n` line endings. Consumers MAY ignore blank
lines.

**J2.** The first non-blank line MUST be a Session header object:

```json
{"__session__":true,"id":"ses_...","metadata":{}}
```

The header fields are:

- `__session__`: the literal boolean `true`.
- `id`: the Session id as a string.
- `metadata`: an object. Empty metadata MUST be represented as `{}`.

Delegation-aware sessions MAY also include:

- `parent_session_id`: the immediate parent Session id, or `null`.
- `root_session_id`: the root Session id for this delegation tree, or
  `null` for a root Session.
- `spawn_id`: the parent `agent_spawn` id that created or attached
  this Session, or `null`.
- `spawned_by_event_id`: the parent Event id that caused the spawn, or
  `null`.
- `delegation_chain`: an array of ancestor links of the form
  `{ "session_id": "...", "spawn_id": "..." }`. The root link's
  `spawn_id` is `null`.

Root sessions MAY omit these fields or set them to `null` / `[]`.
Child sessions SHOULD populate all five fields. `parent_session_id` plus
`spawn_id` is the canonical immediate edge.

**J3.** Every following non-blank line MUST be an Event row object:

```json
{"seq":0,"id":"evt_...","timestamp":"2026-05-24T10:15:30.123Z","type":"user_message","payload":{"text":"hello"}}
```

The Event row fields are:

- `seq`: the Event sequence number.
- `id`: the Event id as a string.
- `timestamp`: the UTC time at which the Event was appended,
  serialized as ISO 8601 / RFC 3339 using UTC and a trailing `Z`.
- `type`: the Event type without a leading colon.
- `payload`: the Event payload object.
- `content_hash`: optional in v0.20.0 and later. When present, it is
  the lowercase hexadecimal SHA-256 digest of the
  `harnas-jcs-v1` canonical JSON bytes for the Event row.

**J4.** Event rows MUST appear in append order. Their `seq` values MUST
be dense and monotonic starting at `0`.

**J5.** Consumers MUST preserve the Session id, metadata, Event seq,
Event id, Event timestamp, Event type, Event payload, and append order
when loading and re-saving a Session.

**J6.** Producers SHOULD emit compact JSON with no insignificant
whitespace. Consumers MUST NOT rely on object key ordering or
whitespace. The semantic JSON values are authoritative.

**J7.** Producers MUST emit unicode as valid UTF-8. They MAY either
emit non-ASCII characters directly or as JSON escapes; consumers MUST
accept both forms.

**J8.** Producers targeting v0.8.0 or later MUST NOT persist streaming
transport Events (`assistant_turn_started`, `assistant_text_delta`,
`tool_use_begin`, `tool_use_argument_delta`, `tool_use_end`,
`assistant_turn_completed`, or `assistant_turn_failed`) in new Session
JSONL files. These Events are Observation-only (§13, §15).

**J9.** Consumers MUST tolerate legacy pre-v0.8 Session JSONL files
that contain streaming transport Events. Loaders MAY preserve those
rows as historical noise, but projections, mutation strategies, and
new saves MUST NOT require them for correct behavior.

**J10.** Consumers MUST tolerate legacy Event rows without
`timestamp`. When re-saving a legacy row, consumers MAY preserve the
missing timestamp or backfill one, but MUST NOT change `seq`, `id`,
`type`, `payload`, or append order. A backfilled timestamp is a
compatibility value, not the original append time, and loaders /
projections MUST NOT treat it as historical truth. New Event rows
produced by v0.19.0 or later implementations MUST include
`timestamp`.

**J11.** When an Event row carries `content_hash`, the hash input is
the §19 Event row object serialized with the `harnas-jcs-v1`
canonicalization profile (§24), excluding only the `content_hash` field
itself. This avoids self-reference. All other row fields present in the
row, including `seq`, `id`, `timestamp`, `type`, and `payload`, are part
of the hash input.

`content_hash` is a row-integrity value, not an Event id. It MUST NOT be
used to assign `seq`, infer ordering, or replace `id`. Consumers that
verify hashes MUST fail loudly on mismatch or mark the row corrupt; they
MUST NOT silently ignore a mismatching hash and continue as though the
row were valid.

The conformance oracle
`conformance/oracle-corpus/event-content-hash/` pins a known Event row
to its expected `content_hash` and also verifies that a persisted
`content_hash` field is excluded from its own input.

## Relationship To Log Conformance

Agent-level conformance fixtures compare Logs using `{seq, type,
payload}` because Event ids are implementation-minted. Session JSONL
persistence is stricter: `id` is part of the persisted wire contract and
MUST round-trip when present.

Round-trip conformance fixtures therefore test two things:

1. Session JSONL can be saved by one implementation and loaded by
   another.
2. The loaded Session remains behaviorally equivalent: after continued
   input, its provider request projection and final Log match the
   fixture's canonical expectations.

## Recommended Metadata Envelope

[informative]

Session metadata is implementer-defined and may carry any
JSON-serializable values. To improve cross-adopter portability of saved
Sessions, the following field names are recommended, not normative,
when the corresponding concept is being recorded:

- `metadata.trace.trace_id` — a unique identifier for the distributed
  trace this Session belongs to, for example an OpenTelemetry trace id.
- `metadata.trace.parent_span_id` — the parent span if the Session was
  triggered by another operation.
- `metadata.trace.request_id` — a unique identifier for the inbound
  request that initiated the Session.
- `metadata.actor.id` — the user or service identity on whose behalf
  the agent is acting.
- `metadata.actor.kind` — the actor type, for example `"user"`,
  `"api_key"`, or `"service"`.
- `metadata.workspace_id` — the multi-tenant workspace the Session
  belongs to, where applicable.
- `metadata.conversation_id` — a stable identifier for the
  conversation, distinct from the Session id.

Adopters remain free to use other names, omit fields, or add new ones.
The recommendation exists so tooling reading saved Sessions across
adopters has a consistent place to look.
