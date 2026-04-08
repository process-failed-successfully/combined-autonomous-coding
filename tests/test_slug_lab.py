import pytest
from unittest.mock import patch, MagicMock
from io import StringIO
import sys
import argparse

from shared.slug_lab import SlugManager, run_slug_lab_logic


class TestSlugLab:
    def test_slugify_normal_string(self):
        manager = SlugManager()
        assert manager.slugify("Hello World") == "hello-world"
        assert manager.slugify("This is a test!") == "this-is-a-test"

    def test_slugify_unicode_string(self):
        manager = SlugManager()
        assert manager.slugify("Héllo Wörld") == "hello-world"
        assert manager.slugify("Café au lait") == "cafe-au-lait"

    def test_slugify_edge_cases(self):
        manager = SlugManager()
        assert manager.slugify("") == ""
        assert manager.slugify("---") == ""
        assert manager.slugify("  Spaces   and   hyphens --- ") == "spaces-and-hyphens"
        assert manager.slugify("123 !@# ABC") == "123-abc"
        assert manager.slugify("Already-a-slug") == "already-a-slug"

    def test_run_slug_lab_logic_success(self):
        args = argparse.Namespace(text="Hello World!")
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = run_slug_lab_logic(args)
            assert result is True
            assert mock_stdout.getvalue().strip() == "hello-world"

    def test_run_slug_lab_logic_missing_text(self):
        args = argparse.Namespace(text=None)
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            result = run_slug_lab_logic(args)
            assert result is False
            assert "Error: 'text' argument is required." in mock_stderr.getvalue()

    def test_tui_instantiation(self):
        pytest.importorskip("textual")
        from textual.app import App
        from shared.tui_slug import SlugLabTab

        class TestApp(App):
            def compose(self):
                yield SlugLabTab()

        app = TestApp()
        assert app is not None
