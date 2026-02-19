import asyncio
from unittest.mock import AsyncMock
import unittest

class TestAsyncMock(unittest.IsolatedAsyncioTestCase):
    async def test_mock_update(self):
        p1 = AsyncMock()
        p1.returncode = None

        async def wait_p1():
            print("wait_p1 called")
            p1.returncode = 0

        p1.wait.side_effect = wait_p1

        print(f"Before wait: {p1.returncode}")
        await p1.wait()
        print(f"After wait: {p1.returncode}")

        self.assertEqual(p1.returncode, 0)

if __name__ == "__main__":
    unittest.main()
