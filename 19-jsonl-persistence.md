# 19. JSONL Persistence

This section defines the canonical Session JSONL persistence format.

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

**J3.** Every following non-blank line MUST be an Event row object:

```json
{"seq":0,"id":"evt_...","type":"user_message","payload":{"text":"hello"}}
```

The Event row fields are:

- `seq`: the Event sequence number.
- `id`: the Event id as a string.
- `type`: the Event type without a leading colon.
- `payload`: the Event payload object.

**J4.** Event rows MUST appear in append order. Their `seq` values MUST
be dense and monotonic starting at `0`.

**J5.** Consumers MUST preserve the Session id, metadata, Event seq,
Event id, Event type, Event payload, and append order when loading and
re-saving a Session.

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
