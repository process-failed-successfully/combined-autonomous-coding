import unittest
from unittest.mock import AsyncMock, patch
import asyncio
import os
import sys

# Mocking the manager class to isolate the issue
class MockManager:
    def __init__(self):
        self.processes = {}

    async def start_process(self, name, command):
        self.processes[name] = await asyncio.create_subprocess_shell(command)

    async def stop_process(self, name):
        proc = self.processes[name]
        if sys.platform != "win32":
            # This is where we expect it to fail if pid is a Mock
            try:
                os.killpg(os.getpgid(proc.pid), 15)
            except TypeError as e:
                print(f"Caught expected TypeError: {e}")
                raise

class TestProcLab(unittest.IsolatedAsyncioTestCase):
    @patch("asyncio.create_subprocess_shell", new_callable=AsyncMock)
    async def test_stop_process_repro(self, mock_subprocess):
        mock_proc = AsyncMock()
        mock_proc.returncode = None
        # WE INTENTIONALLY DO NOT SET PID HERE to see if it fails
        # mock_proc.pid = 12345
        mock_subprocess.return_value = mock_proc

        manager = MockManager()
        await manager.start_process("test", "echo test")

        # This should fail on Linux
        try:
            await manager.stop_process("test")
        except TypeError:
            pass # Expected
        except Exception as e:
            self.fail(f"Unexpected exception: {e}")

if __name__ == "__main__":
    unittest.main()
