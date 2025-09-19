# Maximum Value Finder

This MirageScript walkthrough solves the classic "find the maximum number" task while keeping state updates visible to the reader.

## Problem sketch
Pick out the largest number from a list while documenting the intermediate reasoning.

## Runtime flow
- `remember` introduces the `pile` memory with both the incoming numbers and a champion placeholder.
- `describe_numbers` asks the model to summarize the list before any computation happens and binds the CLI input explicitly with `numbers is argument numbers`.
- `pick_champion` asks `gpt-5-mini` to select the biggest number and explain the choice.
- `show` lines prompt the interpreter to emit the stored explanation, the winning number, and the refreshed memory exactly once.

## Running the demo
```
uv run mirage examples/max_value_finder/max_value_finder.mirage --arg numbers="[3, 14, 7, 28]"
```
Because the LLM drives execution, the exact transcript changes from run to run. You should still see:
- a summary of the input numbers,
- an explanation of the selected maximum, and
- a description of the updated `pile` memory.

Encourage consistent output by keeping comments clear about which memories the `show` statements should emit.
