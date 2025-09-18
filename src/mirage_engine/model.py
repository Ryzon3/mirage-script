"""Core dataclasses that describe MirageScript programs."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Sequence


@dataclass
class FieldDef:
    name: str
    type_hint: str
    description: str | None = None


@dataclass
class ObjectDef:
    name: str
    fields: Sequence[FieldDef] = field(default_factory=list)


@dataclass
class FunctionArg:
    name: str
    type_hint: str


@dataclass
class FunctionDef:
    name: str
    arguments: Sequence[FunctionArg]
    return_type: str
    prompt: str


@dataclass
class InputDecl:
    kind: str  # "argument" or "file"
    name: str
    type_hint: str
    description: str | None = None


@dataclass
class RememberStatement:
    name: str
    type_hint: str
    description: str


@dataclass
class ValueToken:
    raw: str
    is_reference: bool

    @property
    def reference_name(self) -> str | None:
        if self.is_reference:
            if self.raw.startswith('@'):
                return self.raw[1:]
            return self.raw
        return None


@dataclass
class CallArgument:
    name: str
    value: ValueToken


@dataclass
class CallStatement:
    function_name: str
    arguments: Sequence[CallArgument]
    target: str


@dataclass
class ShowStatement:
    value: ValueToken


@dataclass
class NoteStatement:
    text: str


Statement = RememberStatement | CallStatement | ShowStatement | NoteStatement


@dataclass
class Program:
    title: str
    objects: Dict[str, ObjectDef]
    functions: Dict[str, FunctionDef]
    inputs: Sequence[InputDecl]
    statements: Sequence[Statement]
