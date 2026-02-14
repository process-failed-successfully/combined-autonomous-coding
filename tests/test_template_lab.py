import unittest
import tempfile
import os
import shutil
from pathlib import Path
import json
import yaml

# Import the module to be tested
from shared.template_lab import TemplateLabManager

class TestTemplateLab(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.manager = TemplateLabManager(Path(self.test_dir))

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_render_basic(self):
        """Test basic template rendering."""
        tpl_path = Path(self.test_dir) / "test.j2"
        tpl_path.write_text("Hello {{ name }}!", encoding="utf-8")

        data_path = Path(self.test_dir) / "data.json"
        data_path.write_text(json.dumps({"name": "World"}), encoding="utf-8")

        result = self.manager.render("test.j2", str(data_path))
        self.assertEqual(result, "Hello World!")

    def test_render_with_overrides(self):
        """Test rendering with variable overrides."""
        tpl_path = Path(self.test_dir) / "test.j2"
        tpl_path.write_text("Hello {{ name }}!", encoding="utf-8")

        data_path = Path(self.test_dir) / "data.json"
        data_path.write_text(json.dumps({"name": "World"}), encoding="utf-8")

        result = self.manager.render("test.j2", str(data_path), overrides={"name": "Universe"})
        self.assertEqual(result, "Hello Universe!")

    def test_render_with_yaml(self):
        """Test rendering with YAML data."""
        tpl_path = Path(self.test_dir) / "test.j2"
        tpl_path.write_text("Value: {{ value }}", encoding="utf-8")

        data_path = Path(self.test_dir) / "data.yaml"
        data_path.write_text("value: 123", encoding="utf-8")

        result = self.manager.render("test.j2", str(data_path))
        self.assertEqual(result, "Value: 123")

    def test_inspect(self):
        """Test inspecting undeclared variables."""
        tpl_path = Path(self.test_dir) / "test.j2"
        tpl_path.write_text("{{ a }} + {{ b }} = {{ c }}", encoding="utf-8")

        vars_found = self.manager.inspect("test.j2")
        self.assertEqual(vars_found, {"a", "b", "c"})

    def test_lint_valid(self):
        """Test linting a valid template."""
        tpl_path = Path(self.test_dir) / "valid.j2"
        tpl_path.write_text("{% if True %}Yes{% endif %}", encoding="utf-8")

        result = self.manager.lint("valid.j2")
        self.assertTrue(result["valid"])

    def test_lint_invalid(self):
        """Test linting an invalid template."""
        tpl_path = Path(self.test_dir) / "invalid.j2"
        tpl_path.write_text("{% if True %}Missing endif", encoding="utf-8")

        result = self.manager.lint("invalid.j2")
        self.assertFalse(result["valid"])
        self.assertIn("Unexpected end of template", result["message"])

    def test_render_absolute_path(self):
        """Test rendering a template outside project dir (using absolute path)."""
        with tempfile.TemporaryDirectory() as other_dir:
            tpl_path = Path(other_dir) / "absolute.j2"
            tpl_path.write_text("Absolute {{ val }}", encoding="utf-8")

            # Using data in standard test dir
            data_path = Path(self.test_dir) / "data.json"
            data_path.write_text(json.dumps({"val": "Works"}), encoding="utf-8")

            result = self.manager.render(str(tpl_path), str(data_path))
            self.assertEqual(result, "Absolute Works")

if __name__ == '__main__':
    unittest.main()
