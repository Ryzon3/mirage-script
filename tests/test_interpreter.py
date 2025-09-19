from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict, List

from mirage_engine.interpreter import MirageInterpreter, MirageRuntimeError


class FakeClient:
    def __init__(self, responses: List[Dict[str, Any]]) -> None:
        self._responses = list(responses)
        self.calls: List[Dict[str, Any]] = []

    def complete(
        self,
        messages: List[Dict[str, Any]],
        *,
        tools: List[Dict[str, Any]] | None = None,
        tool_choice: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        if not self._responses:
            raise AssertionError("No fake responses remaining")
        self.calls.append({"messages": list(messages), "tools": tools})
        return {"message": self._responses.pop(0)}


class InterpreterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source_path = Path("/tmp/sample.mirage")
        self.sample_source = "remember greeting as Text with \"hello\""

    def test_emit_output_and_finish(self) -> None:
        client = FakeClient(
            [
                {
                    "role": "assistant",
                    "tool_calls": [
                        {
                            "id": "call-1",
                            "type": "function",
                            "function": {
                                "name": "emit_output",
                                "arguments": '{"text": "hi there"}',
                            },
                        }
                    ],
                },
                {"role": "assistant", "content": "done"},
            ]
        )

        interpreter = MirageInterpreter(
            source_path=self.source_path,
            source_text=self.sample_source,
            client=client,  # type: ignore[arg-type]
        )
        result = interpreter.run()

        self.assertEqual(result.outputs, ["hi there"])
        self.assertEqual(result.final_message, "done")

    def test_raise_error_tool_surfaces_message(self) -> None:
        client = FakeClient(
            [
                {
                    "role": "assistant",
                    "tool_calls": [
                        {
                            "id": "call-err",
                            "type": "function",
                            "function": {
                                "name": "raise_error",
                                "arguments": '{"message": "bad input"}',
                            },
                        }
                    ],
                }
            ]
        )

        interpreter = MirageInterpreter(
            source_path=self.source_path,
            source_text=self.sample_source,
            client=client,  # type: ignore[arg-type]
        )

        with self.assertRaisesRegex(MirageRuntimeError, "bad input"):
            interpreter.run()

    def test_get_input_reads_argument(self) -> None:
        client = FakeClient(
            [
                {
                    "role": "assistant",
                    "tool_calls": [
                        {
                            "id": "call-input",
                            "type": "function",
                            "function": {
                                "name": "get_input",
                                "arguments": '{"name": "numbers"}',
                            },
                        }
                    ],
                },
                {
                    "role": "assistant",
                    "tool_calls": [
                        {
                            "id": "call-output",
                            "type": "function",
                            "function": {
                                "name": "emit_output",
                                "arguments": '{"text": "numbers: [1,2,3]"}',
                            },
                        }
                    ],
                },
                {"role": "assistant", "content": "finished"},
            ]
        )

        interpreter = MirageInterpreter(
            source_path=self.source_path,
            source_text=self.sample_source,
            client=client,  # type: ignore[arg-type]
            argument_inputs={"numbers": "[1,2,3]"},
        )
        result = interpreter.run()

        self.assertEqual(result.outputs, ["numbers: [1,2,3]"])
        self.assertEqual(result.final_message, "finished")

        # Ensure the tool response delivered the argument content back to the model.
        tool_exchange = client.calls[1]["messages"][-1]
        self.assertEqual(tool_exchange["role"], "tool")
        payload = json.loads(tool_exchange["content"])
        self.assertTrue(payload["available"])
        self.assertEqual(payload["value"], "[1,2,3]")

    def test_save_file_writes_relative_to_script(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            script_dir = Path(tmp_dir)
            script_path = script_dir / "example.mirage"
            script_path.write_text("story \"Example\"", encoding="utf-8")

            interpreter = MirageInterpreter(
                source_path=script_path,
                source_text=script_path.read_text(encoding="utf-8"),
                client=FakeClient([]),  # type: ignore[arg-type]
            )

            result = interpreter._tool_save_file(
                {"path": "notes/run.txt", "content": "hello"}
            )

            expected_path = script_dir / "notes" / "run.txt"
            self.assertTrue(expected_path.exists())
            self.assertEqual(expected_path.read_text(encoding="utf-8"), "hello")
            self.assertEqual(Path(result["path"]), expected_path)


if __name__ == "__main__":
    unittest.main()
