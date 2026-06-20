# 22. Provider Carriers

**Status note.** This section is staged for v0.20.1 and is bound by
`harnas_version: 0.20.1` and `fixtures_version: 0.20.1`.

Harnas has two layers for provider responses:

1. the **canonical semantic layer**, which is provider-neutral and drives
   normal Log, Projection, tool, compaction, and UI behavior; and
2. the **provider carrier layer**, which preserves provider-native
   response items or parts that cannot be represented losslessly in the
   canonical layer.

The canonical layer is mandatory. The carrier layer is additive. A
carrier never replaces canonical extraction, and a carrier cannot make an
otherwise-empty or malformed canonical Event valid.

## Motivation

Providers attach useful state to their native response objects. Examples
include Gemini part-level `thoughtSignature` values, provider-specific
reasoning item ids, or future provider fields required to replay a turn
faithfully. Some of those fields are opaque to Harnas: the substrate
must not interpret them, but dropping them can make a later provider call
invalid or less capable.

The carrier layer solves this without contaminating the canonical model.
The Log records text, tool calls, reasoning, usage, and attachments in the
normal Harnas vocabulary. It may additionally carry provider-native JSON
beside the canonical data, scoped to the provider destination that can use
it.

## Carrier Shape

A provider carrier is a JSON object with this shape:

```json
{
  "carrier_destination": "gemini.generateContent",
  "index": 0,
  "kind": "gemini.part",
  "wire": {
    "text": "Done.",
    "thoughtSignature": "opaque-provider-token"
  },
  "canonical_refs": ["payload.content[0]"]
}
```

Required fields:

- `carrier_destination` — the exact provider destination this carrier is
  valid for. The value is a stable string chosen by the implementation for
  a specific provider API surface. For example, `openai.chat_completions`
  and `openai.responses` are distinct destinations.
- `index` — the zero-based position of this carrier in its immediate
  carrier array. The stored value MUST equal the actual array position.
- `kind` — a provider-scoped description of the native item, such as
  `gemini.part` or `openai.response_item`.

Exactly one of these representation fields is required:

- `wire` — the provider-native JSON value as parsed data. This is the
  normal representation. It MUST be JSON-portable and canonical-byte-stable
  under §24 `harnas-jcs-v1`.
- `raw_text` — an escape hatch for a future provider surface whose native
  unit is not JSON. `raw_text` MUST NOT be used for JSON provider payloads.

Optional fields:

- `canonical_refs` — JSON-pointer-like strings naming the canonical
  payload fields represented by this carrier. These are informative aids
  for debugging and projection code; the canonical payload remains the
  source of semantic truth.
- `metadata` — JSON-portable implementation metadata about the carrier.
  `metadata` MUST NOT contain provider secrets.

## Carrier Locations

Carriers may appear in two places:

- `payload.provider_items` on an `assistant_message` Event, for provider
  native units that correspond to the assistant turn as a whole; and
- `provider_parts` on canonical content blocks, for provider native units
  bound to one content block.

Provider parts are intentionally nested on the canonical content block
they preserve. For example, a Gemini model part with `text` plus
`thoughtSignature` becomes a normal Harnas text content block whose
`provider_parts` array carries the exact Gemini part.

Implementations MAY add provider carriers to other Event payloads only
after a later spec section defines the location. In v0.20.1, only
assistant-message provider carriers are normative.

## Requirements

**C1. Mandatory canonical extraction.** An Ingestor MUST first extract the
canonical semantic Event from the provider response. If the provider
response contains assistant text, tool calls, tool results, reasoning,
usage, or other currently specified semantic fields and the implementation
cannot extract them, it MUST fail loudly. It MUST NOT store only a carrier
and claim the turn was ingested.

**C1a. Both layers are fixture-visible.** Carrier conformance fixtures
MUST assert both the canonical Event shape and the carrier shape. A
fixture that checks only provider-native bytes or only canonical content
does not prove this section.

**C2. Carrier order is stable.** Carrier arrays MUST preserve provider
order. `carrier.index` MUST equal the carrier's zero-based position in
its immediate carrier array. Loading a Log whose carrier array contains
an index/position mismatch MUST fail loudly.

**C3. Opaque means uninterpreted, not unvalidated.** Implementations MUST
preserve carrier `wire` values losslessly as JSON values. They MUST NOT
interpret opaque provider fields to create Harnas behavior unless another
spec section explicitly defines that mapping.

**C4. Canonical bytes.** A carrier `wire` value is stored as parsed JSON,
not as provider text. Its stable byte form is §24 `harnas-jcs-v1`
canonical JSON. Implementations MUST NOT store JSON provider payloads in
`raw_text` to avoid canonicalization.

**C5. Destination-scoped replay.** A Projection MAY use a carrier only
when projecting to the exact same `carrier_destination`. Destination
matching is exact string equality. A carrier captured for
`openai.chat_completions` MUST NOT be replayed into `openai.responses`;
a carrier captured for `gemini.generateContent` MUST NOT be replayed into
Anthropic, OpenAI, or Ollama.

When the destination does not match, the Projection MUST ignore the
carrier and project from the canonical semantic layer. If canonical data
is insufficient for the target provider, the normal capability-mismatch
or provider-projection error path applies.

**C5a. No fixture-aware carrier behavior.** Implementations MUST NOT
recognize fixture payloads, carrier byte strings, literal signatures, or
provider response fragments to make a carrier fixture pass. The C5 rule
in §23 applies to provider carrier code as well as conformance runners.

**C6. Compaction does not strip carriers in place.** A compaction strategy
MUST NOT mutate existing Events to remove carrier arrays. If a compaction
shadows Events that contain carriers, the compacting Event SHOULD include
`carrier_destinations`, an array of destination strings removed from the
active projection by that compaction. This marker is audit metadata only;
it does not preserve the removed carrier data. Reverting the compaction
restores the original Events and their carriers because the Log is
append-only.

**C7. Round-trip preservation.** For a matching `carrier_destination`,
the sequence provider-native response -> Log carrier -> provider request
MUST preserve the carrier's native JSON value losslessly. Conformance
fixtures for carriers MUST include an `expect_request` assertion that
proves the carrier is used on the next provider projection, and a
round-trip assertion that re-ingesting the same native response produces
the same carrier.

## Cross-Provider Fallback

Carriers are not a portability substitute. Portability comes from the
canonical semantic layer. When a Session written from one provider is
continued on another provider, projections use canonical content,
reasoning, tool, attachment, and usage fields. Provider carriers whose
destination does not match remain in the Log for audit and possible later
return to the original provider, but they do not affect the current
projection.

## Conformance

Carrier fixtures live under `conformance/provider-carriers/`. They are
not full agent scenarios. Each fixture defines:

- the provider destination under test;
- a provider-native response to ingest;
- the expected canonical Event payload including carrier arrays;
- an `expect_request` body proving projection uses a matching carrier;
- a round-trip assertion proving the carrier survives
  Log -> provider-native -> Log losslessly.

All provider-carrier fixture files are tracked by
`conformance/corpus-manifest.json`; changing the corpus without bumping
`fixtures_version` is drift.
