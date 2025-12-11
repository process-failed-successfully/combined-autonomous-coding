"""
End-to-End Verification Script
==============================

Simulates agent runs to verify basic functionality.
"""

from shared.config import Config
from agents.cursor.agent import CursorClient
from agents.gemini.agent import GeminiClient
import asyncio
import shutil
import sys
from pathlib import Path

# Adjust path to include project root
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))


TEST_DIR = Path("tests_output/creation_test")
SPEC_FILE = project_root / "agents/gemini/prompts/app_spec.txt"


def setup():
    if TEST_DIR.exists():
        shutil.rmtree(TEST_DIR)
    TEST_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Test directory created at {TEST_DIR}")


async def test_gemini_instantiation():
    print("Testing Gemini Client Instantiation...")
    config = Config(project_dir=TEST_DIR,
                    agent_type="gemini", spec_file=SPEC_FILE)
    client = GeminiClient(config)
    assert client.config.model == "auto"
    print("PASS: Gemini Client instantiated correctly.")


async def test_cursor_instantiation():
    print("Testing Cursor Client Instantiation...")
    config = Config(project_dir=TEST_DIR,
                    agent_type="cursor", spec_file=SPEC_FILE)
    client = CursorClient(config)
    assert client.config.model == "auto"
    print("PASS: Cursor Client instantiated correctly.")


async def main():
    setup()
    await test_gemini_instantiation()
    await test_cursor_instantiation()

    print("\nAll basic instantiation tests passed.")

if __name__ == "__main__":
    asyncio.run(main())
