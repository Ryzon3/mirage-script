# Longest Substring Without Repeating Characters

MirageScript tackles the sliding-window classic from LeetCode.

## Problem sketch
Given a string, determine the length of the longest substring that contains no repeated characters, and provide one such substring.

## Runtime flow
- `mystery` holds the input string plus placeholders for the answer and the reasoning.
- `find_longest_unique` asks `gpt-5-mini` to simulate the sliding-window scan, update `mystery.length` and `mystery.snippet`, and announce the result.
- `explain_window` records how the window moved and stores the narrative in `mystery.reasoning`.
- `show` prints the headline, the explanation, and the final memory snapshot.

## Expected transcript
Sample run via `uv run mirage examples/longest_unique_substring/longest_unique_substring.mirage --dump-state --arg text=pwwkew`:
```
input argument text [Text] = pwwkew
remembered mystery [SubstringCase] = text: pwwkew; length: 0; snippet: (none); reasoning: (none)
ask find_longest_unique -> headline [Text] = Longest unique substring has length 3: "wke".
update mystery = text: pwwkew; length: 3; snippet: wke; reasoning: (none)
ask explain_window -> detail [Text] = Sweep the window across pwwkew: start with p, drop the first w when a duplicate appears, expand to wke for length 3 before another duplicate forces a shift.
update mystery = text: pwwkew; length: 3; snippet: wke; reasoning: Sweep the window across pwwkew: start with p, drop the first w when a duplicate appears, expand to wke for length 3 before another duplicate forces a shift.
show: headline [Text] = Longest unique substring has length 3: "wke".
show: detail [Text] = Sweep the window across pwwkew: start with p, drop the first w when a duplicate appears, expand to wke for length 3 before another duplicate forces a shift.
show: mystery [SubstringCase] = text: pwwkew; length: 3; snippet: wke; reasoning: Sweep the window across pwwkew: start with p, drop the first w when a duplicate appears, expand to wke for length 3 before another duplicate forces a shift.
```
Expect small phrasing changes, but the algorithmic idea stays true.
