# DocumentFold *(forthcoming)*

**Family:** Compaction

**Selection:** FoldAll (fold every completed turn into a
maintained document; drop the raw turns from the projected view).
**Replacement:** StateDocument (a single synthetic event that is
superseded each turn with the updated document content).
**Trigger:** per-turn (runs at every `:pre_projection`; the
document is updated after every completed turn).

**Purpose:** The most aggressive compaction strategy. No raw turn
history is visible to the model; only a continuously-maintained
state document plus the most recent turn. The document is the
agent's only memory of everything before now.

**Status:** Name reserved. Implementation requires spec primitives
not yet in the catalog. This stub exists so the naming slot in
the catalog is committed to.

## Required primitives (not yet in the spec)

Implementing `DocumentFold` requires one of:

1. **Mutable synthetic events.** Extend `:compact` semantics (or
   add a new Mutation Event type) such that a later event can
   *supersede* an earlier synthetic event. `Mutations.apply`
   would follow supersession chains similar to how `:revert`
   composes transitively. This keeps the document inside the Log.
2. **External state primitive.** An atomic operation for read +
   write to a named cell (file, DB row, KV store) with
   read-through semantics into the Projection. Turns the state
   document into a Layer-1 addressable resource outside the Log.

Option 1 is cleaner (keeps everything in the Log, preserves
audit/replay guarantees) but requires extending the Mutation
Events design. Option 2 is simpler but adds a new I/O primitive.

## Sketched Algorithm (not yet normative)

```
algorithm DocumentFold(projection, provider, ingestor,
                       document_prompt = DEFAULT_DOCUMENT_PROMPT):
  on :pre_projection(session):
    latest_turn_events  := events from the current in-flight turn
    prior_document_seq  := last :state_document event's seq
    prior_document_text := :state_document event's payload.text, or "" if none

    # One LLM turn: "given the prior document and the just-completed
    # turn, produce the updated document."
    sub_log := build_sub_log(prior_document_text, latest_turn_events, document_prompt)
    request := projection.call(sub_log)
    response := provider.call(request)
    updated_document := last_assistant_text(ingestor.call(response))

    # Compact everything-so-far into the new document, replacing the
    # prior :state_document event if there was one.
    all_seqs_except_current_turn := ...
    Actions.Compact(
      session,
      replaces: all_seqs_except_current_turn,
      summary: updated_document
    )
```

## Block-strip (expected signature)

```
document_fold   [S|state_doc.md · entire run so far              |U]   ← single wide synthetic + latest turn
```

The nearly-flat signature is diagnostic — if you see it in a
production token-per-turn chart, you are running DocumentFold.

## Why this is reserved, not shipped

Deciding between the mutable-synthetic-event extension and the
external-state primitive is a load-bearing design choice that
deserves its own phase. Naming the strategy now signals the design
direction; implementing it waits on that choice.
