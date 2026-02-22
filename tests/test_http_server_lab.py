import unittest
import shutil
from pathlib import Path
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
from aiohttp import FormData
from shared.http_server_lab import HttpServerManager

class TestEchoServer(AioHTTPTestCase):
    async def get_application(self):
        self.manager = HttpServerManager()
        return self.manager.create_echo_app()

    @unittest_run_loop
    async def test_echo(self):
        async with self.client.request("POST", "/foo", data="bar") as resp:
            self.assertEqual(resp.status, 200)
            data = await resp.json()
            self.assertEqual(data["method"], "POST")
            self.assertEqual(data["body"], "bar")
            self.assertIn("/foo", data["url"])

class TestUploadServer(AioHTTPTestCase):
    def setUp(self):
        self.temp_dir = Path("./test_http_lab_upload_temp")
        self.temp_dir.mkdir(exist_ok=True)
        super().setUp()

    def tearDown(self):
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
        super().tearDown()

    async def get_application(self):
        self.manager = HttpServerManager()
        return self.manager.create_upload_app(self.temp_dir)

    @unittest_run_loop
    async def test_upload_file(self):
        data = FormData()
        data.add_field('file', b'test-content', filename='test.txt')

        async with self.client.request("POST", "/", data=data) as resp:
            self.assertEqual(resp.status, 200)
            json_resp = await resp.json()
            self.assertEqual(len(json_resp['files']), 1)
            self.assertEqual(json_resp['files'][0]['filename'], 'test.txt')
            self.assertEqual(json_resp['files'][0]['size'], 12)

        file_path = self.temp_dir / 'test.txt'
        self.assertTrue(file_path.exists())
        self.assertEqual(file_path.read_bytes(), b'test-content')

    @unittest_run_loop
    async def test_upload_invalid_content_type(self):
        async with self.client.request("POST", "/", data="raw data") as resp:
            self.assertEqual(resp.status, 400)

class TestStaticServer(AioHTTPTestCase):
    def setUp(self):
        self.temp_dir = Path("./test_http_lab_static_temp")
        self.temp_dir.mkdir(exist_ok=True)
        (self.temp_dir / "index.html").write_text("<html>Index</html>")
        (self.temp_dir / "other.txt").write_text("Text content")
        super().setUp()

    def tearDown(self):
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
        super().tearDown()

    async def get_application(self):
        self.manager = HttpServerManager()
        return self.manager.create_static_app(self.temp_dir)

    @unittest_run_loop
    async def test_get_index(self):
        async with self.client.request("GET", "/") as resp:
            self.assertEqual(resp.status, 200)
            text = await resp.text()
            self.assertIn("Index", text)

    @unittest_run_loop
    async def test_get_file(self):
        async with self.client.request("GET", "/other.txt") as resp:
            self.assertEqual(resp.status, 200)
            text = await resp.text()
            self.assertEqual(text, "Text content")

if __name__ == '__main__':
    unittest.main()
