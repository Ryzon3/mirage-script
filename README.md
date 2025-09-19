# MirageScript Interpreter

MirageScript is a story-driven language where functions are prompts and `gpt-5-mini` performs the actual interpretation. The CLI now hands the full program file to the model and waits for tool calls that request inputs, read or write files, emit terminal output, or halt with an error. Python only brokers those tools — it no longer walks the script or mutates runtime state on its own.

## Highlights
- Lightweight MirageScript syntax (`remember`, `ask`, `show`, `note`) that reads like bedtime instructions.
- Function definitions contain prompts wrapped in `<<< >>>` so writers never touch real code.
- The model consumes the entire program text and drives execution through structured tool calls.
- Python stays in charge of side effects only: reading inputs, saving files, printing output, or surfacing errors on demand.
- Tool-calling contract exposes `emit_output`, `get_input`, `list_inputs`, `read_source`, `read_file`, `save_file`, and `raise_error` — everything else is up to the model.
- CLI `--arg` / `--file` flags advertise dynamic values that the model can pull with `get_input` when it needs them.

## Quick start
1. Ensure your `.env` file contains `OPENAI_API_KEY` (the CLI loads it automatically).
2. Install dependencies with [uv](https://github.com/astral-sh/uv):
   ```bash
   uv sync
   ```
3. Run a Mirage program (requires access to the OpenAI API):
   ```bash
   uv run mirage examples/max_value_finder/max_value_finder.mirage --arg numbers="[3, 14, 7, 28]"
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
Executing `examples/max_value_finder/max_value_finder.mirage --arg numbers="[3, 14, 7, 28]"` now produces whatever narration and bookkeeping the model decides to emit via `emit_output`. Expect the exact lines (and their ordering) to vary between runs because `gpt-5-mini` is in full control of the runtime.
