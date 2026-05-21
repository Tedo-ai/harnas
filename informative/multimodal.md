# Multimodal Messages

[informative]

Harnas v0.17.0 adds typed content blocks for user and assistant
messages. The goal is to let consumers attach images and PDFs without
turning the Log into a provider-specific request body. The Log records
what the user supplied; Projections decide how to translate that content
for Anthropic, OpenAI, Gemini, Ollama, or another provider.

## Content Blocks

The canonical `:user_message` payload is now a `content` array:

```json
{
  "content": [
    { "type": "text", "text": "what does this PDF say?" },
    {
      "type": "document",
      "media_type": "application/pdf",
      "name": "report.pdf",
      "source": { "kind": "ref", "uri": "attachment://a1b2c3" }
    }
  ]
}
```

The same content block shape is valid for `:assistant_message`, though
v0.17.0 implementations only emit assistant text blocks from current
provider responses. Tool results with non-text content and generated
assistant media are intentionally future work.

Three block types are defined in v0.17.0:

- `text`: `{ "type": "text", "text": "..." }`
- `image`: `{ "type": "image", "media_type": "...", "source": ..., "name": "..." }`
- `document`: `{ "type": "document", "media_type": "application/pdf", "source": ..., "name": "..." }`

Images support `image/jpeg`, `image/png`, `image/gif`, and
`image/webp`. Documents support `application/pdf` only. The `name` field
is optional but recommended because it improves transcript rendering and
capability fallback messages.

## Source Kinds

Binary blocks carry a `source` object:

```json
{ "kind": "base64", "data": "<base64-encoded-bytes>" }
```

Inline base64 is the most portable representation: the Log contains the
bytes and can be copied without a sidecar store. It is suitable for small
attachments, fixtures, and tests. It makes JSONL larger and should not
be the default for large files.

```json
{ "kind": "ref", "uri": "attachment://<opaque-id>" }
```

References are the canonical runtime shape. The Log stores an opaque
URI, and the configured `AttachmentStore` resolves it when a Projection
needs bytes. Consumers must not parse the id portion of an
`attachment://` URI; it may be a hash, UUID, filename key, database id,
or any other backend-specific value.

```json
{ "kind": "url", "url": "https://..." }
```

URL sources are useful when a provider can fetch the content directly or
when a downstream store has rehosted the attachment. A Projection may
pass a URL through, resolve and inline it, or fail clearly if the
provider path requires local bytes and the URL cannot be resolved.

## AttachmentStore

The reference implementations expose an AttachmentStore-style helper:

```text
AttachmentStore {
  put(bytes, media_type) -> AttachmentReference
  get(uri) -> (bytes, media_type)
  delete(uri) -> void
  exists(uri) -> bool
  list_referenced(log) -> [uri, ...]
}

AttachmentReference {
  uri: string
  media_type: string
  byte_size: int
  sha256: string
}
```

`FilesystemStore` is the default for CLI and local runtime helpers. For
a Session saved at `~/.harnas/runs/foo.jsonl`, attachments live under
`~/.harnas/runs/foo.attachments/`. Files are named from a SHA-256 digest
plus a media-type extension, so identical bytes deduplicate to the same
URI.

`MemoryStore` is for tests and fixtures. It keeps bytes in memory and is
not persisted. `InlineStore` is a pseudo-store: `put` returns a base64
source object so the bytes live directly in the Log, and `get` is never
used.

Production applications can implement their own stores. A Rails app
might back the interface with Active Storage; a service might use S3; a
desktop agent might keep a per-run directory next to a worktree. The
Projection only depends on `get(uri)`.

## Provider Projection

Projections translate content blocks to provider wire shapes. Text maps
directly everywhere. Images are sent as Anthropic image blocks, OpenAI
`image_url` parts, Gemini `inline_data`, or Ollama image arrays when the
model supports them. PDFs are sent as Anthropic document blocks or
Gemini `inline_data`.

References are resolved at projection time. Inline base64 is decoded and
re-encoded only as needed for the target provider. URLs are passed
through when the provider supports URL content and otherwise resolved or
handled through capability mismatch behavior.

Provider limits still apply. If a file is too large for a known
provider limit, the Projection should fail with a clear projection-time
error rather than sending a request that is known to be invalid. When a
limit is not statically known, the provider error is allowed to surface
normally.

## Capability Mismatch

Providers and models do not support the same media types. Each
implementation ships a conservative capability matrix and lets the
Manifest override flags:

```json
{
  "kind": "openai",
  "model": "my-custom-model",
  "capabilities": {
    "user_message_images": true,
    "user_message_documents": false
  },
  "capability_mismatch_behavior": "metadata_fallback"
}
```

`metadata_fallback` is the default. When a block is unsupported, the
Projection replaces it with a text annotation:

```text
[Note: A document was attached to this message but cannot be viewed by this provider.
 Type: application/pdf. Size: 12345 bytes. URI: attachment://a1b2c3.
 Use available tools to access the content.]
```

Fields are omitted when unavailable. For example, an inline base64 block
has no URI segment; an unnamed attachment has no Name segment. The point
is graceful portability: the model still receives enough information to
ask for a tool such as `read_pdf` or to tell the user it needs a
different model.

`error` is the strict behavior. The runtime emits a `:runtime_error`
with reason `capability_mismatch`, marks it terminal, and does not call
the provider. This is useful when an application requires the selected
model to truly see every attachment.

Unknown models are treated conservatively: unsupported unless a
Manifest capability override says otherwise.

## Compatibility

Pre-v0.17.0 Sessions used message payloads like:

```json
{ "text": "hello" }
```

Implementations continue to accept that shape forever. Parsed in-memory
views normalize it to:

```json
{ "content": [{ "type": "text", "text": "hello" }] }
```

New runtime-written Events use `content`. The `text` field is read-only
legacy compatibility.

## Examples

A CLI can attach a file by creating a user message with text plus a
base64 block:

```json
{
  "content": [
    { "type": "text", "text": "summarize this" },
    {
      "type": "document",
      "media_type": "application/pdf",
      "name": "brief.pdf",
      "source": { "kind": "base64", "data": "..." }
    }
  ]
}
```

A web app should usually store bytes first and put only a reference in
the Log:

```json
{
  "type": "image",
  "media_type": "image/png",
  "name": "screenshot.png",
  "source": { "kind": "ref", "uri": "attachment://abc123" }
}
```

For Anthropic and Gemini, a PDF reference resolves to provider-visible
document bytes. For OpenAI chat completions, the default fallback turns
the PDF into metadata text; the model can then call an application tool
to inspect the URI if one is available.

Attachments are replay dependencies. A saved Session that contains
`attachment://` references is reproducible only when the referenced
AttachmentStore content is preserved with it. Use `list_referenced(log)`
to build cleanup, export, and garbage-collection flows.
