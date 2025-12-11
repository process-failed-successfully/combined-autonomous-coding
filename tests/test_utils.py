"""
Tests for Shared Utilities -> process_response_blocks
=====================================================
"""

import unittest
from unittest.mock import AsyncMock, patch
from pathlib import Path
from shared.utils import process_response_blocks

# Mock data
MOCK_BASH_BLOCK = """
Here is a command:
```bash
echo "hello"
```
"""

MOCK_WRITE_BLOCK = """
I will write a file:
```write:test.txt
content
```
"""

MOCK_MIXED_BLOCKS = """
First write:
```write:hello.py
print("hello")
```

Then run:
```bash
python3 hello.py
```
"""

MOCK_BROKEN_JSON_BLOCK = """
```json
{
 "key": "value"
```
"""


class TestProcessResponseBlocks(unittest.IsolatedAsyncioTestCase):

    async def test_process_bash_block(self):
        project_dir = Path("/tmp/test_project")

        with patch("shared.utils.execute_bash_block", new_callable=AsyncMock) as mock_bash:
            mock_bash.return_value = "hello\n"

            log, actions = await process_response_blocks(MOCK_BASH_BLOCK, project_dir)

            self.assertIn("Ran Bash: echo \"hello\"", actions)
            self.assertIn("> echo \"hello\"", log)
            mock_bash.assert_called_once_with(
                'echo "hello"', project_dir, timeout=120.0)

    async def test_process_write_block(self):
        project_dir = Path("/tmp/test_project")

        with patch("shared.utils.execute_write_block") as mock_write:
            mock_write.return_value = "Successfully wrote test.txt"

            log, actions = await process_response_blocks(MOCK_WRITE_BLOCK, project_dir)

            self.assertIn("Wrote File: test.txt", actions)
            mock_write.assert_called_once_with(
                'test.txt', 'content', project_dir)

    async def test_process_mixed_blocks(self):
        project_dir = Path("/tmp/test_project")

        with patch("shared.utils.execute_write_block") as mock_write, \
                patch("shared.utils.execute_bash_block", new_callable=AsyncMock) as mock_bash:

            mock_write.return_value = "Success"
            mock_bash.return_value = "Output"

            log, actions = await process_response_blocks(MOCK_MIXED_BLOCKS, project_dir)

            self.assertEqual(len(actions), 2)
            self.assertIn("Wrote File: hello.py", actions)
            self.assertIn("Ran Bash: python3 hello.py", actions)

            mock_write.assert_called_once()
            mock_bash.assert_called_once()

    async def test_process_malformed_block(self):
        project_dir = Path("/tmp/test_project")

        log, actions = await process_response_blocks(MOCK_BROKEN_JSON_BLOCK, project_dir)

        # Should ignore unknown blocks
        self.assertEqual(len(actions), 0)


if __name__ == "__main__":
    unittest.main()
