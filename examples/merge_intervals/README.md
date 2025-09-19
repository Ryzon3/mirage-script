# Merge Intervals

This MirageScript example narrates how overlapping intervals collapse into a tidy schedule.

## Flow overview
- `remember planner` seeds the scenario with the original intervals and a blank summary.
- The helper prompt tells `gpt-5-mini` to sort, merge, and explain each combination step.
- `show` encourages the interpreter to emit the merged intervals and a recap for the human.

## Running the demo
```
uv run mirage examples/merge_intervals/merge_intervals.mirage --arg intervals="[[1,3], [2,6], [8,10], [15,18]]"
```
Look for a narration that highlights where overlaps occur and what the merged output looks like. Tone and phrasing change each run, but the merged list should remain consistent with the algorithm.
