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
            app.query_one("#btn_convert").press()
            await pilot.pause()

            # Verify output
            self.assertIn("nginx", tab.output_area.text)
            self.assertIn("ports:", tab.output_area.text)


if __name__ == '__main__':
    unittest.main()
