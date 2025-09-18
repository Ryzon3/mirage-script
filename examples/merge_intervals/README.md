# Merge Intervals

A MirageScript rendition of the merge-intervals algorithmic classic.

## Problem sketch
Given a list of inclusive integer intervals, merge the overlapping ones and keep the result sorted by starting point.

## Runtime flow
- `garden` holds the original interval list and placeholders for a merged list plus a narrative.
- `prune_overlaps` directs `gpt-5-mini` to merge overlaps and store the canonical merged list.
- `narrate_pruning` captures a short human explanation and saves it inside `garden.narrative`.
- `show` logs the merged output, the story, and the final memory state.

## Expected transcript
Typical output from `uv run mirage examples/merge_intervals/merge_intervals.mirage --dump-state --arg intervals="[[1,3], [2,6], [8,10], [15,18]]"`:
```
input argument intervals [List<List<Int>>] = [[1,3], [2,6], [8,10], [15,18]]
remembered garden [IntervalGarden] = intervals: [[1,3], [2,6], [8,10], [15,18]]; merged: (empty); narrative: (none)
note: Time to clean up overlapping appointments.
ask prune_overlaps -> merged [Text] = [[1, 6], [8, 10], [15, 18]] — merged 1 overlap.
update garden = intervals: [[1,3], [2,6], [8,10], [15,18]]; merged: [[1, 6], [8, 10], [15, 18]]; narrative: (none)
ask narrate_pruning -> story [Text] = Sorted intervals then merged [1,3] with [2,6] to form [1,6]; the rest stayed separate at [8,10] and [15,18].
update garden = intervals: [[1,3], [2,6], [8,10], [15,18]]; merged: [[1, 6], [8, 10], [15, 18]]; narrative: Sorted intervals then merged [1,3] with [2,6] to form [1,6]; the rest stayed separate at [8,10] and [15,18].
show: merged [Text] = [[1, 6], [8, 10], [15, 18]] — merged 1 overlap.
show: story [Text] = Sorted intervals then merged [1,3] with [2,6] to form [1,6]; the rest stayed separate at [8,10] and [15,18].
show: garden [IntervalGarden] = intervals: [[1,3], [2,6], [8,10], [15,18]]; merged: [[1, 6], [8, 10], [15, 18]]; narrative: Sorted intervals then merged [1,3] with [2,6] to form [1,6]; the rest stayed separate at [8,10] and [15,18].
```
The model handles the merging logic while the interpreter tracks state.
