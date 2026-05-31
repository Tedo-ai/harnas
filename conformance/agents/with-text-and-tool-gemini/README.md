# with-text-and-tool-gemini

Gemini function-call projection with non-empty model text on the same turn as
the function call.

The second provider request asserts that the prior model turn projects both the
text part and the `functionCall` part before the `functionResponse`.
