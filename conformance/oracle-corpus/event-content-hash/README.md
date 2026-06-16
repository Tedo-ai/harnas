# event-content-hash

Oracle corpus entry for `harnas-jcs-v1` and §19 Event row
`content_hash`.

The primary fixture is `vectors.json`. Each entry in `valid` has:

- `input_json` — source JSON to parse;
- `scope` — `rfc8785` for generic RFC 8785 vectors or
  `harnas_event_content_hash` for §19 Event-row/content-hash vectors;
- optional `exclude_keys` — top-level keys removed from the hash input
  after parse, used to model §19 `content_hash` self-exclusion;
- `expected_canonical` — exact RFC 8785 / `harnas-jcs-v1` canonical
  bytes represented as a JSON string;
- `expected_content_hash` — lowercase SHA-256 hex over those UTF-8
  canonical bytes.

Each entry in `invalid` has `input_json`, `scope`, and
`expected_error`. A conformant implementation MUST reject those inputs
for that scope before producing canonical bytes.

The vectors cover the cross-language divergence points:

- RFC 8785 primitive and number serialization;
- UTF-16 object key ordering, including the RFC 8785 sorting example;
- recursive key sorting;
- `-0`, exponent notation, and decimal input forms;
- arbitrary-precision integer preservation, including a 64-bit
  snowflake-style value;
- true fractional number serialization under RFC 8785 / ES6 rules;
- no Unicode normalization;
- distinct hashes for precomposed and decomposed Unicode strings;
- non-BMP key ordering;
- invalid Unicode;
- Event row `content_hash` self-exclusion.

The standalone `event-row*.json` files and `expected-content-hash.txt`
repeat the event-row subset in a smaller shape for implementations that
want a minimal smoke test before running the full vector corpus.
