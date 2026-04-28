# 06 — Benchmarks

This document specifies the Harnas **Benchmark harness**: the shape
of canonical Scenarios, how a Runner executes them against Strategy
combinations, which metrics are normative, and how implementations
should present comparison results.

## Purpose

[informative]

Harnas's value proposition is **empirical comparison of architectural
choices.** A benchmark suite lets any Harnas implementation report,
on the same canonical workloads, how different Strategy combinations
(compaction, permission, tool discovery, retry, caching, …) affect
measurable outcomes (token cost, latency, compaction counts, tool-
invocation rates). Results are reproducible and shareable across
implementations.

## Scenarios

**R1.** A **Scenario** MUST be a value object carrying:

- `name:` (non-empty String) — a stable identifier.
- `description:` (String) — prose explaining the scenario's intent.
- `prompts:` (non-empty Array<String>) — a sequence of user messages,
  in turn order.
- `canned_responses:` (Array<String>, optional) — pre-recorded
  assistant responses; when present, Scenarios can run
  deterministically without live Provider calls.

**R2.** Scenarios MUST be serializable to a cross-language format.
The reference implementation stores Scenarios as YAML files under
`spec/conformance/scenarios/`; any format that round-trips the
required fields is permitted.

## Runner

**R3.** A **Runner** accepts a Scenario plus a Strategy configuration
and returns a **Result** carrying the metrics observed during the
run. A Runner:

- MUST reset Observation and Hook state between runs (so results
  from one run cannot leak into the next).
- MUST capture Observation events across the whole Scenario.
- MUST report at least the metrics defined in R4.
- MAY extend Result with additional fields (Harnas SHOULD treat
  unknown fields as informative).

**R4.** A Runner Result MUST report:

- `scenario_name:` (String)
- `strategy_name:` (String)
- `turns:` (Integer; count of `:provider_called` Observation events)
- `compactions:` (Integer; count of `:event_appended` events whose
  Event type is `:compact`)
- `total_input_tokens:` (Integer; sum of `:tokens_consumed.input_tokens`)
- `total_output_tokens:` (Integer; sum of `:tokens_consumed.output_tokens`)
- `total_duration_ms:` (Integer; sum of `:provider_responded.duration_ms`)

**R5.** Runners SHOULD use deterministic Providers (canned responses)
by default so strategy comparisons are not confounded by output
variance. A live-API mode MAY be provided for regression testing
against real models; live runs SHOULD be repeated and their results
averaged.

## Strategy Configurations

**R6.** A Strategy Configuration is a (name, install callable) pair.
The `install` callable MUST register hook handlers and MAY return
state for later cleanup. The Runner invokes `install.call` inside a
scoped Hook registry so handlers are automatically unregistered at
the end of the run.

## Report

**R7.** Results from multiple (Scenario × Strategy) runs MUST be
renderable as a comparison table grouped by Scenario. Columns:
strategy name, turns, compactions, input tokens, output tokens,
duration. Implementations MAY add columns; readers MUST tolerate
unknown columns.

## Canonical Scenarios

[informative]

The reference implementation ships the following Scenarios under
`spec/conformance/scenarios/`:

| Name | Purpose |
|---|---|
| `long-conversation` | Twelve prompts exercising context growth; a natural baseline for compaction comparisons. |

Additional Scenarios (e.g., `tool-heavy`, `many-short-turns`,
`cost-sensitive`) are future work. Contributors SHOULD add Scenarios
that target specific Strategy decisions they want to compare.

## Observation Integration

[informative]

The Benchmark harness adds no new canonical Observation events; it
reads the existing vocabulary defined in `13-observation.md`. The
signals it aggregates:

| Observation event | What the benchmark measures |
|---|---|
| `:provider_called` | Turn count |
| `:provider_responded` | Per-turn duration, summed |
| `:tokens_consumed` | Input/output token totals |
| `:event_appended` (filtered to `:compact`) | Compaction count |
| `:event_appended` (filtered to `:tool_result`) | Tool invocation count (future metric) |
| `:hook_handler_failed` | Strategy-induced errors (future metric) |

## Versioning Note

**R8.** The Scenario value shape, the Result value shape (R4), and
the default metric set are stable within a major spec version.
Additional fields in either MAY be added; consumers MUST ignore
unknown fields.
