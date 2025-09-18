# Add Two Numbers — Linked-List Addition

A MirageScript retelling of the LeetCode problem where two numbers are stored as reversed linked lists.

## Problem sketch
Each list stores digits in reverse order. Your job is to add them and return the sum in the same format.

## Runtime flow
- `payload` holds both digit lists, a placeholder for the answer, and an empty note slot.
- `add_lists` asks `gpt-5-mini` to perform the addition, update `payload.result`, and announce the arithmetic.
- `explain_carries` records a brief explanation of each carry step in `payload.carry_notes`.
- `show` reveals the headline sentence, the carry narration, and the final payload memory.

## Expected transcript
Running `uv run mirage examples/add_two_numbers/add_two_numbers.mirage --dump-state --arg list_a="[2, 4, 3]" --arg list_b="[5, 6, 4]"` often yields:
```
input argument list_a [List<Int>] = [2, 4, 3]
input argument list_b [List<Int>] = [5, 6, 4]
remembered payload [LinkedLists] = list_a: [2, 4, 3]; list_b: [5, 6, 4]; result: (unset); carry_notes: (none)
ask add_lists -> headline [Text] = 342 + 465 = 807 -> [7, 0, 8].
update payload = list_a: [2, 4, 3]; list_b: [5, 6, 4]; result: [7, 0, 8]; carry_notes: (none)
ask explain_carries -> story [Text] = Added column by column: 2+5=7, 4+6=10 (carry 1, digit 0), 3+4+1=8. Digits stay reversed as [7,0,8].
update payload = list_a: [2, 4, 3]; list_b: [5, 6, 4]; result: [7, 0, 8]; carry_notes: Added column by column: 2+5=7, 4+6=10 (carry 1, digit 0), 3+4+1=8. Digits stay reversed as [7,0,8].
show: headline [Text] = 342 + 465 = 807 -> [7, 0, 8].
show: story [Text] = Added column by column: 2+5=7, 4+6=10 (carry 1, digit 0), 3+4+1=8. Digits stay reversed as [7,0,8].
show: payload [LinkedLists] = list_a: [2, 4, 3]; list_b: [5, 6, 4]; result: [7, 0, 8]; carry_notes: Added column by column: 2+5=7, 4+6=10 (carry 1, digit 0), 3+4+1=8. Digits stay reversed as [7,0,8].
```
The narrative may vary, but the model should always return the canonical sum list.
