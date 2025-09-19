# MirageScript Interpreter

MirageScript is a prompt-oriented language where functions are instructions and `gpt-5-mini` performs the actual interpretation. The CLI hands the full program file to the model and waits for tool calls that request inputs, read or write files, emit terminal output, or halt with an error. Python only brokers those tools — it no longer walks the script or mutates runtime state on its own.

## Highlights
- Lightweight MirageScript syntax (`remember`, `ask`, `show`, `note`) that emphasizes consistent imperative phrasing.
- Function definitions contain prompts wrapped in `<<< >>>` so authors can focus on clear instructions instead of Python code.
- Keyword-driven declarations (`argument name as Type with`, `note with`, `ask helper for:`) keep scripts uniform and easy to read.
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
> Add `--debug-log transcript.jsonl` to capture the full LLM conversation for later inspection.

## Docs & language guide
- `LANGUAGE_REFERENCE.md` documents the full MirageScript syntax, inputs, and runtime contract.
- `QUICKSTART.md` shows two short programs you can copy, run, and adjust.

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
- `examples/add_two_numbers/` — Linked-list addition with explicit carry handling.
- `examples/longest_unique_substring/` — Sliding-window unique substring search.
- `examples/valid_parentheses/` — Stack-based bracket validator.
- `examples/merge_intervals/` — Merging overlapping intervals.
- `examples/universal_translator/` — Multi-stage translation pipeline that writes results to disk.
- `examples/sudoku_solver/` — Sudoku puzzle analysis, solving, and QA workflow.

Each subfolder contains a `.mirage` file and a markdown explainer.

## Example transcript
Executing `examples/max_value_finder/max_value_finder.mirage --arg numbers="[3, 14, 7, 28]"` produces the natural-language output and bookkeeping the model chooses to emit via `emit_output`. Expect the exact lines (and their ordering) to vary between runs because `gpt-5-mini` controls the runtime.
