# Two Sum — Index Pair Finder

This MirageScript scenario mirrors the classic Two Sum interview problem.

## Problem sketch
Given a list of numbers and a target sum, find two distinct indices whose values add to the target.

## Runtime flow
- `quest` stores the numbers, target, and an "unknown" slot for the matching indices.
- `pick_pair` instructs `gpt-5-mini` to find a valid pair, describe it, and update `quest.match`.
- `verify_pair` double-checks that the proposed pair really reaches the target.
- `show` statements print the chosen pair, the verification blurb, and the updated quest memory.

## Expected transcript
When you run `uv run mirage examples/two_sum/two_sum.mirage --dump-state --arg numbers="[2, 7, 11, 15]" --arg target=9`, a typical output looks like:
```
input argument numbers [List<Int>] = [2, 7, 11, 15]
input argument target [Int] = 9
remembered quest [NumberQuest] = numbers: [2, 7, 11, 15]; target: 9; match: (unknown)
note: Identify the first pair of indices that reach the target sum.
ask pick_pair -> answer [Text] = Indices 0 and 1 (2 + 7) reach 9.
update quest = numbers: [2, 7, 11, 15]; target: 9; match: (0, 1)
ask verify_pair -> proof [Text] = Check passed: 2 + 7 hits the target 9.
show: answer [Text] = Indices 0 and 1 (2 + 7) reach 9.
show: proof [Text] = Check passed: 2 + 7 hits the target 9.
show: quest [NumberQuest] = numbers: [2, 7, 11, 15]; target: 9; match: (0, 1)
```
Because the interpreter uses live completions, phrasing varies, but the logic stays on target.
