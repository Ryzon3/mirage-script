"""Conversation loop that lets the LLM play interpreter."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Sequence

from .llm_client import OpenAIClient

_SYSTEM_PROMPT_CACHE: str | None = None


class MirageRuntimeError(RuntimeError):
    """Raised when the interpreter session cannot continue."""


@dataclass
class RunResult:
    outputs: List[str] = field(default_factory=list)
    final_message: str | None = None
    messages: List[Dict[str, Any]] = field(default_factory=list)


class MirageInterpreter:
    """Thin controller that delegates all reasoning to the model."""

    def __init__(
        self,
        *,
        source_path: Path,
        source_text: str,
        client: OpenAIClient,
        argument_inputs: Dict[str, str] | None = None,
        file_inputs: Dict[str, Path] | None = None,
    ) -> None:
        self.source_path = source_path
        self.source_text = source_text
        self.client = client
        self.argument_inputs = dict(argument_inputs or {})
        self.file_inputs = dict(file_inputs or {})
        self.outputs: List[str] = []

    def run(self) -> RunResult:
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": self._system_prompt()},
            {"role": "user", "content": self._initial_user_message()},
        ]

        final_message: str | None = None

        while True:
            choice = self.client.complete(messages, tools=self._tool_schemas())
            assistant_message = choice.get("message")
            if not isinstance(assistant_message, dict):
                raise MirageRuntimeError("Assistant response missing message payload")

            messages.append(assistant_message)

            tool_calls = assistant_message.get("tool_calls")
            if tool_calls:
                self._handle_tool_calls(messages, tool_calls)
                continue

            content = assistant_message.get("content")
            if isinstance(content, str) and content.strip():
                final_message = content
            break

        return RunResult(outputs=self.outputs, final_message=final_message, messages=messages)

    def _handle_tool_calls(
        self,
        messages: List[Dict[str, Any]],
        tool_calls: Sequence[Dict[str, Any]],
    ) -> None:
        for call in tool_calls:
            if not isinstance(call, dict):
                raise MirageRuntimeError("Tool call payload malformed")
            call_id = call.get("id")
            if not isinstance(call_id, str):
                raise MirageRuntimeError("Tool call missing identifier")
            function = call.get("function")
            if not isinstance(function, dict):
                raise MirageRuntimeError("Tool call missing function payload")
            name = function.get("name")
            if not isinstance(name, str):
                raise MirageRuntimeError("Tool call missing function name")
            arguments_raw = function.get("arguments", "{}")
            if not isinstance(arguments_raw, str):
                raise MirageRuntimeError("Tool arguments must be a JSON string")
            try:
                arguments = json.loads(arguments_raw) if arguments_raw else {}
            except json.JSONDecodeError as error:
                raise MirageRuntimeError(
                    f"Assistant provided invalid JSON for {name!r}: {arguments_raw}"
                ) from error

            result = self._execute_tool(name, arguments)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call_id,
                    "name": name,
                    "content": json.dumps(result, ensure_ascii=False),
                }
            )

    def _execute_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if name == "emit_output":
            return self._tool_emit_output(arguments)
        if name == "list_inputs":
            return self._tool_list_inputs()
        if name == "get_input":
            return self._tool_get_input(arguments)
        if name == "read_source":
            return self._tool_read_source()
        if name == "read_file":
            return self._tool_read_file(arguments)
        if name == "save_file":
            return self._tool_save_file(arguments)
        if name == "raise_error":
            self._tool_raise_error(arguments)
        raise MirageRuntimeError(f"Assistant requested unknown tool '{name}'")

    def _tool_emit_output(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        text = arguments.get("text")
        if not isinstance(text, str):
            raise MirageRuntimeError("emit_output requires a string 'text' field")
        self.outputs.append(text)
        return {"status": "ok"}

    def _tool_list_inputs(self) -> Dict[str, Any]:
        return {
            "arguments": sorted(self.argument_inputs.keys()),
            "files": sorted(self.file_inputs.keys()),
        }

    def _tool_get_input(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        name = arguments.get("name")
        if not isinstance(name, str) or not name.strip():
            raise MirageRuntimeError("get_input requires a non-empty 'name'")
        kind = arguments.get("kind")
        if kind is not None and kind not in {"argument", "file"}:
            raise MirageRuntimeError("get_input kind must be 'argument' or 'file'")

        if kind in (None, "argument") and name in self.argument_inputs:
            return {
                "kind": "argument",
                "name": name,
                "value": self.argument_inputs[name],
                "available": True,
            }

        if kind in (None, "file") and name in self.file_inputs:
            path = self.file_inputs[name]
            try:
                content = path.read_text(encoding="utf-8")
            except OSError as error:
                raise MirageRuntimeError(f"Failed to read file input '{name}': {error}")
            return {
                "kind": "file",
                "name": name,
                "path": str(path),
                "value": content,
                "available": True,
            }

        return {
            "kind": kind or "unknown",
            "name": name,
            "available": False,
        }

    def _tool_read_source(self) -> Dict[str, Any]:
        return {
            "path": str(self.source_path),
            "content": self.source_text,
        }

    def _tool_read_file(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        path_value = arguments.get("path")
        if not isinstance(path_value, str) or not path_value.strip():
            raise MirageRuntimeError("read_file requires a non-empty 'path'")
        target = self._resolve_path(path_value)
        try:
            content = target.read_text(encoding="utf-8")
        except OSError as error:
            return {
                "path": str(target),
                "available": False,
                "error": str(error),
            }
        return {"path": str(target), "available": True, "content": content}

    def _tool_save_file(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        path_value = arguments.get("path")
        content = arguments.get("content")
        if not isinstance(path_value, str) or not path_value.strip():
            raise MirageRuntimeError("save_file requires a non-empty 'path'")
        if not isinstance(content, str):
            raise MirageRuntimeError("save_file requires string 'content'")
        target = self._resolve_path(path_value)
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        except OSError as error:
            raise MirageRuntimeError(f"Failed to write file '{path_value}': {error}")
        return {
            "path": str(target),
            "bytes_written": len(content.encode("utf-8")),
        }

    def _tool_raise_error(self, arguments: Dict[str, Any]) -> None:
        message = arguments.get("message")
        if not isinstance(message, str) or not message.strip():
            message = "Interpreter halted as requested by the program."
        raise MirageRuntimeError(message)

    def _resolve_path(self, path_value: str) -> Path:
        candidate = Path(path_value).expanduser()
        if candidate.is_absolute():
            return candidate

        # Prefer paths relative to the Mirage script directory when the input is not
        # absolute. This ensures new files created via save_file live alongside the
        # program rather than the caller's working directory.
        local_candidate = (self.source_path.parent / candidate).resolve()
        return local_candidate

    def _system_prompt(self) -> str:
        global _SYSTEM_PROMPT_CACHE
        if _SYSTEM_PROMPT_CACHE is None:
            prompt_path = Path(__file__).with_name("system_prompt.txt")
            try:
                _SYSTEM_PROMPT_CACHE = prompt_path.read_text(encoding="utf-8")
            except OSError as error:
                raise MirageRuntimeError(f"Failed to load system prompt: {error}")
        return _SYSTEM_PROMPT_CACHE

    def _initial_user_message(self) -> str:
        argument_names = ", ".join(sorted(self.argument_inputs)) or "(none provided)"
        file_names = ", ".join(sorted(self.file_inputs)) or "(none provided)"
        return (
            f"Program path: {self.source_path}\n"
            "Program source between <<< and >>> markers."
            "\n<<<\n"
            f"{self.source_text}\n"
            ">>>\n\n"
            "Inputs advertised by the CLI flags:\n"
            f"- arguments: {argument_names}\n"
            f"- files: {file_names}\n"
            "Use list_inputs and get_input to inspect their values when needed."
        )

    def _tool_schemas(self) -> Sequence[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "emit_output",
                    "description": "Append a human-visible line to the terminal output.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": "Line to print back to the programmer.",
                            }
                        },
                        "required": ["text"],
                        "additionalProperties": False,
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "list_inputs",
                    "description": "List the available argument and file input names.",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_input",
                    "description": (
                        "Fetch the value for a declared argument or file input."
                        " File inputs return their full text content."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "kind": {
                                "type": "string",
                                "enum": ["argument", "file"],
                                "description": "Optional explicit input kind.",
                            },
                        },
                        "required": ["name"],
                        "additionalProperties": False,
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "read_source",
                    "description": "Retrieve the entire Mirage source file again if needed.",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read an arbitrary UTF-8 text file relative to the program path.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"},
                        },
                        "required": ["path"],
                        "additionalProperties": False,
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "save_file",
                    "description": "Write UTF-8 content to a file relative to the program path.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"},
                            "content": {"type": "string"},
                        },
                        "required": ["path", "content"],
                        "additionalProperties": False,
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "raise_error",
                    "description": "Abort execution and surface a message to the human programmer.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "message": {"type": "string"},
                        },
                        "required": ["message"],
                        "additionalProperties": False,
                    },
                },
            },
        ]
