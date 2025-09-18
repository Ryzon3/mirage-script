"""State management for MirageScript runtime."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List


@dataclass
class MemoryValue:
    name: str
    type_hint: str
    description: str
    history: List[str] = field(default_factory=list)

    def update(self, description: str, note: str | None = None) -> None:
        self.description = description
        if note:
            self.history.append(note)


class RuntimeState:
    def __init__(self) -> None:
        self._values: Dict[str, MemoryValue] = {}

    def remember(
        self,
        name: str,
        type_hint: str,
        description: str,
        note: str | None = None,
    ) -> MemoryValue:
        memory = self._values.get(name)
        if memory is None:
            memory = MemoryValue(name=name, type_hint=type_hint, description=description)
            self._values[name] = memory
        else:
            memory.type_hint = type_hint
            memory.description = description
        if note:
            memory.history.append(note)
        return memory

    def recall(self, name: str) -> MemoryValue | None:
        return self._values.get(name)

    def update(self, name: str, description: str, note: str | None = None) -> MemoryValue:
        memory = self._values.get(name)
        if memory is None:
            raise KeyError(f"Unknown memory '{name}'")
        memory.update(description=description, note=note)
        return memory

    def snapshot(self) -> List[MemoryValue]:
        return list(self._values.values())

    def summary(self) -> str:
        if not self._values:
            return "(memory is empty)"
        lines: List[str] = []
        for memory in self._values.values():
            lines.append(f"- {memory.name} [{memory.type_hint}]: {memory.description}")
        return "\n".join(lines)

    def items(self) -> Iterable[tuple[str, MemoryValue]]:
        return self._values.items()
