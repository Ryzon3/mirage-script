"""Parser that turns MirageScript text into program dataclasses."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence, Tuple

from .model import (
    CallArgument,
    CallStatement,
    FieldDef,
    FunctionArg,
    FunctionDef,
    InputDecl,
    NoteStatement,
    ObjectDef,
    Program,
    RememberStatement,
    ShowStatement,
    Statement,
    ValueToken,
)


class MirageParseError(RuntimeError):
    """Raised when the source text cannot be parsed."""


@dataclass
class _LineCursor:
    lines: Sequence[str]
    index: int = 0

    def done(self) -> bool:
        return self.index >= len(self.lines)

    def peek(self) -> str:
        return self.lines[self.index]

    def advance(self, steps: int = 1) -> None:
        self.index += steps

    def consume(self) -> str:
        line = self.peek()
        self.advance()
        return line


_TITLE_PATTERN = re.compile(r'^story\s+"(?P<title>.+?)"\s*$')
_OBJECT_PATTERN = re.compile(r"^object\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*:\s*$")
_HELPER_PATTERN = re.compile(
    r"^helper\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s+returns\s+(?P<return>[A-Za-z0-9_<>,\s]+)\s*:\s*$"
)
_REMEMBER_PATTERN = re.compile(
    r'^remember\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s+as\s+(?P<type>[A-Za-z0-9_<>,\s]+)\s+with\s+"(?P<desc>.+)"\s*$'
)
_ASK_PATTERN = re.compile(r'^ask\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s+for:\s*$')
_ARG_PATTERN = re.compile(r'^(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s+is\s+(?P<value>.+)$')
_STORE_PATTERN = re.compile(r'^keep\s+answer\s+as\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*$')
_NOTE_PATTERN = re.compile(r'^note\s+"(?P<text>.+)"\s*$')
_SHOW_PATTERN = re.compile(r'^show(?:\s+memory)?\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*$')
_MEMORY_VALUE_PATTERN = re.compile(r'^memory\s+([A-Za-z_][A-Za-z0-9_]*)$')


def parse_program(path: Path) -> Program:
    text = path.read_text(encoding="utf-8")
    cursor = _LineCursor([line.rstrip("\n") for line in text.splitlines()])

    title = "Untitled Mirage"
    objects: dict[str, ObjectDef] = {}
    functions: dict[str, FunctionDef] = {}
    inputs: List[InputDecl] = []
    statements: List[Statement] = []

    while not cursor.done():
        raw_line = cursor.consume()
        stripped = raw_line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        title_match = _TITLE_PATTERN.match(stripped)
        if title_match:
            title = title_match.group("title")
            continue
        object_match = _OBJECT_PATTERN.match(stripped)
        if object_match:
            obj, new_index = _parse_object(cursor, object_match.group("name"))
            objects[obj.name] = obj
            cursor.index = new_index
            continue
        if stripped.lower() == "inputs:":
            parsed_inputs, new_index = _parse_inputs(cursor)
            inputs.extend(parsed_inputs)
            cursor.index = new_index
            continue
        helper_match = _HELPER_PATTERN.match(stripped)
        if helper_match:
            func, new_index = _parse_helper(cursor, helper_match)
            functions[func.name] = func
            cursor.index = new_index
            continue
        if stripped.lower() == "begin:":
            statements = _parse_statements(cursor)
            break
        raise MirageParseError(f"Unrecognised line: {raw_line!r}")

    return Program(
        title=title,
        objects=objects,
        functions=functions,
        inputs=inputs,
        statements=statements,
    )


def _parse_object(cursor: _LineCursor, name: str) -> Tuple[ObjectDef, int]:
    fields: List[FieldDef] = []
    index = cursor.index
    while index < len(cursor.lines):
        raw_line = cursor.lines[index]
        stripped = raw_line.strip()
        if not stripped:
            index += 1
            continue
        indent = len(raw_line) - len(raw_line.lstrip())
        if indent == 0:
            break
        if not stripped.startswith("has "):
            raise MirageParseError(f"Expected 'has' line inside object {name!r}, got: {raw_line!r}")
        field_line = stripped[len("has ") :]
        description = None
        meaning_split = field_line.split(" meaning ", 1)
        if len(meaning_split) == 2:
            field_part, description = [part.strip() for part in meaning_split]
            if description.startswith('"') and description.endswith('"'):
                description = description[1:-1]
        else:
            field_part = field_line.strip()
        if "(" not in field_part or ")" not in field_part:
            raise MirageParseError(f"Invalid field line: {raw_line!r}")
        name_part, type_part = field_part.split("(", 1)
        field_name = name_part.strip()
        type_hint = type_part.strip().rstrip(")")
        fields.append(FieldDef(name=field_name, type_hint=type_hint, description=description))
        index += 1
    return ObjectDef(name=name, fields=fields), index


def _parse_inputs(cursor: _LineCursor) -> Tuple[List[InputDecl], int]:
    items: List[InputDecl] = []
    index = cursor.index
    while index < len(cursor.lines):
        raw_line = cursor.lines[index]
        stripped = raw_line.strip()
        if not stripped:
            index += 1
            continue
        indent = len(raw_line) - len(raw_line.lstrip())
        if indent == 0:
            break
        if stripped.startswith("argument "):
            items.append(_parse_input_line(stripped, kind="argument"))
            index += 1
            continue
        if stripped.startswith("file "):
            items.append(_parse_input_line(stripped, kind="file"))
            index += 1
            continue
        raise MirageParseError(f"Unknown inputs line: {raw_line!r}")
    return items, index


def _parse_input_line(line: str, *, kind: str) -> InputDecl:
    remainder = line[len(kind) :].strip()
    if " as " not in remainder:
        raise MirageParseError(f"Malformed {kind} declaration: {line!r}")
    name_part, rest = remainder.split(" as ", 1)
    name = name_part.strip()
    description = None
    type_hint = rest.strip()
    if " with " in rest:
        type_part, desc_part = rest.split(" with ", 1)
        type_hint = type_part.strip()
        desc_part = desc_part.strip()
        if not (desc_part.startswith('"') and desc_part.endswith('"')):
            raise MirageParseError(f"Description must be wrapped in quotes: {line!r}")
        description = desc_part[1:-1]
    return InputDecl(kind=kind, name=name, type_hint=type_hint, description=description)


def _parse_helper(cursor: _LineCursor, match: re.Match[str]) -> Tuple[FunctionDef, int]:
    name = match.group("name")
    return_type = match.group("return").strip()
    arguments: List[FunctionArg] = []
    index = cursor.index
    while index < len(cursor.lines):
        raw_line = cursor.lines[index]
        stripped = raw_line.strip()
        if not stripped:
            index += 1
            continue
        indent = len(raw_line) - len(raw_line.lstrip())
        if indent == 0:
            break
        if stripped.startswith("needs "):
            arg_line = stripped[len("needs ") :]
            if "(" not in arg_line or ")" not in arg_line:
                raise MirageParseError(f"Malformed needs line: {raw_line!r}")
            name_part, type_part = arg_line.split("(", 1)
            arg_name = name_part.strip()
            type_hint = type_part.strip().rstrip(")")
            arguments.append(FunctionArg(name=arg_name, type_hint=type_hint))
            index += 1
            continue
        if stripped.lower() == "prompt:":
            index += 1
            break
        raise MirageParseError(f"Unexpected line in helper {name!r}: {raw_line!r}")
    else:
        raise MirageParseError(f"Helper {name!r} missing prompt:")

    while index < len(cursor.lines):
        raw_line = cursor.lines[index]
        stripped = raw_line.strip()
        if not stripped:
            index += 1
            continue
        if stripped == "<<<":
            index += 1
            break
        raise MirageParseError(f"Expected <<< to start prompt for helper {name!r}")
    else:
        raise MirageParseError(f"Helper {name!r} is missing <<< delimiter")

    prompt_lines: List[str] = []
    while index < len(cursor.lines):
        raw_line = cursor.lines[index]
        stripped = raw_line.strip()
        if stripped == ">>>":
            index += 1
            break
        prompt_lines.append(raw_line)
        index += 1
    else:
        raise MirageParseError(f"Helper {name!r} prompt not closed with >>>")

    prompt = "\n".join(line.rstrip() for line in prompt_lines).strip()
    helper_def = FunctionDef(
        name=name,
        arguments=arguments,
        return_type=return_type,
        prompt=prompt,
    )
    return helper_def, index


def _parse_statements(cursor: _LineCursor) -> List[Statement]:
    statements: List[Statement] = []
    while cursor.index < len(cursor.lines):
        raw_line = cursor.lines[cursor.index]
        stripped = raw_line.strip()
        if not stripped or stripped.startswith('#'):
            cursor.advance()
            continue
        if stripped.startswith("remember "):
            statements.append(_parse_remember(raw_line))
            cursor.advance()
            continue
        if stripped.startswith("ask "):
            ask_stmt, new_index = _parse_ask(cursor)
            statements.append(ask_stmt)
            cursor.index = new_index
            continue
        if stripped.startswith("show "):
            show_match = _SHOW_PATTERN.match(stripped)
            if not show_match:
                raise MirageParseError(f"Malformed show line: {raw_line!r}")
            statements.append(ShowStatement(value=_parse_value(show_match.group("name"))))
            cursor.advance()
            continue
        if stripped.startswith("note "):
            note_match = _NOTE_PATTERN.match(stripped)
            if not note_match:
                raise MirageParseError(f"Malformed note line: {raw_line!r}")
            statements.append(NoteStatement(text=note_match.group("text")))
            cursor.advance()
            continue
        raise MirageParseError(f"Unknown statement: {raw_line!r}")
    return statements


def _parse_remember(raw_line: str) -> RememberStatement:
    match = _REMEMBER_PATTERN.match(raw_line.strip())
    if not match:
        raise MirageParseError(f"Malformed remember line: {raw_line!r}")
    return RememberStatement(
        name=match.group("name"),
        type_hint=match.group("type"),
        description=match.group("desc"),
    )


def _parse_ask(cursor: _LineCursor) -> Tuple[CallStatement, int]:
    ask_line = cursor.lines[cursor.index]
    indent = len(ask_line) - len(ask_line.lstrip())
    stripped = ask_line.strip()
    match = _ASK_PATTERN.match(stripped)
    if not match:
        raise MirageParseError(f"Malformed ask line: {ask_line!r}")
    function_name = match.group("name")

    arguments: List[CallArgument] = []
    index = cursor.index + 1
    while index < len(cursor.lines):
        raw_line = cursor.lines[index]
        stripped_line = raw_line.strip()
        if not stripped_line:
            index += 1
            continue
        current_indent = len(raw_line) - len(raw_line.lstrip())
        if current_indent <= indent:
            store_match = _STORE_PATTERN.match(stripped_line)
            if not store_match:
                raise MirageParseError(
                    f"Expected 'store answer in <name>' after ask block, got: {raw_line!r}"
                )
            target = store_match.group("name")
            call_statement = CallStatement(
                function_name=function_name,
                arguments=arguments,
                target=target,
            )
            return call_statement, index + 1
        arg_match = _ARG_PATTERN.match(stripped_line)
        if not arg_match:
            raise MirageParseError(f"Malformed argument line: {raw_line!r}")
        arg_name = arg_match.group("name")
        value_text = arg_match.group("value").strip()
        arguments.append(CallArgument(name=arg_name, value=_parse_value(value_text)))
        index += 1

    raise MirageParseError(f"Ask block for helper {function_name!r} missing 'store answer' line")


def _parse_value(raw_value: str, *, is_inline: bool = False) -> ValueToken:
    stripped = raw_value.strip()
    memory_match = _MEMORY_VALUE_PATTERN.match(stripped)
    if memory_match:
        name = memory_match.group(1)
        return ValueToken(raw=name, is_reference=True)
    if (
        stripped.startswith('"')
        and stripped.endswith('"')
        and len(stripped) >= 2
    ):
        return ValueToken(raw=stripped[1:-1], is_reference=False)
    if not is_inline:
        # treat bare words as memory references to keep syntax light
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", stripped):
            return ValueToken(raw=stripped, is_reference=True)
    return ValueToken(raw=stripped, is_reference=False)
