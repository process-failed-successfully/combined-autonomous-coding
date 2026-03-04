import unittest
from pathlib import Path
from shared.tui_bencode import BencodeLabTab


class TestBencodeTui(unittest.IsolatedAsyncioTestCase):
    async def test_bencode_tab_instantiation(self):
        tab = BencodeLabTab(project_dir=Path("."))
        self.assertIsNotNone(tab)


if __name__ == "__main__":
    unittest.main()
