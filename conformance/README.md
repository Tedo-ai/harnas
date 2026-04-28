# Conformance Fixtures

Two layers of conformance:

- **`fixtures/`** — single provider round-trips (one request + one
  response per provider). Records what each provider's wire format
  looks like for a fixed set of canonical cases.
- **`agents/`** — full agent-level fixtures. A manifest + a scripted
  sequence of provider responses + user inputs + the exact Log any
  conformant implementation must produce. This is where the spec's
  language-neutrality claim gets tested.

Both are **normative**. Any Harnas implementation in any language
SHOULD pass every agent fixture and SHOULD be able to load every
single-call fixture into its mock provider.

## `agents/` — agent-level conformance

Each directory under `agents/` is one fixture:

    agents/
    └── <case-name>/
        ├── README.md              # what the case exercises
        ├── manifest.json          # standard spec/18 Agent Manifest
        ├── provider-script.json   # ordered buffered provider responses
        ├── provider-script-stream.json
        │                           # ordered streaming provider events
        ├── inputs.json            # ordered user message strings or actions
        └── expected-log.jsonl     # the Log any conformant impl must produce

Buffered fixtures use `provider-script.json`: an ordered list of
provider responses, one per `Provider.call`. A buffered script entry
may instead be an error object of the form
`{"error":{"status":503,"body":"Service Unavailable"}}`; the
ScriptedProvider MUST raise the implementation's canonical HTTP
provider error for that status/body instead of returning a response.
Buffered script entries may also wrap a response with an expected
request assertion:
`{"expect_request":{...},"response":{...}}`. The ScriptedProvider
MUST compare the projected request to `expect_request` after canonical
normalization and fail the fixture if it differs, then return
`response`.
Streaming fixtures use
`provider-script-stream.json`: an ordered list of streams, one per
streaming provider call; each stream is an ordered list of Event-args
objects `{type, payload}` yielded verbatim to the AgentLoop stream
callback.

The fixture format is language-neutral: no Ruby-specific state, no
host-dependent timing, no randomness. Every event in
`inputs.json` entries are usually strings, each appended as a
`:user_message` before running the AgentLoop. Fixtures may also use
explicit action objects when they need to exercise Log operations
directly:

- `{"compact":{"replaces":[0,1],"summary":"..."}}` appends a
  `:compact` Mutation Event without a provider call.
- `{"revert":2}` appends a `:revert` Mutation Event revoking the
  mutation at seq 2, without a provider call.
- `{"fork":{"at_seq":1}}` replaces the active Session with
  `Session#fork(at_seq: 1)`, verifies the forked prefix and
  `forked_from` / `forked_at_seq` metadata, and continues subsequent
  inputs on the fork.

`expected-log.jsonl` carries `seq`, `type`, and `payload` fields
with canonical values per the spec.

### Running the reference implementation's conformance suite

    just conformance

Replays every fixture under `agents/` against Ruby's Harnas,
compares the resulting Log to `expected-log.jsonl`, and reports
pass/fail per fixture. A named subset can be run by passing
fixture names: `just conformance minimal-chat with-tool-call`.

Agent fixtures are also run as part of `just test` (via
`reference/spec/harnas/conformance/runner_spec.rb`) so any
regression in projection/ingestor/agent-loop behavior is caught
on normal CI.

### For cross-language implementors

To verify a `harnas-py` / `harnas-go` / `harnas-ts` port is
conformant on the agent layer:

1. Implement a ScriptedProvider in your language: for buffered fixtures,
   consume `provider-script.json` and return the next response on each
   `#call(request)` invocation; for streaming fixtures, consume
   `provider-script-stream.json` and yield the next stream's Event-args
   objects one by one to the AgentLoop stream callback.
2. Implement a manifest loader for spec v0.1.
3. For each fixture directory:
    - Load the manifest
    - Install its strategies
    - Replace the resolved provider with your ScriptedProvider
    - Append each `inputs.json` entry as a `:user_message` and
      run the agent loop
    - Serialize the resulting Log to `{seq, type, payload}` per
      event
    - Diff against `expected-log.jsonl`
4. All fixtures MUST match byte-for-byte after canonical
   normalization (string keys, sorted hashes).

A port that passes every fixture under `agents/` is, by the spec's
definition, conformant on those cases. Add new fixtures as the
catalog grows; every new canonical strategy should come with at
least one fixture that exercises it.

### The conformance stub tool handler — normative format

[normative]

For every tool in a fixture's manifest, the conformance runner MUST
register a stub handler that returns a deterministic, language-neutral
string of the form:

    [conformance stub: <handler_name>(<args>)]

Where:

- `<handler_name>` is the manifest's symbolic handler reference for
  this tool (e.g. `"conformance.get_current_time"`), inserted verbatim.
- `<args>` is the **canonical compact JSON serialization** of the
  arguments object: no whitespace between separators, object keys
  sorted lexically at every nesting level, and unicode characters
  emitted as characters rather than ASCII escape sequences. For an
  empty arguments object the value is `{}`; for `{"x": 1}` the value
  is `{"x":1}`; etc.

This format is normative because fixture `expected-log.jsonl` files
record it byte-for-byte. A port that uses any other format (e.g.
Ruby's native `Hash#inspect`, Python's `repr`) will produce
non-conformant fixtures even for the empty-args case the moment a
fixture exercises non-empty args. The reference implementations use
canonical compact JSON to comply with this rule.

### Adding a new agent fixture

1. Create `agents/<new-case-name>/`.
2. Write `README.md`, `manifest.json`, `provider-script.json`,
   `inputs.json`.
3. Generate `expected-log.jsonl` by running the reference
   implementation once:

    ```ruby
    require "harnas/conformance/runner"
    dir = "spec/conformance/agents/<new-case-name>"
    manifest  = JSON.parse(File.read("#{dir}/manifest.json"))
    script = if File.exist?("#{dir}/provider-script-stream.json")
               JSON.parse(File.read("#{dir}/provider-script-stream.json"))
             else
               JSON.parse(File.read("#{dir}/provider-script.json"))
             end
    inputs    = JSON.parse(File.read("#{dir}/inputs.json"))
    actual    = Harnas::Conformance::Runner.run_agent(
      manifest, script, inputs,
      streaming: File.exist?("#{dir}/provider-script-stream.json")
    )
    File.write("#{dir}/expected-log.jsonl", actual.map { |e| JSON.generate(e) }.join("\n") + "\n")
    ```

4. Review the generated `expected-log.jsonl` for correctness
   (does it match the intent of your fixture?). This file is the
   normative record; review it carefully.
5. Commit the whole directory in one commit.

---

## `fixtures/` — single provider round-trips

The files under `fixtures/` are the **normative** record of how each
provider's wire format looks for a fixed set of canonical cases. They are
part of the Harnas specification. Any Harnas implementation in any language
SHOULD be able to load these fixtures and replay them through its own mock
provider.

Each fixture captures **one real round-trip** with a provider's API. The
request is reproducible; the response is a single recorded sample. Provider
responses vary run-to-run (model temperature, changing model versions,
evolving API details), so fixtures are authoritative for *structure* but
not for *exact content*. Tests against fixtures MUST assert on shape, not
on, for example, the particular string of text the model happened to
produce.

## Layout

    fixtures/
    └── <case-name>/
        ├── README.md                  # describes the case (prompt, intent)
        └── <provider>/
            ├── request.json           # exact body we sent
            └── response.json          # exact body received

`<case-name>` is a short kebab-case slug describing the scenario. The
current cases:

- `hello-one-word` — prompt `"say hello in one word"`, expected behavior:
  the provider returns a single short word of text with no tool calls.

`<provider>` is the provider identifier used in Harnas. The current set:

- `anthropic` — Anthropic's Messages API
- `openai` — OpenAI's Chat Completions API
- `gemini` — Google Gemini's generateContent API

### A note on what `request.json` is

The `request.json` for a fixture is the input the smoke script handed to
the provider's `call` method, not necessarily the byte-exact body sent on
the wire. For Anthropic and OpenAI these happen to be identical (the
provider sends the request hash unchanged as the JSON body). For Gemini
they are not: the `model` field in `request.json` is routed by the
provider into the URL path (`.../models/<model>:generateContent`) rather
than the JSON body. This is normative — see `../02-provider-contract.md`,
R1 — and it means a mock provider that compares incoming `request` to the
recorded `request.json` is a faithful substitute for the live provider at
the contract level, even when the wire bytes differ.

## Regenerating a fixture

From the repo root:

    just record

This re-runs the canonical prompt against every live provider and rewrites
the files under `fixtures/hello-one-word/`. You must have valid API keys in
`reference/.env` for this to work. Regeneration is expected (not exceptional)
maintenance: provider APIs evolve, and fixtures should track reality.

After regenerating, inspect the diff. Non-cosmetic changes to `request.json`
(new required fields, renamed fields) may indicate a breaking change on the
provider's side and warrant a response across the spec. Changes to
`response.json` should be reviewed to confirm they are shape-compatible
with existing implementations; if not, the case may need to be versioned
or superseded.

## Adding a new case

1. Create `fixtures/<new-case-name>/README.md` describing the prompt and
   intent of the case.
2. Add a corresponding smoke invocation (or a dedicated recording script)
   that sends the canonical request with `--record
   spec/conformance/fixtures/<new-case-name>/<provider>`.
3. Run it against every supported provider.
4. Add a matching entry to the `just record` recipe so the case is
   regenerated together with the others.
5. Commit all resulting JSON files under one commit.

## Using a fixture as a mock

A mock provider (see `../02-provider-contract.md`) consumes a fixture
directory and replays `response.json` when called. The reference
implementation exposes this as `Harnas::Providers::Mock`. A typical use:

    provider = Harnas::Providers::Mock.new(
      fixture_path: "spec/conformance/fixtures/hello-one-word/anthropic"
    )
    response = provider.call(request) # returns the recorded response.json

In strict mode (the default), the mock verifies that the incoming `request`
deep-equals the recorded `request.json` after JSON normalization.
