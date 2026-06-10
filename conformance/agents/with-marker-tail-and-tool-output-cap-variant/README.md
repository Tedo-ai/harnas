# with-marker-tail-and-tool-output-cap-variant

Variant canary for fixture-aware MarkerTail implementations. It uses the
same ToolOutputCap + MarkerTail composition as
`with-marker-tail-and-tool-output-cap`, but changes the user literals and
uses `max_messages=4, keep_recent=1`. The expected MarkerTail replacement is
non-contiguous because the earlier tool pair has already been compacted.
