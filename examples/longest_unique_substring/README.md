# Longest Unique Substring

Sliding-window reasoning, but with bedtime storytelling. This MirageScript example asks the model to find the longest substring without repeating characters.

## Flow overview
- `remember report` sets up a narrative placeholder for the current best window.
- The helper prompt walks `gpt-5-mini` through a sliding-window strategy and asks for a summary.
- `show` ensures the final explanation reaches the terminal via `emit_output`.

## Running the demo
```
uv run mirage examples/longest_unique_substring/longest_unique_substring.mirage --arg text=pwwkew
```
You should see a short adventure describing how the window expands and contracts, concluding with the winning substring. The precise sentences change per run, but the core facts—characters examined, window length, final answer—remain.

Add stricter wording inside the helper prompt if you want bullet lists or JSON output instead of free-form prose.
