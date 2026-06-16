# 24. harnas-jcs-v1 Canonical JSON

**Status note.** This section is staged for v0.20.0 and is bound by
`fixtures_version: 0.20.0`. It is present here for review and
reference-build work before the released `harnas_version` advances.

`harnas-jcs-v1` is the canonical JSON profile used by Harnas whenever
two independently-written implementations must produce identical bytes
for the same JSON value. It is used by conformance-runner normalization
(§23), Event row `content_hash` (§19), and any future hash or signature
that says it is computed over canonical Harnas JSON.

This section is the single normative definition of the profile. Other
sections MUST reference it rather than defining their own
canonicalization rules.

## Base Standard

`harnas-jcs-v1` is RFC 8785 JSON Canonicalization Scheme (JCS), with
one Harnas-specific integer preservation rule defined below.
Implementations MUST follow RFC 8785 for:

- parsing and constraining inputs to I-JSON;
- serialization of literals, strings, and non-integer numbers;
- recursive object property sorting;
- object key comparison by UTF-16 code units;
- UTF-8 output bytes.

RFC 8785 is intentionally reused rather than re-specified here. If a
future Harnas release needs different canonicalization semantics, it
MUST define a new profile name.

## Rationale

Canonicalization is for deterministic byte-form, not semantic
equivalence. It attests what Harnas recorded; it does not reinterpret
payload meaning. Harnas therefore deviates from RFC 8785 only to
preserve recorded data, never to transform it.

Application-level semantic equivalence, such as deciding that two
Unicode spellings or two domain-specific numeric encodings mean the same
thing, happens before an Event is created. Once an Event row exists, the
canonical hash path preserves the row's data model.

## Harnas Constraints And Deviations

Harnas makes the following constraints explicit:

1. **Arbitrary-precision integer preservation.** RFC 8785 relies on
   ECMAScript number serialization, which cannot preserve integers
   outside IEEE-754's exact range. Harnas Event rows and Event payloads
   MAY contain integer JSON number tokens of arbitrary precision. Such
   integer tokens MUST be parsed without loss and serialized in canonical
   decimal integer form: optional leading `-`, followed by `0` or a
   non-zero digit and digits, with no leading zeroes, decimal point, or
   exponent. This preserves ids, snowflakes, counters, and other recorded
   integer data that would otherwise be rounded by `float64` or native
   JavaScript `number` parsing.
2. **Non-integer number serialization.** JSON numbers with a decimal
   point or exponent are canonicalized exactly as RFC 8785 specifies:
   ECMAScript `Number::toString` / `JSON.stringify` semantics, including
   `-0` serializing as `0`. Non-finite values such as `NaN` and
   infinities are invalid JSON and invalid Harnas canonical inputs.
3. **Unicode normalization.** Harnas does not apply Unicode
   normalization. String values and property names are preserved exactly
   as parsed, matching RFC 8785. In particular, NFC and NFD forms that
   look visually similar remain distinct byte inputs. The hash attests
   the actual stored value, and §19 requires payloads to round-trip
   exactly. Normalizing in the hash path would contradict that
   requirement and would also tie the hash to an implementation's
   Unicode database version.
4. **Invalid Unicode.** Lone surrogates or otherwise invalid Unicode
   string data MUST cause canonicalization to fail loudly.
5. **Absent host-language values.** Values that are not JSON values,
   such as JavaScript `undefined`, are outside the profile. They MUST be
   rejected before canonicalization or omitted only when the surrounding
   Harnas data model explicitly defines them as absent fields. JSON
   `null` is a real value and is preserved.

The arbitrary-precision integer rule is the only v1 deviation from RFC
8785. The Unicode rule is not a deviation; it restates RFC 8785's
preservation behavior because normalization has caused cross-language
drift in practice.

## Hashing

When a spec section says to compute SHA-256 over `harnas-jcs-v1`, it
means:

1. parse or construct the JSON value;
2. validate that it is in the Harnas input domain above;
3. canonicalize it according to RFC 8785;
4. hash the resulting UTF-8 bytes with SHA-256;
5. render the digest as lowercase hexadecimal.

No trailing newline is included in the hash input unless the JSON value
itself contains a newline inside a string.

## Oracle Vectors

`conformance/oracle-corpus/event-content-hash/vectors.json` pins the
cross-language divergence cases that implementations MUST agree on. The
valid vectors include generic RFC 8785 canonicalization cases. The
invalid vectors apply the additional Harnas Event-row/content-hash input
constraints above.

The vector corpus covers:

- RFC 8785 primitive serialization and number forms;
- RFC 8785 UTF-16 property ordering, including non-BMP keys;
- arbitrary-precision integer preservation, including a 64-bit
  snowflake-style value;
- true fractional number serialization under RFC 8785 / ES6 rules;
- recursive property sorting;
- no Unicode normalization;
- distinct hashes for precomposed and decomposed Unicode strings;
- rejection of invalid Unicode;
- Event row `content_hash` self-exclusion.
