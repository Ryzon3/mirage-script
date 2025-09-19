# Sudoku Strategy Workshop

`sudoku_strategy_workshop.mirage` demonstrates how MirageScript can orchestrate a
multi-step Sudoku solving session. The program analyses a 9×9 puzzle, outlines a
strategy, documents key deductions, writes the solved grid to disk, and emits a
quality-assurance summary.

## Inputs
- `--arg puzzle_name` – Identifier for the puzzle (e.g., `Guardian-2024-04-08`).
- `--arg difficulty` – Difficulty label to set expectations (`Easy`, `Expert`, etc.).
- `--arg target_style` – Tone for explanations (`Educational`, `Succinct`, `Verbose`).
- `--arg output_stub` – Filename stem used when creating the solution file.
- `--file puzzle` – Path to a text file containing nine rows of digits, with `0`
  representing blanks.

The script saves the final grid and QA checklist to
`solutions/<stub>_<puzzle_name>_solution.txt` relative to the working directory.

## Example run
Solve the bundled puzzle and generate an explanation:

```bash
uv run mirage examples/sudoku_solver/sudoku_strategy_workshop.mirage \
  --arg puzzle_name=Guardian-2024-04-08 \
  --arg difficulty=Easy \
  --arg target_style=Educational \
  --arg output_stub=guardian_easy \
  --file puzzle=examples/sudoku_solver/sample_sudoku_easy.txt
```

## Sample artefacts
- Input puzzle: `sample_sudoku_easy.txt`
- Solved grid + QA report: `sample_outputs/guardian_easy_solution.txt`

Each run emits progress via `emit_output` (triggered by `show` statements) and writes
its final grid to the `solutions/` directory.
