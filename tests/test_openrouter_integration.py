import json
import shutil
import subprocess
import os
import sys
from pathlib import Path

# Config
SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent.resolve()
TEST_DIR = REPO_ROOT / "tests_output/openrouter_creation_test"
SOURCE_DIR = SCRIPT_DIR / "creation_test"
EXPECTED_OUTPUT = {"London": 45.0, "New York": 25.0, "Paris": 30.0, "Tokyo": 100.0}

def run_openrouter_agent():
    """Run the openrouter agent using mock verification mode."""
    if TEST_DIR.exists():
        shutil.rmtree(TEST_DIR)
    TEST_DIR.mkdir(parents=True)

    # Copy input files
    shutil.copy(SOURCE_DIR / "input.csv", TEST_DIR / "input.csv")
    
    spec_path = SOURCE_DIR / "app_spec.txt"

    # Command to run the agent locally (not via Docker for simplicity in this specific test)
    # Ensure OPENROUTER_API_KEY is dummy but present if required by client init
    env = os.environ.copy()
    if "OPENROUTER_API_KEY" not in env:
        env["OPENROUTER_API_KEY"] = "sk-or-v1-dummy-key-for-test"
    
    cmd = [
        sys.executable,
        str(REPO_ROOT / "main.py"),
        "--project-dir", str(TEST_DIR),
        "--spec", str(spec_path),
        "--agent", "openrouter",
        "--max-iterations", "5",
        "--verbose",
        "--verify-creation"
    ]

    print(f"Running OpenRouter agent: {' '.join(cmd)}")
    subprocess.run(cmd, check=True, env=env)

def verify_output():
    """Verify the output.json."""
    output_file = TEST_DIR / "output.json"
    if not output_file.exists():
        print(f"FAIL: output.json was not created in {TEST_DIR}.")
        return False

    try:
        data = json.loads(output_file.read_text())
        print(f"Generated Output: {data}")

        matches = True
        for city, avg in EXPECTED_OUTPUT.items():
            if city not in data:
                print(f"FAIL: Missing city {city}")
                matches = False
            elif abs(data[city] - avg) > 0.1:
                print(f"FAIL: Wrong average for {city}. Expected {avg}, got {data[city]}")
                matches = False

        if len(data) != len(EXPECTED_OUTPUT):
            print(f"FAIL: Output has {len(data)} cities, expected {len(EXPECTED_OUTPUT)}")
            matches = False

        if matches:
            print("SUCCESS: OpenRouter agent verification passed.")
            return True
        else:
            return False

    except Exception as e:
        print(f"FAIL: Error reading/parsing output: {e}")
        return False

if __name__ == "__main__":
    try:
        run_openrouter_agent()
        if verify_output():
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception as e:
        print(f"Test failed with error: {e}")
        sys.exit(1)
