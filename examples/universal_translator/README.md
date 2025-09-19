# Polyglot Translation Workshop

`polyglot_translator.mirage` orchestrates a multi-step translation workflow that:
- inspects the input document to classify its domain and risks,
- builds a plan tailored to the requested tone and target language,
- produces a translation (for natural language or code) and runs quality checks,
- persists the result to a deterministic file inside a `translations/` directory, and
- reports its actions through structured helper calls.

## Inputs
- `--arg source_language` – Source language label (e.g., `English`, `Python`).
- `--arg target_language` – Target language label (e.g., `Spanish`, `TypeScript`).
- `--arg tone` – Desired tone (`Formal`, `Conversational`, `Production-ready`, etc.).
- `--arg output_stub` – Filename stem used for the output (no extension).
- `--file document` – Path to the file that contains the text or code to translate.

The program creates `translations/<stub>_<source>_to_<target>.txt` relative to the working directory.

## Example runs
Translate the sample press release from English to Spanish:
```bash
uv run mirage examples/universal_translator/polyglot_translator.mirage \
  --arg source_language=English \
  --arg target_language=Spanish \
  --arg tone=Formal \
  --arg output_stub=press_release \
  --file document=examples/universal_translator/sample_press_release.txt
```

Translate a Python analytics helper into TypeScript:
```bash
uv run mirage examples/universal_translator/polyglot_translator.mirage \
  --arg source_language=Python \
  --arg target_language=TypeScript \
  --arg tone="Production-ready" \
  --arg output_stub=analytics_helper \
  --file document=examples/universal_translator/sample_python_snippet.py
```

## Sample artefacts
The `sample_outputs/` directory contains translations produced from the bundled inputs to illustrate the expected format. Each run also emits a checklist (`run_quality_gate`) and summary (`produce_summary`) through `emit_output`.

- `sample_press_release.txt` → `sample_outputs/press_release_english_to_spanish.txt`
- `sample_python_snippet.py` → `sample_outputs/analytics_helper_python_to_typescript.txt`

You can delete and regenerate these outputs by running the commands above; the program will write fresh files under `translations/`.
