import unittest
from pathlib import Path

from textual.app import App
from shared.run2compose_lab import Run2ComposeManager


class TestRun2ComposeManager(unittest.TestCase):
    def setUp(self):
        self.manager = Run2ComposeManager()

    def test_parse_simple(self):
        cmd = "docker run -d --name web -p 80:80 nginx"
        result = self.manager.parse(cmd)

        self.assertIn("success", result)
        compose = result["compose"]

        self.assertEqual(compose["version"], "3.8")
        self.assertIn("web", compose["services"])
        web = compose["services"]["web"]

        self.assertEqual(web["image"], "nginx")
        self.assertEqual(web["ports"], ["80:80"])

    def test_parse_complex(self):
        cmd = "docker run --rm -it -v /host:/container -e ENV_VAR=value --network mynet myimage arg1 arg2"
        result = self.manager.parse(cmd)

        self.assertIn("success", result)
        compose = result["compose"]

        app = compose["services"]["app"]
        self.assertEqual(app["image"], "myimage")
        self.assertEqual(app["volumes"], ["/host:/container"])
        self.assertEqual(app["environment"], ["ENV_VAR=value"])
        self.assertEqual(app["command"], ["arg1", "arg2"])

        # Test network handling at top level
        self.assertIn("mynet", compose["networks"])

    def test_parse_docker_container_run(self):
        cmd = "docker container run -d nginx"
        result = self.manager.parse(cmd)
        self.assertIn("success", result)
        self.assertEqual(result["compose"]["services"]["app"]["image"], "nginx")

    def test_parse_empty(self):
        result = self.manager.parse("")
        self.assertIn("error", result)

        result2 = self.manager.parse("docker run")
        self.assertIn("error", result2)

    def test_parse_shlex_error(self):
        result = self.manager.parse("docker run -d nginx 'unclosed quote")
        self.assertIn("error", result)

    def test_parse_no_image(self):
        result = self.manager.parse("docker run -d -p 80:80")
        self.assertIn("error", result)

    def test_parse_additional_flags(self):
        cmd = "docker run --restart always --env-file .env -u 1000:1000 -w /app --privileged nginx"
        result = self.manager.parse(cmd)
        self.assertIn("success", result)
        app = result["compose"]["services"]["app"]
        self.assertEqual(app["restart"], "always")
        self.assertEqual(app["env_file"], [".env"])
        self.assertEqual(app["user"], "1000:1000")
        self.assertEqual(app["working_dir"], "/app")
        self.assertTrue(app["privileged"])


class TestRun2ComposeCLI(unittest.TestCase):
    def test_run_logic_no_command(self):
        from shared.run2compose_lab import run_run2compose_lab_logic
        import argparse
        args = argparse.Namespace(action="convert", command_str=None)
        with self.assertRaises(SystemExit) as cm:
            run_run2compose_lab_logic(args)
        self.assertEqual(cm.exception.code, 1)

    def test_run_logic_invalid_command(self):
        from shared.run2compose_lab import run_run2compose_lab_logic
        import argparse
        args = argparse.Namespace(action="convert", command_str="docker run", output=None)
        with self.assertRaises(SystemExit) as cm:
            run_run2compose_lab_logic(args)
        self.assertEqual(cm.exception.code, 1)

    def test_run_logic_success_print(self):
        from shared.run2compose_lab import run_run2compose_lab_logic
        import argparse
        from unittest.mock import patch
        import io
        args = argparse.Namespace(action="convert", command_str="docker run nginx", output=None)
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout, patch('sys.exit') as mock_exit:
            run_run2compose_lab_logic(args)
            mock_exit.assert_called_once_with(0)
            self.assertIn("nginx", mock_stdout.getvalue())

    def test_run_logic_success_output_file(self):
        from shared.run2compose_lab import run_run2compose_lab_logic
        import argparse
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_name = tmp.name

        args = argparse.Namespace(action="convert", command_str="docker run nginx", output=tmp_name)
        try:
            with self.assertRaises(SystemExit) as cm:
                run_run2compose_lab_logic(args)
            self.assertEqual(cm.exception.code, 0)
            with open(tmp_name, 'r') as f:
                content = f.read()
            self.assertIn("nginx", content)
        finally:
            os.remove(tmp_name)

    def test_run_logic_output_file_error(self):
        from shared.run2compose_lab import run_run2compose_lab_logic
        import argparse
        args = argparse.Namespace(action="convert", command_str="docker run nginx", output="/nonexistent/dir/file.yml")
        with self.assertRaises(SystemExit) as cm:
            run_run2compose_lab_logic(args)
        self.assertEqual(cm.exception.code, 1)

    def test_run_logic_invalid_action(self):
        from shared.run2compose_lab import run_run2compose_lab_logic
        import argparse
        args = argparse.Namespace(action="unknown")
        with self.assertRaises(SystemExit) as cm:
            run_run2compose_lab_logic(args)
        self.assertEqual(cm.exception.code, 1)


class DummyApp(App[None]):
    def __init__(self, project_dir):
        super().__init__()
        self.project_dir = project_dir

    def compose(self):
        from shared.tui_run2compose import Run2ComposeLabTab
        yield Run2ComposeLabTab(self.project_dir)


class TestRun2ComposeLabTab(unittest.IsolatedAsyncioTestCase):
    async def test_tab_mount(self):
        app = DummyApp(project_dir=Path("."))
        async with app.run_test() as pilot:
            from shared.tui_run2compose import Run2ComposeLabTab
            tab = app.query_one(Run2ComposeLabTab)
            self.assertIsNotNone(tab)
            self.assertIn("docker run", tab.input_area.text)

            # Click convert button
            await pilot.click("#btn_convert")

            # Verify output
            self.assertIn("nginx", tab.output_area.text)
            self.assertIn("ports:", tab.output_area.text)

    async def test_tab_empty_input(self):
        app = DummyApp(project_dir=Path("."))
        async with app.run_test() as pilot:
            from shared.tui_run2compose import Run2ComposeLabTab
            tab = app.query_one(Run2ComposeLabTab)
            tab.input_area.text = "   "
            await pilot.click("#btn_convert")
            self.assertIn("Error: Input is empty.", tab.output_area.text)

    async def test_tab_parsing_error(self):
        app = DummyApp(project_dir=Path("."))
        async with app.run_test() as pilot:
            from shared.tui_run2compose import Run2ComposeLabTab
            tab = app.query_one(Run2ComposeLabTab)
            tab.input_area.text = "docker run -p 80:80"  # no image
            await pilot.click("#btn_convert")
            self.assertIn("No image specified.", tab.output_area.text)

    async def test_tab_yaml_exception(self):
        app = DummyApp(project_dir=Path("."))
        async with app.run_test() as pilot:
            from shared.tui_run2compose import Run2ComposeLabTab
            from unittest.mock import patch
            tab = app.query_one(Run2ComposeLabTab)
            tab.input_area.text = "docker run nginx"
            with patch('shared.run2compose_lab.Run2ComposeManager.to_yaml', side_effect=Exception("YAML Error")):
                await pilot.click("#btn_convert")
            self.assertIn("Error generating YAML: YAML Error", tab.output_area.text)


if __name__ == '__main__':
    unittest.main()
