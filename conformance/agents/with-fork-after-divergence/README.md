# with-fork-after-divergence

Variant canary for `Session#fork(at_seq:)` from conformance inputs.

Unlike `with-fork-and-continue`, this fixture writes a divergent second turn
before forking back to `seq=1`. A runner that treats `fork` as no-op carries
the discarded turn into the next provider request and fails the fixture.
