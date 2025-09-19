"""Command-line interface for the Mirage interpreter."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Dict

from .interpreter import MirageInterpreter, MirageRuntimeError
from .llm_client import OpenAIClient, OpenAIError


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
    parser = argparse.ArgumentParser(description="Run Mirage programs with GPT guidance")
    parser.add_argument("source", type=Path, help="Path to the .mirage program file")
    parser.add_argument(
        "--env",
        dest="env_path",
        type=Path,
        default=Path(".env"),
        help="Optional path to an environment file with OPENAI_API_KEY",
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
        source_text = args.source.read_text(encoding="utf-8")
    except FileNotFoundError:
        parser.error(f"No such program file: {args.source}")
    except OSError as error:
        parser.error(f"Failed to read program file: {error}")

    try:
        client = OpenAIClient(model="gpt-5-mini", temperature=1.0)
    except OpenAIError as error:
        parser.error(str(error))

    try:
        argument_values = _parse_assignments(args.arg_inputs, label="arg")
        file_paths = _parse_assignments(args.file_inputs, label="file")
    except ValueError as error:
        parser.error(str(error))

    expanded_files: Dict[str, Path] = {}
    for name, raw_path in file_paths.items():
        expanded_files[name] = Path(raw_path).expanduser()

    interpreter = MirageInterpreter(
        source_path=args.source,
        source_text=source_text,
        client=client,
        argument_inputs=argument_values,
        file_inputs=expanded_files,
    )

    try:
        result = interpreter.run()
    except MirageRuntimeError as error:
        parser.error(str(error))

    for line in result.outputs:
        print(line)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
