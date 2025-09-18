# Valid Parentheses Checker

This MirageScript scene recreates the "valid parentheses" interview staple.

## Problem sketch
Check whether a string containing `()[]{}` characters is properly balanced using the implied stack algorithm.

## Runtime flow
- `puzzle` remembers the bracket sequence along with placeholder verdict and reasoning fields.
- `assess_balance` asks `gpt-5-mini` to mentally run the stack procedure and set `puzzle.verdict`.
- `explain_balance` retells the stack operations and stores the story in `puzzle.reasoning`.
- `show` statements print the verdict, the explanation, and the final puzzle memory.

## Expected transcript
Running `uv run mirage examples/valid_parentheses/valid_parentheses.mirage --dump-state --arg sequence="{[]()}"` usually yields:
```
input argument sequence [Text] = {[]()}
remembered puzzle [BracketPuzzle] = sequence: {[]()}; verdict: unknown; reasoning: (not yet)
ask assess_balance -> verdict [Text] = Balanced — every opener found its closer.
update puzzle = sequence: {[]()}; verdict: Balanced; reasoning: (not yet)
ask explain_balance -> summary [Text] = Used a stack: push {, [, (, then pop (, ], }. All matched, so Balanced.
update puzzle = sequence: {[]()}; verdict: Balanced; reasoning: Used a stack: push {, [, (, then pop (, ], }. All matched, so Balanced.
show: verdict [Text] = Balanced — every opener found its closer.
show: summary [Text] = Used a stack: push {, [, (, then pop (, ], }. All matched, so Balanced.
show: puzzle [BracketPuzzle] = sequence: {[]()}; verdict: Balanced; reasoning: Used a stack: push {, [, (, then pop (, ], }. All matched, so Balanced.
```
The exact words vary, but the stack logic remains intact.
