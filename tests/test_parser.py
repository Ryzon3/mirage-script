from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from mirage_engine.parser import parse_program


class ParserTests(unittest.TestCase):
    def test_parse_basic_program(self) -> None:
        source = (
            'story "Test"\n\n'
            'object Friend:\n'
            '  has name (Text) meaning "a friendly name"\n\n'
            'helper greet returns Text:\n'
            '  needs friend (Friend)\n'
            '  prompt:\n'
            '<<<\n'
            'Say hello.\n'
            '>>>\n\n'
            'begin:\n'
            '  remember buddy as Friend with "name: Jamie"\n'
            '  ask greet for:\n'
            '    friend is memory buddy\n'
            '  keep answer as wave\n'
            '  show wave\n'
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "sample.mirage"
            path.write_text(source, encoding="utf-8")
            program = parse_program(path)
        self.assertEqual(program.title, "Test")
        self.assertIn("Friend", program.objects)
        self.assertIn("greet", program.functions)
        self.assertEqual(len(program.inputs), 0)
        self.assertEqual(len(program.statements), 3)
        call_stmt = program.statements[1]
        self.assertEqual(call_stmt.function_name, "greet")
        self.assertEqual(call_stmt.target, "wave")

    def test_parse_inputs_section(self) -> None:
        source = (
            'story "With Inputs"\n\n'
            'inputs:\n'
            '  argument numbers as List<Int>\n'
            '  file dataset as Text with "raw content"\n\n'
            'begin:\n'
            '  show numbers\n'
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "inputs.mirage"
            path.write_text(source, encoding="utf-8")
            program = parse_program(path)
        self.assertEqual(len(program.inputs), 2)
        self.assertEqual(program.inputs[0].kind, "argument")
        self.assertEqual(program.inputs[0].name, "numbers")
        self.assertEqual(program.inputs[1].kind, "file")
        self.assertEqual(program.inputs[1].description, "raw content")


if __name__ == "__main__":
    unittest.main()
