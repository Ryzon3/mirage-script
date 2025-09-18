"""Command-line interface for the MirageScript interpreter."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Dict

from .interpreter import MirageInterpreter, MirageRuntimeError
from .llm_client import OpenAIClient, OpenAIError
from .parser import MirageParseError, parse_program


def load_env_file(env_path: Path) -> None:
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = [piece.strip() for piece in stripped.split("=", 1)]
        if key and value and key not in os.environ:
            os.environ[key] = value


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run MirageScript programs")
    parser.add_argument("source", type=Path, help="Path to the .mirage program file")
    parser.add_argument(
        "--env",
        dest="env_path",
        type=Path,
        default=Path(".env"),
        help="Optional path to an environment file with OPENAI_API_KEY",
    )
    parser.add_argument(
        "--dump-state",
        dest="dump_state",
        action="store_true",
        help="Print the final memory snapshot after execution",
    )
    parser.add_argument(
        "--arg",
        dest="arg_inputs",
        action="append",
        default=[],
        metavar="NAME=VALUE",
        help="Provide a value for an input argument declared in the script",
    )
    parser.add_argument(
        "--file",
        dest="file_inputs",
        action="append",
        default=[],
        metavar="NAME=PATH",
        help="Provide a path for an input file declared in the script",
    )
    return parser


def _parse_assignments(pairs: list[str], *, label: str) -> Dict[str, str]:
    assignments: Dict[str, str] = {}
    for pair in pairs:
        if "=" not in pair:
            raise ValueError(f"Malformed --{label} value '{pair}'. Use NAME=VALUE format.")
        name, value = pair.split("=", 1)
        name = name.strip()
        if not name:
            raise ValueError(f"Missing name in --{label} assignment '{pair}'.")
        assignments[name] = value
    return assignments


def main(argv: list[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)

    load_env_file(args.env_path)

    try:
        program = parse_program(args.source)
    except FileNotFoundError:
        parser.error(f"No such program file: {args.source}")
    except MirageParseError as error:
        parser.error(str(error))

    try:
        client = OpenAIClient(model="gpt-5-mini", temperature=1.0)
    except OpenAIError as error:
        parser.error(str(error))

    try:
        argument_values = _parse_assignments(args.arg_inputs, label="argument")
        file_paths = _parse_assignments(args.file_inputs, label="file")
    except ValueError as error:
        parser.error(str(error))

    input_values: Dict[str, str] = {}
    for declaration in program.inputs:
        if declaration.kind == "argument":
            raw_value = argument_values.pop(declaration.name, None)
            if raw_value is None:
                parser.error(
                    f"Missing --arg {declaration.name}=<value> for declared input argument"
                )
            input_values[declaration.name] = raw_value
        elif declaration.kind == "file":
            raw_path = file_paths.pop(declaration.name, None)
            if raw_path is None:
                parser.error(
                    f"Missing --file {declaration.name}=<path> for declared input file"
                )
            file_path = Path(raw_path).expanduser()
            try:
                content = file_path.read_text(encoding="utf-8")
            except OSError as error:
                parser.error(
                    f"Failed to read file for input '{declaration.name}': {error}"
                )
            input_values[declaration.name] = content
        else:
            parser.error(f"Unsupported input kind: {declaration.kind}")

    if argument_values:
        unexpected = ", ".join(sorted(argument_values))
        parser.error(f"Unexpected --arg values provided for undeclared inputs: {unexpected}")
    if file_paths:
        unexpected = ", ".join(sorted(file_paths))
        parser.error(f"Unexpected --file values provided for undeclared inputs: {unexpected}")

    interpreter = MirageInterpreter(program, client, input_values=input_values)
    try:
        result = interpreter.run()
    except MirageRuntimeError as error:
        parser.error(str(error))
    for line in result.outputs:
        print(line)
    if args.dump_state:
        print("\nfinal memory:")
        for memory in result.state.snapshot():
            history_tail = f" | notes: {'; '.join(memory.history)}" if memory.history else ""
            print(f"- {memory.name} [{memory.type_hint}]: {memory.description}{history_tail}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
