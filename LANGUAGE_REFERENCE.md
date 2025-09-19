# MirageScript Language Notes

MirageScript programs are text-based scripts that **the language model** interprets directly. The CLI delivers the entire `.mirage` file (plus any inputs you advertise on the command line) to `gpt-5-mini`, and the model decides how to execute each instruction. Python only provides a handful of tools for reading inputs, printing output, and touching the filesystem.

Because there is no longer a Python-side parser or scheduler, the language surface below should be treated as guidance for how to write programs the model understands. The closer you stay to these patterns, the easier it is for the LLM interpreter to follow along.

## Recommended file layout

```
story "Program title"

object ... definitions (optional)
inputs: ... (optional)
helper ... definitions (optional)

begin:
  ...program steps...
```

Blank lines and `#` comments remain useful for organization and in-line hints; the model sees them exactly as written.

## Core declarations

Every section uses explicit keywords to keep the structure predictable:

- `story "Title"` declares the program name.
- `object TypeName:` introduces a reusable record shape. Each property line follows `has field_name (Type) meaning "Description"`.
- `inputs:` lists dynamic values. Use one line per input in the form `argument name as Type with "Description"` or `file name as Type with "Description"`.
- `helper helper_name returns Type:` defines a helper. List its dependencies with `needs parameter (Type) meaning "Description"` (the `meaning` clause is optional but recommended) and provide the prompt inside `<<< >>>`.
- `begin:` starts the instruction sequence for the program body.

## Statement keywords

Within the `begin` block, keep statements keyword-driven:

- `remember label as Type with "key: value; ..."` stores structured context.
- `note with "Message."` documents intent or intermediate reasoning.
- `ask helper_name for:` introduces a call. Indent bindings using `parameter is memory saved_label`, `parameter is argument cli_name`, or `parameter is file cli_name`.
- `keep answer as label` names the most recent helper response.
- `show label` or `show memory label` requests a visible output (the helper should call `emit_output`).
- `raise error with "Message."` is a conventional phrasing the model can convert into a `raise_error` tool call if needed.

### Objects

Declare shared data shapes:

```
object NumberPile:
  has items (List<Int>) meaning "numbers pending evaluation"
  has champion (Int) meaning "current best number"
```

These sections are descriptive scaffolding. They help the model keep track of the relevant fields when reasoning about memories or helper prompts.

### Inputs

```
inputs:
  argument numbers as List<Int> with "Numbers to examine"
  file dataset as Text with "Raw dataset contents"
```

- `argument` values are supplied with `--arg name=value`.
- `file` values are supplied with `--file name=PATH`; the CLI reads the file as UTF-8 when the model asks for it.

Nothing is seeded automatically anymore. The model calls `get_input` (see tools below) whenever it wants the text for one of these names.

When you pass inputs into helpers, reference them explicitly:

```
ask compute_sum for:
  dataset is file dataset
  threshold is argument limit
```

### Helpers

Helpers bundle prompts that the LLM can call while “running” the program. Describe each dependency with `needs parameter (Type) meaning "Description"` so the model knows what data it receives:

```
helper pick_champion returns Int:
  needs pile (NumberPile) meaning "candidate numbers and current champion"
  prompt:
<<<
Look through pile.items, decide which number is greatest, and provide a concise summary of the decision.
>>>
```

Prompts can be as structured or conversational as you need. Because *the same model* reads the script and executes it, treat helper bodies as reusable sub-instructions rather than remote calls.

### Begin block

Continue writing steps in the imperative syntax the previous interpreter supported. Lead each instruction with its keyword (`remember`, `note with`, `ask`, `keep answer as`, `show`) so the model can quickly match the pattern. Consistent phrasing improves reliability.

```
begin:
  remember pile as NumberPile with "items: {numbers}; champion: 0"
  note with "Identify the largest number."
  ask pick_champion for:
    pile is memory pile
  keep answer as champion_summary
  show champion_summary
```

## Tool interface

The only way the model can affect the outside world is by calling the tools exposed by the CLI. Each tool expects a JSON object as its argument payload. The interpreter validates inputs and raises `MirageRuntimeError` if the payload is malformed.

| Tool name    | Purpose | Payload fields |
|--------------|---------|----------------|
| `emit_output` | Append a line to the terminal transcript. | `{ "text": "..." }` |
| `list_inputs` | Discover the names of declared argument/file inputs. | `{}` |
| `get_input`   | Fetch the value of an input. `argument` returns the raw CLI string; `file` reads the file contents. | `{ "name": "numbers", "kind": "argument" }` |
| `read_source` | Retrieve the entire `.mirage` source again. | `{}` |
| `read_file`   | Read a UTF-8 text file relative to the program directory. | `{ "path": "notes/output.txt" }` → returns `{ "available": true/false, ... }` |
| `save_file`   | Write UTF-8 content to a file (parents are created automatically). | `{ "path": "notes/output.txt", "content": "..." }` |
| `raise_error` | Abort execution and surface a message to the user. | `{ "message": "Something went wrong" }` |

Every user-facing line **must** flow through `emit_output`; returning plain assistant text ends the session and prints the final message verbatim. When calling `get_input`, include the `kind` field to avoid ambiguity between arguments and files.

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
  has items (List<Int>) meaning "numbers pending evaluation"
  has champion (Int) meaning "current best number"

inputs:
  argument numbers as List<Int> with "Numbers to inspect"

helper pick_champion returns Int:
  needs pile (NumberPile) meaning "candidate numbers and current champion"
  prompt:
<<<
Inspect pile.items, choose the largest value, and explain the result in one or two sentences.
>>>

begin:
  remember pile as NumberPile with "items: {numbers}; champion: 0"
  note with "Identify the largest integer."
  ask pick_champion for:
    pile is memory pile
  keep answer as summary
  show summary
```

Run it with:

```
uv run mirage examples/max_value_finder/max_value_finder.mirage --arg numbers="[3, 14, 7, 28]"
```

Expect varied natural-language output — not deterministic transcripts — because `gpt-5-mini` now improvises each run while relying on the listed tools.
