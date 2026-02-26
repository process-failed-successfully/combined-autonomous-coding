import unittest
import shutil
from pathlib import Path

# Attempt to import aiohttp and shared module
try:
    from aiohttp.test_utils import AioHTTPTestCase
    from aiohttp import FormData
    from shared.http_server_lab import HttpServerManager
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

    # Mock classes for when aiohttp is missing, so collection doesn't fail
    class AioHTTPTestCase(unittest.IsolatedAsyncioTestCase):
        pass

    class FormData:
        pass


@unittest.skipUnless(AIOHTTP_AVAILABLE, "aiohttp or shared.http_server_lab not available")
class TestEchoServer(AioHTTPTestCase):
    async def get_application(self):
        self.manager = HttpServerManager()
        return self.manager.create_echo_app()

    async def test_echo(self):
        async with self.client.request("POST", "/foo", data="bar") as resp:
            self.assertEqual(resp.status, 200)
            data = await resp.json()
            self.assertEqual(data["method"], "POST")
            self.assertEqual(data["body"], "bar")
            self.assertIn("/foo", data["url"])


@unittest.skipUnless(AIOHTTP_AVAILABLE, "aiohttp or shared.http_server_lab not available")
class TestUploadServer(AioHTTPTestCase):
    def setUp(self):
        if not AIOHTTP_AVAILABLE:
            self.skipTest("aiohttp not available")
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

    async def test_upload_invalid_content_type(self):
        async with self.client.request("POST", "/", data="raw data") as resp:
            self.assertEqual(resp.status, 400)


@unittest.skipUnless(AIOHTTP_AVAILABLE, "aiohttp or shared.http_server_lab not available")
class TestStaticServer(AioHTTPTestCase):
    def setUp(self):
        if not AIOHTTP_AVAILABLE:
            self.skipTest("aiohttp not available")
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

    async def test_get_index(self):
        async with self.client.request("GET", "/") as resp:
            self.assertEqual(resp.status, 200)
            text = await resp.text()
            self.assertIn("Index", text)

    async def test_get_file(self):
        async with self.client.request("GET", "/other.txt") as resp:
            self.assertEqual(resp.status, 200)
            text = await resp.text()
            self.assertEqual(text, "Text content")


if __name__ == '__main__':
    unittest.main()
