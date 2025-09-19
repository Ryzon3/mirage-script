# MirageScript Language Notes

MirageScript programs are storytelling scripts that **the language model** now interprets directly. The CLI simply delivers the entire `.mirage` file (plus any inputs you advertise on the command line) to `gpt-5-mini`, and the model decides how to execute each instruction. Python only provides a handful of tools for reading inputs, printing output, and touching the filesystem.

Because there is no longer a Python-side parser or scheduler, the language surface below should be treated as guidance for how to write stories the model understands. The closer you stay to these patterns, the easier it is for the LLM interpreter to follow along.

## Recommended file layout

```
story "Program title"

object ... definitions (optional)
inputs: ... (optional)
helper ... definitions (optional)

begin:
  ...story steps...
```

Blank lines and `#` comments remain useful for breathing room and hints; the model sees them exactly as written.

### Objects

Declare shared data shapes:

```
object NumberPile:
  has items (List<Int>) meaning "numbers waiting their turn"
  has champion (Int) meaning "current best number"
```

These sections are purely descriptive. They help the LLM remember key fields when reasoning about memories or helper prompts.

### Inputs

```
inputs:
  argument numbers as List<Int> with "Numbers to examine"
  file dataset as Text with "Raw dataset contents"
```

- `argument` values are supplied with `--arg name=value`.
- `file` values are supplied with `--file name=PATH`; the CLI reads the file as UTF-8 when the model asks for it.

Nothing is seeded automatically anymore. The model calls `get_input` (see tools below) whenever it wants the text for one of these names.

### Helpers

Helpers bundle prompts that the LLM can call out to while “running” the story:

```
helper pick_champion returns Int:
  needs pile (NumberPile)
  prompt:
<<<
Look through pile.items, decide which number is greatest, and narrate the result.
>>>
```

Prompts can be as structured or whimsical as you like. Remember that *the same model* both reads the script and executes it, so helper bodies are more like reusable sub-instructions than remote calls.

### Begin block

Continue writing steps in the bedtime-syntax the previous interpreter supported. The model expects to see verbs such as `remember`, `ask`, `show`, and `note`, but it is free to interpret them however it likes. The more consistently you phrase steps, the more reliable the results become.

```
begin:
  remember pile as NumberPile with "items: {numbers}; champion: 0"
  note "Identify the largest number."
  ask pick_champion for:
    pile is memory pile
  keep answer as champion_story
  show champion_story
```

## Tool interface

The only way the model can affect the outside world is by calling the tools exposed by the CLI. Each tool expects a JSON object as its argument payload. The interpreter validates inputs and raises `MirageRuntimeError` if the payload is malformed.

| Tool name    | Purpose | Payload fields |
|--------------|---------|----------------|
| `emit_output` | Append a line to the terminal transcript. | `{ "text": "..." }` |
| `list_inputs` | Discover the names of declared argument/file inputs. | `{}` |
| `get_input`   | Fetch the value of an input. `argument` returns the raw CLI string; `file` reads the file contents. | `{ "name": "numbers", "kind": "argument"? }` |
| `read_source` | Retrieve the entire `.mirage` source again. | `{}` |
| `read_file`   | Read a UTF-8 text file relative to the program directory. | `{ "path": "notes/output.txt" }` → returns `{ "available": true/false, ... }` |
| `save_file`   | Write UTF-8 content to a file (parents are created automatically). | `{ "path": "notes/output.txt", "content": "..." }` |
| `raise_error` | Abort execution and surface a message to the user. | `{ "message": "Something went wrong" }` |

Every user-facing line **must** flow through `emit_output`; returning plain assistant text ends the session and prints the final message verbatim.

`read_file` always returns whether the file was available; if `available` is `False`, the payload also carries an `error` string so the model can decide how to proceed.

## Execution flow

1. `uv run mirage script.mirage [--arg name=value] [--file name=path]`
2. The CLI loads optional `.env`, reads the script, and constructs the opening conversation: a system message describing the contract and a user message that includes the program text and advertised input names.
3. The model drives execution by issuing tool calls. Each tool response is fed back as a tool message.
4. When the model no longer calls tools, whatever text remains in the last assistant message is echoed to the terminal (after any prior `emit_output` lines).

Errors can surface in three ways:
- The CLI detects invalid CLI flags or missing files.
- The model calls `raise_error`.
- A tool rejects a malformed payload (for example, wrong types or unreadable files).

## Worked example

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
Inspect pile.items, choose the largest value, and celebrate the winner. Produce a short story.
>>>

begin:
  remember pile as NumberPile with "items: {numbers}; champion: 0"
  note "Find the mightiest integer."
  ask pick_champion for:
    pile is memory pile
  keep answer as celebration
  show celebration
```

Run it with:

```
uv run mirage examples/max_value_finder/max_value_finder.mirage --arg numbers="[3, 14, 7, 28]"
```

Expect playful text – not deterministic transcripts – because `gpt-5-mini` now improvises each run while relying on the listed tools.
