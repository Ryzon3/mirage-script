# MirageScript Quickstart

The Mirage CLI now hands your entire `.mirage` file to `gpt-5-mini`, then steps aside. The model interprets every instruction, calls the available tools, and writes the terminal output via `emit_output`. This quick tour shows a few scripts that play nicely with the LLM interpreter.

## 1. Hello Mirage
Create `hello.mirage` with a short story:

```
story "Hello Mirage"

begin:
  note "Introduce the project."
  show greeting
```

Add a comment near the top (optional) reminding the model what the verbs mean:

```
# Interpret `note` as a narrator aside. Use emit_output to share it.
# Interpret `show X` as printing a memory or idea named X.
```

Run it:
```bash
uv run mirage hello.mirage
```
Expect a couple of lines describing the greeting—exact wording varies every run.

## 2. Friendly Greeter (helper prompt)
`gpt-5-mini` reads helper prompts too, so you can stash reusable instructions inside them.

```
story "Friendly Greeter"

object Friend:
  has name (Text) meaning "a friendly name"

helper compose_greeting returns Text:
  needs friend (Friend)
  prompt:
<<<
Compose a one-sentence hello for friend.name. Call emit_output with the final line.
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
You should see a cheerful greeting for Jamie. The helper prompt nudges the model to call `emit_output` before finishing.

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
  needs quest (NumberQuest)
  prompt:
<<<
Find two indices whose values add to quest.target. When you have them, call emit_output with the pair and a short explanation.
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
The model will call `get_input` for `numbers` and `target`, reason about them, and narrate a solution.

## 4. Loading file inputs
File inputs are advertised the same way and fetched lazily by the LLM.

```
story "Sum From File"

inputs:
  file dataset as Text with "Numbers separated by spaces"

helper compute_sum returns Text:
  needs dataset (Text)
  prompt:
<<<
Split dataset into integers separated by spaces. Report their sum through emit_output.
>>>

begin:
  note "Add the values contained in the dataset file."
  ask compute_sum for:
    dataset is memory dataset
  keep answer as summary
  show summary
```

Create a sample file and run it:
```bash
printf "4 9 15 6" > numbers.txt
uv run mirage dataset_input.mirage --file dataset=numbers.txt
```
The helper will request the file contents and produce a narrated total.

## Tips
- Annotate scripts with short comments explaining how to treat each verb; the model reads them verbatim.
- Keep helper prompts explicit about when to call `emit_output`, especially if you expect multiple lines of output.
- Inputs are on-demand; if the program never calls `get_input`, the CLI never reads the file or argument.
- Outputs differ between runs. If you need deterministic data, instruct the helper to stick to a strict format.

Ready for more? Explore the example programs in `examples/` or skim `LANGUAGE_REFERENCE.md` for a deeper discussion of the tool contract.
