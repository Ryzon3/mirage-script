"""Interpreter for MirageScript programs."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Sequence

from .llm_client import OpenAIClient, OpenAIError
from .model import (
    CallArgument,
    CallStatement,
    FunctionDef,
    NoteStatement,
    Program,
    RememberStatement,
    ShowStatement,
    ValueToken,
)
from .state import RuntimeState


class MirageRuntimeError(RuntimeError):
    """Raised when execution cannot proceed."""


@dataclass
class RunResult:
    outputs: List[str]
    state: RuntimeState


class MirageInterpreter:
    def __init__(
        self,
        program: Program,
        client: OpenAIClient,
        input_values: Dict[str, str] | None = None,
    ):
        self.program = program
        self.client = client
        self.state = RuntimeState()
        self._history: Dict[str, List[Dict[str, str]]] = {}
        self._outputs: List[str] = []
        self._input_values = dict(input_values or {})
        self._inputs_seeded = False

    def run(self) -> RunResult:
        if not self._inputs_seeded:
            self._seed_inputs()
        for statement in self.program.statements:
            if isinstance(statement, RememberStatement):
                self._handle_remember(statement)
            elif isinstance(statement, CallStatement):
                self._handle_call(statement)
            elif isinstance(statement, ShowStatement):
                self._handle_show(statement)
            elif isinstance(statement, NoteStatement):
                self._outputs.append(f"note: {statement.text}")
            else:
                raise MirageRuntimeError(f"Unknown statement type: {statement}")
        return RunResult(outputs=self._outputs, state=self.state)

    def _handle_remember(self, statement: RememberStatement) -> None:
        description = self._interpolate(statement.description)
        self.state.remember(statement.name, statement.type_hint, description)
        self._outputs.append(
            f"remembered {statement.name} [{statement.type_hint}] = {description}"
        )

    def _handle_show(self, statement: ShowStatement) -> None:
        content = self._resolve_value(statement.value)
        self._outputs.append(f"show: {content}")

    def _resolve_value(self, token: ValueToken) -> str:
        if token.is_reference:
            target = token.reference_name
            if target is None:
                raise MirageRuntimeError("Reference token missing name")
            memory = self.state.recall(target)
            if memory is None:
                raise MirageRuntimeError(f"Cannot show unknown memory '{target}'")
            return f"{target} [{memory.type_hint}] = {memory.description}"
        return token.raw

    def _interpolate(self, text: str) -> str:
        def replace(match: re.Match[str]) -> str:
            name = match.group(1)
            memory = self.state.recall(name)
            if memory is None:
                return match.group(0)
            return memory.description

        return re.sub(r"\{([A-Za-z_][A-Za-z0-9_]*)\}", replace, text)

    def _handle_call(self, statement: CallStatement) -> None:
        function = self.program.functions.get(statement.function_name)
        if function is None:
            raise MirageRuntimeError(f"Function {statement.function_name!r} is not defined")
        argument_payload = self._build_arguments(statement.arguments, function)
        state_summary = self.state.summary()
        tools = [self._tool_schema()]
        messages = self._build_messages(function, argument_payload, state_summary)
        try:
            choice = self.client.complete(
                messages,
                tools=tools,
                tool_choice={"type": "function", "function": {"name": "emit_response"}},
            )
        except OpenAIError as error:
            raise MirageRuntimeError(str(error)) from error

        assistant_message = choice.get("message")
        if not isinstance(assistant_message, dict):
            raise MirageRuntimeError("Assistant response missing message payload")

        result_payload = self._extract_tool_arguments(assistant_message, "emit_response")

        assistant_summary = json.dumps(result_payload, ensure_ascii=False)
        self._history.setdefault(function.name, []).extend([
            {"role": "user", "content": messages[-1]["content"]},
            {"role": "assistant", "content": assistant_summary},
        ])

        return_block = result_payload.get("return")
        if not isinstance(return_block, dict):
            raise MirageRuntimeError("LLM response missing 'return' object")
        return_value = return_block.get("value")
        if not isinstance(return_value, str):
            raise MirageRuntimeError("LLM response return value must be a string description")
        summary_note = return_block.get("summary")
        self.state.remember(
            statement.target,
            function.return_type,
            return_value,
            note=summary_note if isinstance(summary_note, str) else None,
        )
        self._outputs.append(
            f"ask {function.name} -> {statement.target} [{function.return_type}] = {return_value}"
        )

        updates = result_payload.get("updates", [])
        if isinstance(updates, list):
            for update in updates:
                if not isinstance(update, dict):
                    continue
                target = update.get("target")
                value = update.get("value")
                if not isinstance(target, str) or not isinstance(value, str):
                    continue
                note = update.get("summary")
                note_text = note if isinstance(note, str) else None
                type_hint = update.get("type")
                if isinstance(type_hint, str):
                    self.state.remember(target, type_hint, value, note=note_text)
                else:
                    try:
                        self.state.update(target, value, note=note_text)
                    except KeyError:
                        self.state.remember(target, "Unknown", value, note=note_text)
                self._outputs.append(f"update {target} = {value}")

        notes = result_payload.get("notes")
        if isinstance(notes, list):
            for note in notes:
                if isinstance(note, str):
                    self._outputs.append(f"assistant note: {note}")

    def _seed_inputs(self) -> None:
        for decl in self.program.inputs:
            value = self._input_values.get(decl.name)
            if value is None:
                raise MirageRuntimeError(
                    f"Missing value for {decl.kind} '{decl.name}'. Provide one via CLI."
                )
            self.state.remember(decl.name, decl.type_hint, value)
            self._outputs.append(
                f"input {decl.kind} {decl.name} [{decl.type_hint}] = {value}"
            )
        self._inputs_seeded = True

    def _build_arguments(
        self, arguments: Sequence[CallArgument], function: FunctionDef
    ) -> List[Dict[str, str]]:
        payload: List[Dict[str, str]] = []
        arg_type_lookup = {arg.name: arg.type_hint for arg in function.arguments}
        provided_names = {argument.name for argument in arguments}
        missing = [arg.name for arg in function.arguments if arg.name not in provided_names]
        if missing:
            raise MirageRuntimeError(
                f"Call to {function.name} missing arguments: {', '.join(missing)}"
            )
        for argument in arguments:
            type_hint = arg_type_lookup.get(argument.name, "Unknown")
            if argument.value.is_reference:
                name = argument.value.reference_name
                if not name:
                    raise MirageRuntimeError("Reference argument missing a target name")
                memory = self.state.recall(name)
                if memory is None:
                    raise MirageRuntimeError(f"Argument references unknown memory '{name}'")
                payload.append(
                    {
                        "name": argument.name,
                        "type": type_hint,
                        "origin": "memory",
                        "memory_name": name,
                        "value": memory.description,
                    }
                )
            else:
                payload.append(
                    {
                        "name": argument.name,
                        "type": type_hint,
                        "origin": "literal",
                        "value": argument.value.raw,
                    }
                )
        return payload

    def _build_messages(
        self,
        function: FunctionDef,
        argument_payload: Sequence[Dict[str, str]],
        state_summary: str,
    ) -> List[Dict[str, str]]:
        developer_message = {
            "role": "developer",
            "content": (
                "You are MirageScript's imagination kernel. Use the `emit_response` tool exactly "
                "once to respond. Keep answers playful but concise."
                " Respect memory names exactly as given and avoid inventing new slots or"
                " dotted variants."
            ),
        }
        argument_lines = []
        for item in argument_payload:
            if item["origin"] == "memory":
                argument_lines.append(
                    "- {name} [{type}] from memory '{memory}': {value}".format(
                        name=item["name"],
                        type=item["type"],
                        memory=item["memory_name"],
                        value=item["value"],
                    )
                )
            else:
                argument_lines.append(f"- {item['name']} [{item['type']}]: {item['value']}")
        object_lines = []
        for obj in self.program.objects.values():
            if not obj.fields:
                object_lines.append(f"- {obj.name}: (no fields declared)")
                continue
            field_descriptions = ", ".join(
                f"{field.name} ({field.type_hint})" for field in obj.fields
            )
            object_lines.append(f"- {obj.name}: {field_descriptions}")
        prompt_text = (
            f"Function name: {function.name}\n"
            f"Purpose: {function.prompt}\n\n"
            f"Return type: {function.return_type}\n\n"
            f"Arguments:\n" + "\n".join(argument_lines or ["(no arguments)"]) + "\n\n"
            "Known objects:\n" + "\n".join(object_lines or ["(no objects declared)"]) + "\n\n"
            f"Current memory:\n{state_summary}\n\n"
            "Call the `emit_response` tool once with:\n"
            "- return: object containing optional type, required value, optional summary\n"
            "- updates: list describing memory adjustments (target, optional type, value, optional"
            " summary)\n"
            "- notes: list of playful remarks for the human programmer\n"
            "Use empty lists when nothing changes. Keep descriptions short and vivid."
            " When updating memories, target the base memory name (e.g., 'payload') and provide"
            " its full new description."
        )

        user_message = {"role": "user", "content": prompt_text}

        history = self._history.get(function.name, [])
        return [developer_message, *history, user_message]

    @staticmethod
    def _tool_schema() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "emit_response",
                "description": (
                    "Return the MirageScript function call result, including the main return value,"
                    " any memory updates, and light-hearted notes for the human."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "return": {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string"},
                                "value": {"type": "string"},
                                "summary": {"type": "string"},
                            },
                            "required": ["value"],
                            "additionalProperties": False,
                        },
                        "updates": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "target": {"type": "string"},
                                    "type": {"type": "string"},
                                    "value": {"type": "string"},
                                    "summary": {"type": "string"},
                                },
                                "required": ["target", "value"],
                                "additionalProperties": False,
                            },
                        },
                        "notes": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                    "required": ["return", "updates", "notes"],
                    "additionalProperties": False,
                },
            },
        }

    @staticmethod
    def _extract_tool_arguments(message: Dict[str, Any], expected_name: str) -> Dict[str, Any]:
        tool_calls = message.get("tool_calls")
        if not isinstance(tool_calls, list) or not tool_calls:
            raise MirageRuntimeError("Assistant did not call the required tool")
        for call in tool_calls:
            if not isinstance(call, dict):
                continue
            if call.get("type") != "function":
                continue
            function = call.get("function")
            if not isinstance(function, dict):
                continue
            if function.get("name") != expected_name:
                continue
            arguments = function.get("arguments")
            if not isinstance(arguments, str):
                raise MirageRuntimeError("Tool arguments missing or malformed")
            try:
                return json.loads(arguments)
            except json.JSONDecodeError as error:
                raise MirageRuntimeError("Tool arguments were not valid JSON") from error
        raise MirageRuntimeError("Assistant did not call the expected tool")
