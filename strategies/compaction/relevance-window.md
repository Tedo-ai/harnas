# RelevanceWindow *(reserved)*

**Family:** Compaction

**Selection:** Relevance (top-k events by semantic similarity to
the current turn's context).
**Replacement:** Marker (a fixed format string for the
non-retrieved gaps between retained events).
**Trigger:** per-turn, or threshold-based.

**Purpose:** Retrieval-based compaction. Instead of keeping the
most recent events (Tail selection), keep the events that are
most *relevant* to the current turn — even if they are far back in
the Log. Older events that remain relevant stay visible;
irrelevant recent events may be dropped.

**Status:** Name reserved. Implementation requires spec primitives
not yet in the catalog. This stub exists so the naming slot in
the catalog is committed to.

## Required primitives (not yet in the spec)

Implementing `RelevanceWindow` requires:

1. **Embeddings primitive.** A pure function
   `embed(text) -> Vector<Float>` that turns an event's text
   payload into a fixed-dimension embedding. Probably delegated
   to a Provider-adjacent service (e.g. Anthropic/OpenAI/Gemini
   embedding endpoints) with an `Embedder` type analogous to the
   `Provider` type.
2. **VectorStore primitive.** An atomic operation for storing
   embeddings keyed by event seq, and for querying by cosine
   similarity: `vector_store.query(query_embedding, top_k)
   -> [seq, ...]`. Whether the store is in-memory, durable, or
   remote is an implementation detail; the spec primitive is the
   query interface.
3. **Extension to `17-composition-rules.md` R2** adding Embedder
   and VectorStore as atomic operations.

## Sketched Algorithm (not yet normative)

```
algorithm RelevanceWindow(embedder, vector_store, top_k,
                          summary_format = "[↳ retrieved $K of $N earlier messages]"):
  on :pre_projection(session):
    visible := filter(Mutations.apply(session.log), is_message_event)
    if no new events since last call: return

    current_context := recent-window(visible, n=recent_n)
    query_embedding := embedder.embed(text_of(current_context))
    retained_seqs   := vector_store.query(query_embedding, top_k).map(&:seq)

    candidates := seqs_of(visible) - retained_seqs - seqs_of(current_context)
    safe := tool_pair_safe_range(session.log, candidates)
    Actions.Compact(session, replaces: safe, summary: ...)
```

## Block-strip (expected signature)

```
relevance_window   [S|↳ retrieved · 3 chunks|A|  |Tr|  |U]   ← non-contiguous retained events
```

Retained events appear in seq order; non-retrieved ranges collapse
to a retrieval marker.

## Why this is reserved, not shipped

Adding Embeddings + VectorStore to Layer 1 is a real primitive
addition. We want to do it when a concrete use case forces the
design, not preemptively.
