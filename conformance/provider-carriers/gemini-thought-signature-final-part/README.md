# gemini-thought-signature-final-part

Gemini provider-carrier fixture for a non-tool final model part carrying
a part-level `thoughtSignature`.

The canonical semantic layer is a normal assistant text content block.
The carrier layer preserves the exact Gemini part so a later
`gemini.generateContent` projection can replay the `thoughtSignature`.
The fixture asserts both:

1. the follow-up `expect_request` contains the original provider-native
   part with `thoughtSignature`; and
2. re-ingesting the same native Gemini response produces the same
   `provider_parts` carrier.
