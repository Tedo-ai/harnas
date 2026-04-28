# Compaction Strategies

This directory is the **strategy catalog** for the compaction family.
Each strategy is one short Markdown stub declaring its purpose,
configuration surface, arbitrary choices, and benchmark profile.
The implementation for each is plain Ruby — not a framework — living
under `reference/lib/harnas/strategies/compaction/<name>.rb`.

The family contract (R1–R6 — what every compaction strategy MUST
honor regardless of its implementation) is specified once in
[`../../05-compaction.md`](../../05-compaction.md). This README is
family-level documentation about *how compaction strategies are
written*, so authors can follow the pattern and cross-language
implementers can port the catalog faithfully.

## Catalog

| Strategy | Selection | Replacement | Trigger | LLM call? | Spec |
|---|---|---|---|---|---|
| MarkerTail | Tail | Marker | MessageCount | no | [marker-tail.md](marker-tail.md) |
| TokenMarkerTail | Tail | Marker | TokenEstimate (% of budget) | no | [token-marker-tail.md](token-marker-tail.md) |
| SummaryTail | Tail | LLMSummary | MessageCount | yes (via Projection + Provider + Ingestor) | [summary-tail.md](summary-tail.md) |
| ToolOutputCap | Targeted (tool pair) | PrefixWithNote | PayloadSize | no | [tool-output-cap.md](tool-output-cap.md) |
| *RelevanceWindow* | *Relevance (top-k)* | *Marker* | *per-turn or threshold* | *no (retrieval, not generation)* | *forthcoming — requires Embeddings + VectorStore primitives* |
| *DocumentFold* | *FoldAll* | *StateDocument (maintained)* | *per-turn* | *yes (document update via LLM)* | *forthcoming — requires mutable-synthetic-event or external-state primitives* |

## How compaction strategies are written

A compaction strategy is plain Ruby that installs as a
`:pre_projection` hook handler and appends a `:compact` Mutation
Event when it decides to. That's the entire contract. Everything
else is the strategy's own code.

Reference strategies in this catalog follow a common pattern for
readability:

```ruby
class MyStrategy
  def self.install(**config)
    new(**config).install
  end

  def initialize(**config)
    # validate config
  end

  def install
    handler = method(:on_pre_projection)
    Harnas::Hooks.on(:pre_projection, handler)
    handler
  end

  def on_pre_projection(session:)
    messages = Harnas::Compaction::Helpers.message_events(session.log)
    return unless my_trigger_condition?(messages)

    candidate_seqs = my_selection(messages).map(&:seq)
    safe_seqs = Harnas::Compaction::Helpers.tool_pair_safe_range(
      session.log, candidate_seqs
    )
    return if safe_seqs.empty?

    session.log.append(
      type: :compact,
      payload: Harnas::Events::Compact.new(
        replaces: safe_seqs,
        summary: my_summary(safe_seqs)
      ).to_h
    )
  end
end
```

Authors are expected to call the Compaction Helpers rather than
reinvent them — the helpers are the family's shared safety rails.

## Shared helpers (from `reference/lib/harnas/compaction/helpers.rb`)

| Helper | Purpose |
|---|---|
| `Helpers.message_events(log)` | Effective events filtered to the 4 real message types (excludes `:summary` for idempotency) |
| `Helpers.estimate_tokens(events)` | Cheap 4-chars-per-token estimate |
| `Helpers.tool_pair_safe_range(log, candidate_seqs)` | Drops orphan halves of tool_use/tool_result pairs from a candidate seq list |

The tool-pair safety helper MUST be called by any strategy that
might compact across tool-call boundaries — otherwise a compacted
`:tool_use` whose `:tool_result` remains visible produces a
provider-side malformed-request error.

## Spec stub template

Every strategy's spec stub lives next to this README and looks like:

```markdown
# <StrategyName>

**Family:** Compaction

**Purpose:** <one sentence>

## Configuration
- `<param>:` <type>, default <value>

## Arbitrary choices
- Trigger: <exact condition>
- Selection: <keep-recent / preserve-first / sliding-window / …>
- Tool-pair safety: <yes via Helpers.tool_pair_safe_range / no>
- Summary: <constant text / template / LLM / structured>
- Idempotency: <how the strategy avoids re-triggering on its own output>

## When to use
<one paragraph>

## Benchmark profile
<latest results from canonical scenarios>
```

When adding a new compaction strategy, fill in the template,
implement the Ruby, add tests. The arbitrary choices line-by-line
comparison between strategies is the value the catalog provides.

## Visualization convention

Every canonical compaction strategy SHOULD include a **block-strip
figure** in its spec stub showing the shape of `messages[]` after
the strategy has fired. The block-strip is the family's standard
visual language; two strategies that produce visually similar
strips on the same Log behave similarly; two that diverge
editorially produce visibly different strips.

### Format

The block-strip is a single horizontal row of colored blocks, one
block per Event contributing to the projected messages array after
`Mutations.apply`. Dropped events (compacted by this strategy) are
shown faded in-position for reference. Synthetic events (the
`:summary` Event a `:compact` expands to) are shown at the position
of the lowest replaced seq, spanning the visual range they replace.

| Attribute | Encoding |
|---|---|
| **Row order** | chronological (seq order), left to right |
| **Block width** | approximately proportional to the event's token contribution |
| **Block color** | event type (see palette below) |
| **Block opacity** | 100% for visible; ~20% for dropped-but-shown-faded |
| **Synthetic block label** | short text: `≡ summary · N turns`, `↳ retrieved · N chunks`, `state_doc.md · …` |

### Palette

Strategies MAY use alternative colors for accessibility, but the
semantic mapping SHOULD match:

| Event type | Color (conceptual) |
|---|---|
| `:user_message` | blue |
| `:assistant_message` | cream / off-white |
| `:tool_use` | amber |
| `:tool_result` | teal |
| `:summary` (synthetic) | taupe / desaturated |
| retrieved chunks (future) | violet |
| system prompt (future) | purple |

### A comparison strip

When more than one strategy is being explained, arrange the strips
as rows of a table: one row per strategy, labeled on the left with
the strategy name and key configuration, with two right-hand
columns — *what it preserves* and *what breaks*. This layout is the
adopted family-level figure for documentation and blog posts about
compaction strategies.

Draft ASCII form (prose-stub-safe) of the block-strip:

```
baseline           [S|U|A|Tu|Tr|A|Tu|Tr|U|A|U|A|Tu|Tr|U]        ~38,400 tok
sliding_window     [S|d|d|d |d |d|d |d |d|d|d|A|Tr|U]          ~8,100  tok   dropped · 11 turns
summarize_tail     [S|≡ summary · 11 turns              |Tr|A|U] ~9,200  tok
semantic_retrieval [S|↳ retrieved · 3 chunks|Tr|  |A|  |U]       ~6,800  tok
state_document     [S|state_doc.md · entire run so far        |U] ~3,400 tok
```

The rendered form (SVG or similar) follows the same structure with
proper proportional widths, colors, and connecting lines between a
synthetic block and the range it replaced.

### Where the figure lives

In a spec stub's **Visualization** section (sibling to *Composed
of* and *Algorithm*). A stub MAY inline an ASCII approximation for
offline readability and link to a higher-fidelity rendered figure
under `spec/figures/<family>/<name>.svg` once those figures are
added to the spec tree.

## Out of scope for this README

- **R1–R7 family contract** — lives in [`../../05-compaction.md`](../../05-compaction.md).
- **Benchmark protocol** — lives in [`../../06-benchmarks.md`](../../06-benchmarks.md).
- **Hook mechanism** — lives in [`../../14-hooks.md`](../../14-hooks.md).
