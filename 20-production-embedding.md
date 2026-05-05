# 20. Production Embedding

This section is informative. It describes the recommended shape for
embedding Harnas in a production application, especially a web
application serving concurrent users.

Harnas specifies the agent harness layer. It does not own user
identity, authorization, queues, memory storage, databases, web
transports, billing, or UI. Production adopters compose those concerns
around a Harnas Session.

## Request Shape

The recommended request lifecycle is:

1. Load or create one Session for the conversation.
2. Build provider, projection, ingestor, tools, and strategies for that
   Session.
3. Append the user's message to the Session Log.
4. Run one AgentLoop turn.
5. Stream deltas or return the final assistant message to the client.
6. Persist the Session as JSONL.

Each live conversation should have its own Session. Implementations
SHOULD avoid sharing hook registries, observation subscribers,
strategy instances with mutable state, or tool permission decisions
across unrelated Sessions.

## Persistence Boundary

Session JSONL is the recommended persistence boundary. Store it as the
conversation source of truth, or store an equivalent event-row form that
can be emitted as canonical Session JSONL.

Applications MAY also maintain derived indexes for search, analytics,
or UI summaries. Those indexes are caches. The Session Log remains the
authoritative replay source.

## Streaming To Clients

When using streaming providers, applications SHOULD forward delta
Observation events to the client as they are emitted. As of §15,
streaming transport events are Observation-only: they are visible live,
but they are not appended to the durable Session Log. The consolidated
semantic result, such as `:assistant_message` or `:tool_use`, is what
lands in the Log on successful stream completion.

If a stream fails, the client may have already seen partial deltas over
Observation. Those transport details remain observable but are not part
of the saved JSONL unless the application has attached a DeltaLogger
sidecar as described in §13. Applications should surface the failure
using the later runtime/provider error signal rather than trying to
rewrite the durable Log.

## Provider Errors

Provider failures are part of the Log. Applications SHOULD inspect
terminal `:provider_error` Events when deciding whether to show an
error state, offer retry, or stop the conversation.

Retries are a runtime policy choice. Harnas's contract is that retry
attempts and final provider failures are visible in the Log.

## Fork, Retry, And Conversation Trees

`Session#fork(at_seq:)` exists for rewind-and-retry workflows:

- retrying from before a provider failure,
- exploring alternate prompts,
- implementing conversation branches,
- debugging by replaying from a known prefix.

The forked Session should be persisted independently. Its metadata
should record `forked_from` and `forked_at_seq` so applications can
display or audit the relationship.

## Memory

Cross-Session memory is outside Harnas. Applications that extract facts
from older Sessions should store them in their own memory layer and
compose selected facts into the next Session's system prompt or initial
context Events.

The important boundary is that a Session Log is single-conversation.
External memory may inform a new Session; it is not silently part of
the old Session's Log.

## Observability

Observation events are useful for telemetry, UI timelines, and
debugging, but they are not the source of truth. The Log is. Production
systems SHOULD treat Observation as a live signal and Session JSONL as
the replayable record.

## What Harnas Does Not Provide

Harnas deliberately does not provide:

- web servers,
- database schemas,
- authentication or authorization systems,
- background job orchestration,
- memory extraction/retrieval systems,
- multi-agent scheduling,
- billing or tenant isolation,
- UI components.

Those are application concerns. Harnas should remain small enough to be
embedded inside any of them.
