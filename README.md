# MirageScript Interpreter

MirageScript is a story-driven language where functions are prompts and `gpt-5-mini` hallucinates the runtime. The interpreter keeps a mutable memory table, forwards context to the model, and applies any updates described in the JSON reply.

## Highlights
- Lightweight MirageScript syntax (`remember`, `ask`, `show`, `note`) that reads like bedtime instructions.
- Function definitions contain prompts wrapped in `<<< >>>` so writers never touch real code.
- Runtime state persists between calls; the model can mutate memories through structured JSON updates.
- Pure Python implementation that only relies on the OpenAI HTTP endpoint.
- Tool-calling contract forces `gpt-5-mini` to yield well-formed results via the `emit_response` function.
- Declarative `inputs:` block plus `--arg` / `--file` flags feed dynamic values into memories before execution.

## Quick start
1. Ensure your `.env` file contains `OPENAI_API_KEY` (the CLI loads it automatically).
2. Install dependencies with [uv](https://github.com/astral-sh/uv):
   ```bash
   uv sync
   ```
3. Run a Mirage program (requires access to the OpenAI API):
   ```bash
   uv run mirage examples/max_value_finder/max_value_finder.mirage --dump-state --arg numbers="[3, 14, 7, 28]"
   ```

> Supply runtime values with `--arg name=value` (and `--file name=path` for file-based inputs).

## Docs & language guide
- `LANGUAGE_REFERENCE.md` documents the full MirageScript syntax, inputs, and runtime contract.
- `QUICKSTART.md` shows two tiny programs you can copy, run, and tweak.

## Testing
Run unit tests:
```bash
uv run python -m unittest discover -s tests
```

## Linting
MirageScript targets Ruff for linting:
```bash
uvx --from ruff ruff check
```
If Ruff is not pre-installed, the command will try to download it from PyPI.

## Example gallery
- `examples/max_value_finder/` — Maximum element selection with state updates.
- `examples/two_sum/` — Classic Two Sum helper workflow.
- `examples/add_two_numbers/` — Linked-list addition with carry narration.
- `examples/longest_unique_substring/` — Sliding-window unique substring search.
- `examples/valid_parentheses/` — Stack-based bracket validator.
- `examples/merge_intervals/` — Merging overlapping intervals.

Each subfolder contains a `.mirage` file and a markdown explainer.

## Example transcript
Executing `examples/max_value_finder/max_value_finder.mirage --arg numbers="[3, 14, 7, 28]"` prints:
```
input argument numbers [List<Int>] = [3, 14, 7, 28]
remembered pile [NumberPile] = items: [3, 14, 7, 28]; champion: 0
remembered tag [Text] = Input numbers
ask describe_numbers -> story [Text] = ...
ask pick_champion -> biggest [Int] = ...
show: story [Text] = ...
show: biggest [Int] = ...
show: pile [NumberPile] = ...
```
Each `...` is invented by `gpt-5-mini` at temperature 1.0.
