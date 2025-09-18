# Maximum Value Finder

This MirageScript walkthrough solves the classic "find the maximum number" task while keeping state updates visible.

## Problem sketch
Pick out the largest number from a list while narrating the process in playful language.

## Runtime flow
- `remember` seeds the `pile` memory with a list description plus the current champion.
- `describe_numbers` asks `gpt-5-mini` to summarise the pile so a human sees the data.
- `pick_champion` instructs the model to choose the biggest number, update `pile.champion`, and celebrate.
- Three `show` commands display the story, the winning number, and the updated pile state.

## Expected behaviour
Running `uv run mirage examples/max_value_finder/max_value_finder.mirage --dump-state --arg numbers="[3, 14, 7, 28]"` prints a transcript similar to:
```
input argument numbers [List<Int>] = [3, 14, 7, 28]
remembered pile [NumberPile] = items: [3, 14, 7, 28]; champion: 0
remembered tag [Text] = Input numbers
ask describe_numbers -> story [Text] = Input numbers: 3, 14, 7, and 28.
ask pick_champion -> biggest [Int] = Hooray! The champion is 28.
update pile = items: [3, 14, 7, 28]; champion: 28
show: story [Text] = Input numbers: 3, 14, 7, and 28.
show: biggest [Int] = Hooray! The champion is 28.
show: pile [NumberPile] = items: [3, 14, 7, 28]; champion: 28
```
`gpt-5-mini` writes the details live; the final memory dump confirms the champion update.
