# MirageScript Quickstart

Welcome! This quick tour shows how to write and run MirageScript files using the new, story-like syntax.

## 1. Hello Mirage (no helpers required)
Create `hello.mirage` with the following contents:

```
story "Hello Mirage"

begin:
  remember greeting as Text with "Hello from MirageScript!"
  note "Let’s share what we remembered."
  show greeting
```

Run it:
```bash
uv run mirage hello.mirage --dump-state
```
You should see the note, the greeting, and the final memory snapshot.

## 2. Friendly Greeter (using a helper)
Save this as `friendly_greeter.mirage` next to the first program:

```
story "Friendly Greeter"

object Friend:
  has name (Text) meaning "a friendly name"

helper compose_greeting returns Text:
  needs friend (Friend)
  prompt:
<<<
Say hello to friend.name using a cheerful, single-sentence message.
Mention their name and a short compliment.
Call emit_response with the sentence and leave other memories unchanged.
>>>

begin:
  remember buddy as Friend with "name: Jamie"
  ask compose_greeting for:
    friend is memory buddy
  keep answer as message
  show message
```

Execute it:
```bash
uv run mirage friendly_greeter.mirage --dump-state
```
The helper will ask `gpt-5-mini` to craft the greeting and store it in `message`.
## 3. Reading inputs at runtime
To solve algo-style problems you can declare inputs and pass them on the command line.

Create `two_sum_quickstart.mirage`:

```
story "Two Sum Quickstart"

object NumberQuest:
  has numbers (List<Int>) meaning "candidate values"
  has target (Int) meaning "desired sum"
  has match (Pair<Int>) meaning "solution indices"

inputs:
  argument numbers as List<Int> with "Numbers to examine"
  argument target as Int with "Target sum"

helper find_pair returns Text:
  needs quest (NumberQuest)
  prompt:
<<<
Find two indices whose values add up to quest.target. Choose the first valid pair in ascending order.
Call emit_response with the pair and update quest.match to remember it.
>>>

begin:
  remember quest as NumberQuest with "numbers: {numbers}; target: {target}; match: (unknown)"
  ask find_pair for:
    quest is memory quest
  keep answer as summary
  show summary
  show quest
```

Run it with arguments:
```bash
uv run mirage two_sum_quickstart.mirage --arg numbers="[2, 7, 11, 15]" --arg target=9
```

The interpreter seeds the `numbers` and `target` memories before running the rest of the script, letting the helper operate on dynamic inputs.
## 4. Reading file inputs
Inputs can also pull data from files. Create `dataset_input.mirage` alongside a text file:

```
story "Sum From File"

inputs:
  file dataset as Text with "Numbers separated by spaces"

helper compute_sum returns Text:
  needs dataset (Text)
  prompt:
<<<
Split dataset into integers separated by spaces. Compute their total and call emit_response with:
- return: sentence stating the sum
- updates: []
- notes: optional reminder about the data
>>>

begin:
  ask compute_sum for:
    dataset is memory dataset
  keep answer as summary
  show summary
  show dataset
```

Create a sample file:
```bash
printf "4 9 15 6" > numbers.txt
```

Run with the file input:
```bash
uv run mirage dataset_input.mirage --dump-state --file dataset=numbers.txt
```

The interpreter reads `numbers.txt`, stores its contents in the `dataset` memory, and feeds it to the helper.

## 5. Tips
- Keep literal text inside quotes; use `memory name` when you want to pass an existing memory.
- Prompts can be playful—tell the model exactly what tone or structure you want.
- `--dump-state` is handy while experimenting; remove it when you just want the log.
- Supply declared inputs with `--arg name=value` and `--file name=path` (file contents load as strings).

Ready for more? Explore the LeetCode-flavoured examples inside `examples/` or skim `LANGUAGE_REFERENCE.md` for the full language guide.
