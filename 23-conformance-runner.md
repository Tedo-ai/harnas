# 23. Conformance Runner

This section defines the contract for Harnas conformance runners. The
fixtures are the measure, not the target: a runner exists to execute the
implementation under test and compare the resulting artifacts to the
specification corpus without fixture-specific accommodation.

## Scope

A conformance runner consumes the normative fixture corpus under
`conformance/` and reports whether an implementation reproduces the
expected artifacts. Artifacts include, when present:

- agent Logs (`expected-log.jsonl`)
- provider request expectations (`expect_request`)
- streaming delta sidecars (`expected-deltas.jsonl`)
- strategy event sidecars (`expected-strategy-events.jsonl`)
- tool descriptor snapshots (`expected-tool-descriptors.json`)
- child-session assertions (`expected-spawn-children.json`)
- cross-session projections (`expected-projections.jsonl`)
- round-trip Session JSONL outputs

## Runner Laws

**C1. No fixture-specific branching.** A runner MUST NOT branch on a
fixture name, fixture path, literal user input, literal tool command,
literal provider payload, or other fixture-specific content to make a
fixture pass. Runners MAY branch on declared fixture capabilities or
metadata that are part of the fixture format, such as `platform`, the
presence of a sidecar artifact, or the manifest's provider kind.

**C2. Execute implementation behavior.** A runner MUST exercise the
implementation's public or internal implementation path for the behavior
under test. It MUST NOT synthesize expected Log rows, provider requests,
projection rows, tool outputs, or strategy events in the runner when the
implementation has not produced them.

Conformance helpers are permitted only when the fixture explicitly
declares a helper surface, such as a scripted provider, a conformance
tool stub, or an in-memory attachment store. The helper MUST be generic
for that fixture class and MUST NOT encode the expected answer for one
fixture by name.

**C3. Strict artifact diffing.** A runner MUST compare the full actual
artifact to the expected artifact after canonical normalization. It MUST
NOT filter actual objects down to the keys present in the expected
object. Extra actual keys, missing actual keys, extra array items,
missing array items, and differing scalar values are mismatches unless
the fixture format explicitly defines a wildcard.

This rule applies recursively to payloads, `usage` objects, provider
requests, sidecar rows, tool descriptors, projection outputs, and
round-trip JSONL rows.

**C4. Canonical normalization.** Canonical normalization for runner
diffs is the `harnas-jcs-v1` profile. This section does not redefine
that profile. Runners MUST use the same canonicalization profile for
actual and expected artifacts before comparison.

Runner-specific normalization is limited to fields explicitly marked by
the fixture format as generated. For example, an expected value of
`"<generated>"` matches any non-empty generated value at that exact
position. A generated wildcard does not relax sibling keys, parent
object keys, array length, or unrelated values.

**C5. Generated fields.** Fixture authors SHOULD prefer explicit
generated sentinels over omission when a field is required by the spec
but implementation-minted, such as event ids or timestamps. When legacy
fixtures omit a generated top-level field, runners MAY ignore that field
for that fixture until the fixture is refreshed. Runners MUST NOT extend
this tolerance to payload fields or nested data.

**C6. Honest reporting.** A runner report MUST distinguish executed
implementation behavior from simulation. If a runner uses simulation for
any fixture family, the report MUST label that claim with the word
`SIMULATION` in the same sentence as the count.

Published conformance claims SHOULD include:

- the spec version and fixtures version
- the exact fixture count passed and failed
- whether provider calls were live, scripted, or simulated
- whether round-trip and packed-artifact checks were run
- the command that produced the claim

**C7. Red is valid signal.** A strict runner that turns a previously
green suite red is behaving correctly when the failures expose fixture
or implementation gaps. Implementations MUST NOT reintroduce filtering,
fixture-name branches, or runner-side synthesis to restore a green
count.

## Oracle Corpus

`conformance/oracle-corpus/` contains fixtures for testing conformance
runners themselves. These entries are not agent scenarios. They are
small actual/expected artifact pairs that prove a runner rejects known
invalid matches.

The oracle entry `strict-diff-extra-payload-field` contains an actual
Log row with an extra payload field that is absent from the expected Log
row. A conformant strict differ MUST report a mismatch for this oracle.
A runner that accepts this oracle is non-conformant because it is
filtering actual payload keys down to the expected payload shape.

Implementations SHOULD include fast unit tests that load every oracle
entry and assert the documented outcome. These tests are part of the
measurement system; they are not substitutes for the agent fixture suite.
