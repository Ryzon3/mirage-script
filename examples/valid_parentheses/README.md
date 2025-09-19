# Valid Parentheses

Stack-based validation with clear commentary. This MirageScript script prompts the model to inspect a bracket sequence and explain whether it stays balanced.

## Flow overview
- `remember trail` introduces the bracket string and a placeholder verdict.
- The helper prompt explains the stack algorithm and asks for a step-by-step explanation.
- `show` lines remind the interpreter to share both the verdict and the reasoning via `emit_output`.

## Running the demo
```
uv run mirage examples/valid_parentheses/valid_parentheses.mirage --arg sequence="{[]()}"
```
Expect a concise recap of the stack activity together with a clear yes/no answer. Because the LLM owns the runtime, phrasing varies, but the judgement should always match the input.
