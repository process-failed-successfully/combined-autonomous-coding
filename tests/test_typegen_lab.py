import unittest
from shared.typegen_lab import TypegenManager, run_typegen_lab_logic
import argparse







class TestTypegenManager(unittest.TestCase):
    def setUp(self):
        self.manager = TypegenManager()

    def test_get_type_name(self):
        self.assertEqual(self.manager._get_type_name("my_snake_case"), "MySnakeCase")
        self.assertEqual(self.manager._get_type_name("camelCase"), "Camelcase")
        self.assertEqual(self.manager._get_type_name("hyphen-case"), "HyphenCase")

    def test_generate_typescript(self):
        json_str = '{"name": "John", "age": 30, "isActive": true}'
        result = self.manager.generate(json_str, root_name="User", lang="typescript")
        self.assertIn("export interface User {", result)
        self.assertIn("name: string;", result)
        self.assertIn("age: number;", result)
        self.assertIn("isActive: boolean;", result)

    def test_generate_go(self):
        json_str = '{"user_id": 123, "email": "test@example.com"}'
        result = self.manager.generate(json_str, root_name="Account", lang="go")
        self.assertIn("type Account struct {", result)
        self.assertIn("UserId int `json:\"user_id\"`", result)
        self.assertIn("Email string `json:\"email\"`", result)

    def test_generate_python(self):
        json_str = '{"items": [1, 2, 3], "tags": ["a", "b"]}'
        result = self.manager.generate(json_str, root_name="Data", lang="python")
        self.assertIn("@dataclass", result)
        self.assertIn("class Data:", result)
        self.assertIn("items: List[int]", result)
        self.assertIn("tags: List[str]", result)

    def test_generate_rust(self):
        json_str = '{"id": "abc", "count": 10, "type": "user"}'
        result = self.manager.generate(json_str, root_name="Response", lang="rust")
        self.assertIn("pub struct Response {", result)
        self.assertIn("pub id: String,", result)
        self.assertIn("pub count: i64,", result)
        self.assertIn("pub r#type: String,", result)
        self.assertIn("#[serde(rename = \"type\")]", result)

    def test_generate_nested(self):
        json_str = '{"user": {"name": "test"}}'
        result = self.manager.generate(json_str, root_name="Root", lang="typescript")
        self.assertIn("export interface Root {", result)
        self.assertIn("user: User;", result)
        self.assertIn("export interface User {", result)
        self.assertIn("name: string;", result)

    def test_invalid_json(self):
        result = self.manager.generate("{invalid json", root_name="Root")
        self.assertIn("Error parsing JSON", result)







class TestTypegenLabCLI(unittest.TestCase):
    def test_run_logic_json_arg(self):
        from unittest.mock import patch
        args = argparse.Namespace(json='{"id": 1}', name="Root", lang="go")

        with patch('builtins.print') as mock_print:
            result = run_typegen_lab_logic(args)
            self.assertTrue(result)
            mock_print.assert_any_call("type Root struct {\n  Id int `json:\"id\"`\n}")

    def test_run_logic_file_arg(self):
        from unittest.mock import patch, mock_open
        args = argparse.Namespace(file='test.json', name="Root", lang="typescript", json=None)

        with patch("builtins.open", mock_open(read_data='{"test": true}')):
            with patch('builtins.print') as mock_print:
                result = run_typegen_lab_logic(args)
                self.assertTrue(result)
                mock_print.assert_any_call("export interface Root {\n  test: boolean;\n}")







if __name__ == '__main__':
    unittest.main()
