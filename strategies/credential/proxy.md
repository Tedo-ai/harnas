# credential/proxy

`credential/proxy` is a `:pre_tool_use` strategy that injects
credentials into tool arguments immediately before execution without
persisting the credential value in the Log.

Version 1 only rewrites tool arguments. It does not inject per-tool
config and does not inject `bash_session` environment variables.

## Configuration

```json
{
  "strategy": "credential/proxy",
  "config": {
    "credentials": {
      "github": { "from": "env", "name": "GH_TOKEN" },
      "search": { "from": "literal", "value": "test-only" }
    },
    "routes": [
      {
        "tool": "fetch_url",
        "match": { "url_host": "api.github.com" },
        "inject": {
          "into": "headers",
          "key": "Authorization",
          "value": "Bearer {credential.github}"
        }
      }
    ]
  }
}
```

Credential sources:

- `env`: reads the environment variable named by `name`.
- `literal`: uses the inline `value`; intended for tests and local
  deterministic fixtures only.

Routes are evaluated in array order. Multiple matching routes may fire;
later routes win on key collisions. For `fetch_url`, a route may match
either `url_host` exactly or `url_host_glob` against the URL host. For
custom tools, an empty `match` object means "always fire for this tool".

The v1 injection target is `headers`. For `fetch_url`, injected headers
are merged into the outgoing HTTP request, with proxy-injected values
winning over agent-provided headers.

## Redaction

Credential values MUST NOT be appended to the Log and MUST NOT be
emitted through Observation. The recorded `:tool_use` Event preserves
the agent's original arguments. If a route injects a credential, the
strategy SHOULD append an `:annotation` Event with kind
`credential_injected` and metadata containing the route index and
logical credential names only.

If an upstream service echoes a credential in its response, that is
outside the strategy's control. Implementations should avoid including
injected values in errors they create themselves.

## Failure

If a route matches but the required credential is unavailable, the tool
call is refused with a `:tool_result` error visible to the agent. After
three consecutive missing-credential failures, the strategy emits a
terminal `:runtime_error` with reason
`credential_proxy_missing_persistent`.

Malformed strategy configuration fails manifest loading.
