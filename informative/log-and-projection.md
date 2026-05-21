# Log And Projection

[informative]

Harnas distinguishes two related but separate concepts: the durable Log
and derived Projections.

## The Log

The Log is the immutable, append-only source of truth for a Session. It
is:

- append-only: events are never modified or removed;
- persisted as JSONL;
- the canonical record for replay, audit, fork, and resume;
- the same shape across conforming implementations.

## A Projection

A Projection is a derived view of the Log used for a specific purpose.
Examples include:

- the provider request body sent to Anthropic, OpenAI, Gemini, or
  another provider;
- a UI transcript rendered for human reading;
- a token usage summary;
- a diff between two Sessions.

Projections are computed from the Log on demand. They are not the
durable truth. They can be lossy, reformatted, provider-specific,
compressed, or optimized for a particular consumer.

## The Invariant

The Log is the truth. Projections are views. Two consumers reading the
same Log should derive the same Projection given the same Projection
logic and options. Changes to Projection logic do not alter the
underlying Log.
