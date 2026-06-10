# strict-diff-extra-payload-field

Oracle corpus entry for conformance runner strict diffing.

The actual Log contains an extra `payload.garbage` field not present in
the expected Log. Runners that filter actual payload keys down to the
expected shape incorrectly accept this pair. Strict diffing must reject it.
