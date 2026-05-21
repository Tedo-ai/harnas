# with-credential-proxy-injection

Verifies that `credential/proxy` injects an Authorization header into a
matching `fetch_url` call without persisting the credential value in the
Log.

The fixture uses the literal credential value `SECRET-DO-NOT-LOG` so
the conformance runners can assert that the actual tool handler received
the header. The expected Log intentionally contains only the logical
credential name `test_cred`, never the credential value.
