# Strategy Catalog

This directory is the browsable catalog of **strategies** — the
hook-handler packs that implement the different architectural choices
a Harnas installation can make. Every strategy has a one-page spec
stub declaring its purpose, configuration, arbitrary choices, and
benchmark profile. The implementations live under
`reference/lib/harnas/strategies/`.

Each family's README gives the pattern for writing strategies in
that family and the shared helpers strategies can rely on. The
normative *contract* every strategy in a family must honor lives in
the numbered spec section for that family (e.g. `05-compaction.md`).

## Families

| Family | Status | Spec section | Strategies currently in catalog |
|---|---|---|---|
| [Compaction](compaction/) | shipped | [05-compaction.md](../05-compaction.md) | MarkerTail, TokenMarkerTail, SummaryTail (RelevanceWindow, DocumentFold reserved) |
| [Permission / trust](permission/) | shipped | [07-permission.md](../07-permission.md) | AlwaysAllow, DenyByName, HumanApproval (ClassifierGated, SandboxedExec, TwoTier reserved) |
| Tool discovery | reserved | — | AllUpfront, DeferredSearch, MCPRouted, LazyByName |
| Prompt assembly | reserved | — | LinearConcat, StaticDynamicBoundary, TemplateVariants |
| Caching | reserved | — | SimplePrefix, DeferredToolFolding, DeepPrefixManagement |
| Retry / recovery | reserved | — | SimpleRetry, Tombstone, EscalateToUser |
| Concurrency | reserved | — | Serial, PartitionedBatch, RwLock |
| Persistence | reserved | — | InMemory, JSONLAppendOnly, DAGWithBoundaries |
| Memory injection | reserved | — | CLAUDE.md-style, AGENTS.md-style, DAGRetrieve |
| Meta-reflection | reserved | — | PerTurn, OnBudget, OnFailure |

The estimated maturity count is **~40–50 strategies** across all
families. Each is a small, documented, benchmarkable artifact.

## The structure of a canonical strategy

A Harnas canonical strategy is:

1. **Language-neutral pseudocode** in the strategy's spec stub
   ("Algorithm (normative)" section) — the authoritative description
   of the strategy's behavior, including normative string literals
   (marker text, prompt text, reason phrases). Every language
   implementation is a port of this pseudocode.
2. **A "Composed of" declaration** (Hook × Predicate × Action) in
   the stub — normative, matches the pseudocode.
3. **An implementation** in each supported language. The Ruby version
   lives under `reference/lib/harnas/strategies/<family>/<name>.rb`
   and is informative (one of possibly many conformant ports).
4. **A test file** under `reference/spec/harnas/strategies/...`
   verifying the Ruby port matches the pseudocode, including the
   normative defaults.
5. **Optionally** a benchmark profile (results of running the
   strategy on canonical scenarios via the harness in
   [`06-benchmarks.md`](../06-benchmarks.md)).

See [`00-conventions.md`](../00-conventions.md) §"Specification
Layers" for the distinction between canonical strategies (in the
spec) and user strategies (an organization's own code).

Harnas provides **sharp primitives and per-family shared helpers** —
not a composition grammar. Strategies compose from helpers as they
see fit; the family README documents the pattern; the catalog
surfaces the choices each strategy made.

## Writing a new canonical strategy

Canonical strategies go in the spec. Follow this order:

1. Pick (or create) a family.
2. Read the family's README for the pattern and helper catalog.
3. **Write the spec stub first**, including the Algorithm pseudocode
   and any normative strings. This is the authoritative description.
4. Implement the pseudocode as plain Ruby using the family's helpers.
5. Add tests that verify both the defaults (normative strings
   byte-identical) and that caller overrides are honored.
6. Run `just benchmark` to capture its profile on existing scenarios;
   add rows to the stub's benchmark section.

## Writing a user strategy (your own)

User strategies are not in the spec. They live in your own codebase.
The pattern (Ruby example; the contract is language-neutral):

```ruby
require "harnas"
# (optionally) require canonical strategies you want to reuse
# require "harnas/strategies/compaction/snip"

module Acme
  module Strategies
    class MyRetentionPolicy
      def self.install(**config)
        # construct an instance with the validated config and
        # register its handler(s) on Harnas::Hooks.
        # Returns the registered handler so callers can Hooks.off it.
      end
      # ... your strategy here, using Harnas primitives
    end
  end
end

Acme::Strategies::MyRetentionPolicy.install(...)
```

### The contract is the class-level entry point

A strategy MUST expose a class-level `install(**config)` (or its
language equivalent — a static method, factory function, etc.) that
takes the manifest's `config` Hash and registers whatever Hooks the
strategy needs. The Ruby reference also defines an instance-level
`install` method that the class-level one delegates to; that is
**implementation idiom, not part of the contract**. Languages that
cannot have class-level and instance-level methods of the same name
(Python, Rust, Go) MAY inline the registration inside the class-level
entry. The catalog spec stubs and the Ruby reference both assume the
two-method form for readability; readers should treat the inner
delegation as a Ruby convenience, not a normative requirement.

Your strategy MUST honor `17-composition-rules.md` R1 (build from
the spec's atomic operations; no harness-internal escape-hatch
callables). Beyond that it's your code — not tracked in the Harnas
catalog, not constrained by the spec. The three-layer separation
in [`00-conventions.md`](../00-conventions.md) §"Specification
Layers" exists precisely so organizations can build this layer fit
to their workflow without fighting the framework.

## Observation around invocation

**R5.** A Strategy SHOULD emit `:strategy_started` and
`:strategy_completed` Observation events per Hook invocation, with
payload `{ name, hook_point }` for the start and
`{ name, hook_point, effect }` for completion. The `effect` field MUST
be one of `"noop"`, `"mutated"`, `"refused"`, or `"error"`.

These Observation events MUST NOT be appended to the Log. They are
live telemetry: useful for audit, debugging, benchmark traces, and UI
inspection, but not part of the durable semantic conversation.

## Canonical vs user strategies — separability

Canonical strategies in the Ruby reference are independently
requireable: `require "harnas/strategies/compaction/snip"` loads
only Snip. `require "harnas"` alone loads the machinery (Layer 1
in the spec) without opting you into any canonical strategy.
Organizations can mix-and-match canonical strategies and their
own without inheriting the whole catalog.

## Why this shape, not a framework

The "strategy" layer in Harnas could in principle be a framework
with slots for trigger / selection / action / etc. It deliberately
isn't. Reasons:

- Strategies are diverse enough that any grammar would be bent by
  the second or third family (e.g. strategies that themselves make
  LLM calls, strategies with multi-step workflows).
- The cost of imposing a grammar everyone has to learn, and that
  cross-language implementers have to match, exceeds the benefit of
  the mechanical composability it buys.
- Sharp primitives + documented helpers + small-but-explicit
  per-strategy specs is enough structure without being a cage. A
  strategy that doesn't fit the pattern can simply ignore it and
  still honor the family contract.

See the devlog entry for 2026-04-20 for the design discussion that
led here.
