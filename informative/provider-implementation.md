# Provider Implementation

[informative]

Reference implementations SHOULD use direct provider HTTP APIs rather
than provider SDK packages for their built-in providers. Harnas defines
the Projection and Ingestor boundary itself; inserting a provider SDK
between those two layers can hide wire-shape changes, retry behavior,
stream framing, and provider-specific errors that the Log is meant to
make visible.

The current reference implementations follow this convention:

| Implementation | Provider transport |
|---|---|
| Go | Standard-library `net/http` for buffered and streaming providers. |
| Ruby | `httpx` for buffered providers; `Net::HTTP` and curl subprocesses for SSE streaming paths where chunk buffering matters. |
| Python | Standard-library `urllib.request` helpers for buffered and streaming providers. |

Direct HTTP does not mean every implementation must share the same HTTP
client library. It means the implementation owns the provider request
body, response parsing, error mapping, retry policy, and streaming event
translation explicitly rather than delegating those semantics to an SDK.

Future provider implementations should document any deliberate exception
to this convention. If an SDK is adopted for a provider, the
implementation should still preserve the exact Harnas Projection and
Ingestor semantics and should add conformance or smoke coverage for any
SDK-shaped behavior that can affect the Log.
