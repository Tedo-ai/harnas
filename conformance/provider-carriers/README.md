# Provider Carrier Fixtures

Provider carrier fixtures exercise §22. They are not full agent
scenarios; they are small ingestor/projection/round-trip contracts for
provider-native carrier data.

Each fixture directory contains `fixture.json` with:

- `provider` — the provider kind, model, and exact
  `carrier_destination`;
- `ingest.provider_response` — provider-native JSON returned by the
  provider;
- `ingest.expect_event` — the canonical Harnas Event payload the
  Ingestor must produce, including any `provider_items` or
  `provider_parts`;
- `project.log` — a minimal Log used for the follow-up projection;
- `project.expect_request` — the exact provider request body. This is
  the carrier equivalent of agent fixture `expect_request`;
- `round_trip` — a second ingest assertion proving the carrier survives
  provider-native response -> Log -> provider-native request -> Log.

Runners MUST compare these artifacts with the same strict differ used for
agent fixtures. Extra actual keys, missing carrier fields, carrier order
changes, and destination mismatches are failures.
