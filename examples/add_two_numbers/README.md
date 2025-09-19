# Add Two Numbers (Linked List Style)

This MirageScript program mirrors the classic LeetCode problem: add two numbers represented by linked lists and narrate the process.

## Flow overview
- Objects define the `DigitList` shape so the model remembers how to describe carries and next pointers.
- Helpers walk through each list, compute the sum digit by digit, and explain the carry handling.
- `show` lines remind the interpreter to report the assembled result list.

## Running the demo
```
uv run mirage examples/add_two_numbers/add_two_numbers.mirage --arg list_a="[2, 4, 3]" --arg list_b="[5, 6, 4]"
```
Expect vivid storytelling that still respects the underlying math. Wording varies every run, but the helper should:
- describe the traversal of both lists,
- outline the carry propagation, and
- finish with the summed list in the correct order.

Tighten your prompts if you need machine-readable output or deterministic phrasing.
