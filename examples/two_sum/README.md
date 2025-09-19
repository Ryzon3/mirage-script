# Two Sum Helper

This MirageScript story tackles the classic Two Sum problem. The helper prompt guides `gpt-5-mini` to find indices while narrating the reasoning.

## Flow overview
- `remember quest` captures the input array and target along with a placeholder for the match.
- `find_pair` instructs the LLM to inspect the numbers, choose the first valid pair, and explain why it works.
- `show` steps nudge the interpreter to share the update with the user via `emit_output`.

## Running the demo
```
uv run mirage examples/two_sum/two_sum.mirage --arg numbers="[2, 7, 11, 15]" --arg target=9
```
Each run produces slightly different wording, but you should consistently receive:
- an explanation of which indices were selected,
- confirmation that the values add up to the target, and
- any additional notes the helper chose to narrate.

If you need strict formatting, add reminders inside the helper prompt about the exact text the model should output.
