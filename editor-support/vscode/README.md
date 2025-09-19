# MirageScript VS Code Highlighting

This folder ships a lightweight VS Code extension that provides syntax highlighting for `.mirage` files.
Install it locally in a few minutes:

## 1. Copy or link the extension

a. Create a workspace extension directory (once):
```bash
mkdir -p ~/.vscode/extensions
```

b. Copy this folder there (or symlink so changes update automatically):
```bash
cp -R $(pwd)/editor-support/vscode ~/.vscode/extensions/miragescript-syntax
# or: ln -s $(pwd)/editor-support/vscode ~/.vscode/extensions/miragescript-syntax
```

> Rename `miragescript-syntax` however you like; VS Code only cares that each
> extension folder has a `package.json`.

## 2. Restart VS Code

Quit and reopen VS Code. You should now see highlighted MirageScript files.
If highlighting doesn’t appear immediately, run the **Developer: Reload Window** command.

The grammar recognises the full language, including `inputs:`, `argument`, `file`, `ask ... for`, and prompt blocks within `<<< >>>`.

## 3. Optional: Package with `vsce`

If you plan to share the extension, install [`vsce`](https://code.visualstudio.com/api/working-with-extensions/publishing-extension#vsce) and then:
```bash
cd editor-support/vscode
vsce package
```
This produces a `.vsix` file that others can install via **Extensions → … → Install from VSIX…**.

## Grammar highlights
- Keywords: `story`, `object`, `inputs`, `argument`, `file`, `helper`, `needs`, `prompt`, `begin`, `remember`, `ask`, `for`, `keep`, `show`, `note`, `with`, `returns`, `is`.
- Block prompts inside `<<< >>>` are treated as strings.
- Uppercase identifiers (e.g., `NumberPile`) render as types.
- `#` comments become grey.

Adjust the colors by editing `syntaxes/mirage.tmLanguage.json` or add snippets under a new `snippets/` folder.
