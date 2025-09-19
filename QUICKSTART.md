# MirageScript Quickstart

The Mirage CLI now hands your entire `.mirage` file to `gpt-5-mini`, then steps aside. The model interprets every instruction, calls the available tools, and writes the terminal output via `emit_output`. This quick tour highlights a few scripts that work well with the LLM interpreter.

## 1. Hello Mirage
Create `hello.mirage` with a minimal script:

```
story "Hello Mirage"

begin:
  note with "Introduce the project."
  show greeting
```

Add a comment near the top (optional) reminding the model what the verbs mean:

```
# Interpret `note with` as an explanatory aside.
# Treat `show X` as: emit the stored value X exactly once via emit_output.
```

Run it:
```bash
uv run mirage hello.mirage
```
Expect one or two lines describing the greeting; the wording varies every run.

## 2. Friendly Greeter (helper prompt)
`gpt-5-mini` reads helper prompts too, so you can store reusable instructions inside them.

```
story "Friendly Greeter"

object Friend:
  has name (Text) meaning "a person's name"

helper compose_greeting returns Text:
  needs friend (Friend) meaning "person receiving the greeting"
  prompt:
<<<
Compose a one-sentence hello for friend.name. Return the greeting so the show step can emit it.
>>>

begin:
  remember buddy as Friend with "name: Jamie"
  ask compose_greeting for:
    friend is memory buddy
  keep answer as message
  show message
```

Run:
```bash
uv run mirage friendly_greeter.mirage
```
You should see a greeting for Jamie; the helper returns the text and the `show` line emits it.

## 3. Reading CLI arguments on demand
Describe arguments in the `inputs:` block and fetch them with `get_input` when needed.

```
story "Two Sum Quickstart"

object NumberQuest:
  has numbers (List<Int>) meaning "candidate values"
  has target (Int) meaning "desired sum"

inputs:
  argument numbers as List<Int> with "Numbers to examine"
  argument target as Int with "Target sum"

helper find_pair returns Text:
  needs quest (NumberQuest) meaning "input numbers, target, and match placeholder"
  prompt:
<<<
Find two indices whose values add to quest.target. Return the pair and a short explanation; the show step will emit it.
>>>

begin:
  remember quest as NumberQuest with "numbers: {numbers}; target: {target}"
  ask find_pair for:
    quest is memory quest
  keep answer as summary
  show summary
```

Run it:
```bash
uv run mirage two_sum_quickstart.mirage --arg numbers="[2, 7, 11, 15]" --arg target=9
```
The model will call `get_input` for `numbers` and `target`, reason about them, and describe a solution.

## 4. Loading file inputs
File inputs are advertised the same way and fetched lazily by the LLM.

```
story "Sum From File"

inputs:
  file dataset as Text with "Numbers separated by spaces"

helper compute_sum returns Text:
  needs dataset (Text) meaning "numbers read from the dataset file"
  prompt:
<<<
Split dataset into integers separated by spaces. Return a sentence reporting their sum; the show step will emit it.
>>>

begin:
  note with "Add the values contained in the dataset file."
  ask compute_sum for:
    dataset is file dataset
  keep answer as summary
  show summary
```

Create a sample file and run it:
```bash
printf "4 9 15 6" > numbers.txt
uv run mirage dataset_input.mirage --file dataset=numbers.txt
```
The helper will request the file contents and produce a concise total.
The binding uses `dataset is file dataset` to make the source explicit; use `argument <name>` for CLI arguments.

## Tips
- Annotate scripts with short comments explaining how to treat each verb; the model reads them verbatim.
- Keep helper prompts clear about which values should be returned so that `show` can emit them without duplication.
- Inputs are on-demand; if the program never calls `get_input`, the CLI never reads the file or argument.
- Outputs differ between runs. If you need deterministic data, instruct the helper to stick to a strict format.
- When binding CLI data inside `ask`, prefer `argument name` for `--arg` values and `file name` for `--file` values so the source is explicit.

For additional material, explore the example programs in `examples/` or review `LANGUAGE_REFERENCE.md` for a deeper discussion of the tool contract.
