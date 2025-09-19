# Maximum Value Finder

This MirageScript walkthrough solves the classic "find the maximum number" task while keeping state updates visible to the human reader.

## Problem sketch
Pick out the largest number from a list while narrating the process in playful language.

## Runtime flow
- `remember` introduces the `pile` memory with both the incoming numbers and a champion placeholder.
- `describe_numbers` invites the model to narrate the list before any computation happens.
- `pick_champion` asks `gpt-5-mini` to select the biggest number and recap the choice.
- `show` lines remind the interpreter to call `emit_output` so humans see the story, the winning number, and the refreshed memory.

## Running the demo
```
uv run mirage examples/max_value_finder/max_value_finder.mirage --arg numbers="[3, 14, 7, 28]"
```
Because the LLM now drives execution, the exact transcript changes from run to run. You should still see:
- a summary of the input numbers,
- a celebratory note about the champion, and
- a description of the updated `pile` memory.

Encourage consistent output by keeping comments and prompt instructions explicit about when to call `emit_output`.
