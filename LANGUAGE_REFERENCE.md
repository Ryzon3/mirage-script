# MirageScript Language Reference

This document collects the entire MirageScript surface area: file structure, syntax, and runtime behaviour.

## File overview

A MirageScript file ends with `.mirage` and follows this high-level structure:

```
story "Program title"

object ... definitions
inputs: ... (optional)
helper ... definitions

begin:
  ...steps...
```

Comments start with `#` and blank lines are ignored.

## Objects

Objects describe reusable records of data that the LLM can reason about. Each field line explains the name, type, and optional description.

```
object NumberPile:
  has items (List<Int>) meaning "numbers waiting their turn"
  has champion (Int) meaning "current best number"
```

Field descriptions are purely informational; the interpreter does not enforce them but includes them in prompts.

## Inputs

Use an `inputs:` block to declare data the script expects at runtime. Every entry populates a memory before the `begin:` block runs.

```
inputs:
  argument numbers as List<Int> with "Numbers to examine"
  file dataset as Text with "Raw dataset contents"
```

- `argument` values are supplied via `--arg name=value`. The value is stored verbatim.
- `file` values come from `--file name=PATH`; the interpreter reads the file as UTF-8 and stores the contents.
- Inside `remember` descriptions you can interpolate values with `{name}` to copy them into richer strings.

## Helpers & prompts

Helpers declare typed parameters plus a return type. The helper body is a prompt enclosed by `<<< >>>`; it instructs the LLM what to do.

```
helper pick_champion returns Int:
  needs pile (NumberPile)
  prompt:
<<<
Look through pile.items, decide which number is greatest, and call emit_response with:
- return: joyful sentence naming the integer winner
- updates: set pile.champion appropriately
- notes: any extra remarks
>>>
```

## Begin block commands

The `begin:` section lists executable steps. Supported commands:

- `remember name as Type with "description"`
  * Creates or updates a memory. The description may include `{other_memory}` placeholders.
- `ask helper_name for:` ... `keep answer as result`
  * Calls a helper. Each argument line uses `name is <value>` where `<value>` can be `memory X`, a quoted literal, or a plain word treated as a literal.
- `show [memory] name`
  * Prints the memory contents. `show memory name` is optional; the keyword `memory` is ignored.
- `note "text"`
  * Emits a narrator note in the output log.

Example anatomy:

```
begin:
  remember quest as NumberQuest with "numbers: {numbers}; target: {target}; match: (unknown)"
  note "Identify the first pair of indices that reach the target sum."
  ask find_pair for:
    quest is memory quest
  keep answer as summary
  show summary
```

## Tool contract

The interpreter enforces a single completion tool: `emit_response`. Helpers must call it exactly once with this JSON shape:

```
{
  "return": {
    "type": "Optional type name",
    "value": "Description of the return value",
    "summary": "Short optional remark"
  },
  "updates": [
    {"target": "memory", "type": "Optional type", "value": "New description", "summary": "Why it changed"}
  ],
  "notes": ["Optional remarks echoed to the user"]
}
```

The interpreter halts if parsing fails or the tool is missing.

## Runtime log

During execution the CLI prints a transcript:

- `input argument name [Type] = ...` lines for each declared input.
- `remembered ...` for `remember` statements.
- `ask helper -> result [...] = ...` plus optional `update ...` and `assistant note ...` entries from the helper response.
- `show: ...` for display commands.
- `note: ...` for narrator notes.

Use `--dump-state` to append a final memory snapshot.

## Example: Maximum Value Finder

```
story "Maximum Value Finder"

object NumberPile:
  has items (List<Int>) meaning "numbers waiting their turn"
  has champion (Int) meaning "current best number"

inputs:
  argument numbers as List<Int> with "Numbers to inspect"

helper pick_champion returns Int:
  needs pile (NumberPile)
  prompt:
<<<
Look through pile.items, decide which number is greatest, and call emit_response with:
- return: a sentence naming the winner
- updates: set pile.champion accordingly
- notes: any short celebration
>>>

helper describe_numbers returns Text:
  needs label (Text)
  needs numbers (List<Int>)
  prompt:
<<<
Describe the list in under 25 words.
>>>

begin:
  remember pile as NumberPile with "items: {numbers}; champion: 0"
  remember tag as Text with "Input numbers"
  ask describe_numbers for:
    label is memory tag
    numbers is memory numbers
  keep answer as overview
  ask pick_champion for:
    pile is memory pile
  keep answer as winner
  show overview
  show winner
  show pile
```

Run it with:
```
uv run mirage examples/max_value_finder/max_value_finder.mirage --arg numbers="[3, 14, 7, 28]"
```

## CLI recap

- `uv run mirage program.mirage --arg name=value --file dataset=path --dump-state`
- Missing required inputs produce explicit errors.
- Files are read as UTF-8 strings and stored directly; add parsing logic in helpers if needed.

That’s the complete language surface—mix and match helpers, inputs, and memories to orchestrate LLM-driven solutions.
