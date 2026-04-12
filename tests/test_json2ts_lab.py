import unittest
import os
import json
from pathlib import Path
from tempfile import NamedTemporaryFile
from shared.json2ts_lab import Json2TsManager, run_json2ts_lab_logic
import sys
from io import StringIO
from unittest.mock import patch, MagicMock

class DummyArgs:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

class TestJson2TsManager(unittest.TestCase):
    def setUp(self):
        self.manager = Json2TsManager()

    def test_convert_primitive(self):
        self.assertEqual(self.manager.convert('"hello"', "RootObject"), "export type RootObject = string;")
        self.assertEqual(self.manager.convert('123', "RootObject"), "export type RootObject = number;")
        self.assertEqual(self.manager.convert('true', "RootObject"), "export type RootObject = boolean;")

    def test_convert_simple_object(self):
        json_data = '{"name": "Alice", "age": 30}'
        result = self.manager.convert(json_data, "User")
        self.assertIn("export interface User", result)
        self.assertIn("name: string;", result)
        self.assertIn("age: number;", result)

    def test_convert_nested_object(self):
        json_data = '{"user": {"name": "Alice", "age": 30}, "active": true}'
        result = self.manager.convert(json_data, "Root")
        self.assertIn("export interface User", result)
        self.assertIn("export interface Root", result)
        self.assertIn("user: User;", result)
        self.assertIn("active: boolean;", result)

    def test_convert_list_of_objects(self):
        json_data = '[{"id": 1, "name": "A"}, {"id": 2, "name": "B"}]'
        result = self.manager.convert(json_data, "Users")
        self.assertIn("export type Users = UserItem[];", result)

    def test_convert_list_primitive(self):
        json_data = '[1, 2, 3]'
        result = self.manager.convert(json_data, "Numbers")
        self.assertIn("export type Numbers = number[];", result)

    def test_convert_empty_list(self):
        json_data = '{"items": []}'
        result = self.manager.convert(json_data, "Root")
        self.assertIn("items: any[];", result)

    def test_invalid_json(self):
        with self.assertRaises(ValueError):
            self.manager.convert("{invalid:", "Root")

    def test_non_identifier_keys(self):
        json_data = '{"first name": "Alice", "user-age": 30}'
        result = self.manager.convert(json_data, "Root")
        self.assertIn('"first name": string;', result)
        self.assertIn('"user-age": number;', result)


class TestJson2TsCLI(unittest.TestCase):
    def test_run_json2ts_text(self):
        args = DummyArgs(text='{"name": "Alice"}', file=None, name="User", output=None, tui=False)
        with patch('sys.stdout', new=StringIO()) as fake_out:
            self.assertTrue(run_json2ts_lab_logic(args))
            self.assertIn("export interface User", fake_out.getvalue())

    def test_run_json2ts_file(self):
        with NamedTemporaryFile(mode='w', delete=False, suffix=".json") as tmp:
            tmp.write('{"name": "Bob"}')
            tmp_path = tmp.name

        args = DummyArgs(text=None, file=tmp_path, name="User", output=None, tui=False)
        try:
            with patch('sys.stdout', new=StringIO()) as fake_out:
                self.assertTrue(run_json2ts_lab_logic(args))
                self.assertIn("export interface User", fake_out.getvalue())
        finally:
            os.remove(tmp_path)

    def test_run_json2ts_invalid_json(self):
        args = DummyArgs(text='{"name": "Alice"', file=None, name="User", output=None, tui=False)
        with patch('sys.stderr', new=StringIO()) as fake_err:
            self.assertFalse(run_json2ts_lab_logic(args))
            self.assertIn("Invalid JSON", fake_err.getvalue())
