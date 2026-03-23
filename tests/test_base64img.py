import unittest
import base64
import os
import tempfile
from shared.base64img_lab import Base64ImgLabManager

class TestBase64ImgLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = Base64ImgLabManager()
        self.test_data = b"fake image data"
        self.test_base64 = base64.b64encode(self.test_data).decode('utf-8')

        # Create a temporary file
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_file.write(self.test_data)
        self.temp_file.close()

    def tearDown(self):
        if os.path.exists(self.temp_file.name):
            os.remove(self.temp_file.name)

    def test_encode_image_success(self):
        result = self.manager.encode_image(self.temp_file.name)
        self.assertTrue(result["success"])
        self.assertEqual(result["result"], self.test_base64)

    def test_encode_image_file_not_found(self):
        result = self.manager.encode_image("nonexistent_file.png")
        self.assertFalse(result["success"])
        self.assertIn("File not found", result["error"])

    def test_decode_image_success(self):
        output_file = tempfile.NamedTemporaryFile(delete=False)
        output_file.close()

        result = self.manager.decode_image(self.test_base64, output_file.name)
        self.assertTrue(result["success"])
        self.assertEqual(result["result"], output_file.name)

        with open(output_file.name, "rb") as f:
            data = f.read()
            self.assertEqual(data, self.test_data)

        os.remove(output_file.name)

    def test_decode_image_with_data_uri(self):
        output_file = tempfile.NamedTemporaryFile(delete=False)
        output_file.close()

        data_uri = f"data:image/png;base64,{self.test_base64}"
        result = self.manager.decode_image(data_uri, output_file.name)
        self.assertTrue(result["success"])
        self.assertEqual(result["result"], output_file.name)

        with open(output_file.name, "rb") as f:
            data = f.read()
            self.assertEqual(data, self.test_data)

        os.remove(output_file.name)

    def test_decode_image_empty_input(self):
        result = self.manager.decode_image("", "output.png")
        self.assertFalse(result["success"])
        self.assertIn("cannot be empty", result["error"])

    def test_decode_image_no_output_path(self):
        result = self.manager.decode_image(self.test_base64, "")
        self.assertFalse(result["success"])
        self.assertIn("Output path must be provided", result["error"])

    def test_decode_image_invalid_base64(self):
        output_file = tempfile.NamedTemporaryFile(delete=False)
        output_file.close()

        result = self.manager.decode_image("not_valid_base64!@#", output_file.name)
        self.assertFalse(result["success"])
        self.assertIn("Error decoding", result["error"])

        os.remove(output_file.name)

import unittest.mock as mock
from textual.app import App
from shared.tui_base64img import Base64ImgLabTab

class DummyApp(App):
    def compose(self):
        yield Base64ImgLabTab()

class TestBase64ImgLabTab(unittest.IsolatedAsyncioTestCase):
    async def test_encode_success(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            # We mock the manager
            tab = app.query_one(Base64ImgLabTab)
            with mock.patch.object(tab.manager, 'encode_image', return_value={"success": True, "result": "base64output"}):
                # Set input
                await pilot.click("#input-encode-path")
                await pilot.press(*list("dummy.png"))

                # Click encode
                await pilot.click("#btn-encode")

                # Check output
                output = tab.query_one("#output-base64").text
                status = tab.query_one("#lbl-encode-status").renderable

                self.assertEqual(output, "base64output")
                self.assertIn("successfully encoded", str(status))

    async def test_encode_empty_input(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            tab = app.query_one(Base64ImgLabTab)
            # Click encode without typing
            await pilot.click("#btn-encode")
            status = tab.query_one("#lbl-encode-status").renderable
            self.assertIn("Please provide a file path", str(status))

    async def test_decode_success(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            tab = app.query_one(Base64ImgLabTab)
            with mock.patch.object(tab.manager, 'decode_image', return_value={"success": True, "result": "out.png"}):
                # We need to manually update text area since typing might be tricky in tests
                tab.query_one("#input-decode-base64").text = "base64string"

                await pilot.click("#input-decode-output")
                await pilot.press(*list("out.png"))

                await pilot.click("#btn-decode")
                status = tab.query_one("#lbl-decode-status").renderable

                self.assertIn("successfully saved to out.png", str(status))

    async def test_decode_empty_input(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            tab = app.query_one(Base64ImgLabTab)
            # Click decode without typing
            await pilot.click("#btn-decode")
            status = tab.query_one("#lbl-decode-status").renderable
            self.assertIn("Please provide a Base64 string", str(status))
