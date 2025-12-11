
import json
import shutil
import subprocess
import sys
from pathlib import Path

# Config
SCRIPT_DIR = Path(__file__).parent
TEST_DIR = Path("tests_output/creation_test_run")
SOURCE_DIR = SCRIPT_DIR / "creation_test"
EXPECTED_OUTPUT = {
    "London": 45.0,
    "New York": 25.0,
    "Paris": 30.0,
    "Tokyo": 100.0
}


def run_agent(agent_type):
    """Run the agent."""
    test_dir_agent = TEST_DIR / agent_type
    if test_dir_agent.exists():
        shutil.rmtree(test_dir_agent)
    test_dir_agent.mkdir(parents=True)

    # Copy input files
    shutil.copy(SOURCE_DIR / "input.csv", test_dir_agent / "input.csv")

    main_py_path = SCRIPT_DIR.parent / "main.py"

    cmd = [
        "python3", str(main_py_path),
        "--project-dir", str(test_dir_agent),
        "--spec", str(SOURCE_DIR / "app_spec.txt"),
        "--agent", agent_type,
        "--max-iterations", "5",  # Give it enough turns to plan, implement, and run
        "--verbose",
        "--verify-creation"
    ]
    print(f"Running {agent_type} agent: {' '.join(cmd)}")
    try:
        # We don't verify return code as agent might hit max iterations
        subprocess.run(cmd, check=False)
    except KeyboardInterrupt:
        print("\nAgent execution interrupted by user. Proceeding to verification...")

    return test_dir_agent


def verify_output(test_dir):
    """Verify the output.json."""
    output_file = test_dir / "output.json"
    if not output_file.exists():
        print(f"FAIL: output.json was not created in {test_dir}.")
        return False

    try:
        data = json.loads(output_file.read_text())
        print(f"Generated Output in {test_dir}: {data}")

        # Check equality with tolerance for floats
        matches = True
        for city, avg in EXPECTED_OUTPUT.items():
            if city not in data:
                print(f"FAIL: Missing city {city}")
                matches = False
            elif abs(data[city] - avg) > 0.1:
                print(f"FAIL: Wrong average for {city}. Expected {avg}, got {data[city]}")
                matches = False

        if len(data) != len(EXPECTED_OUTPUT):
            print(
                f"FAIL: Output has {len(data)} cities, expected {len(EXPECTED_OUTPUT)}")
            matches = False

        if matches:
            print(
                f"SUCCESS: Output for {test_dir.name} matches expected data.")
            return True
        else:
            return False

    except Exception as e:
        print(f"FAIL: Error reading/parsing output in {test_dir}: {e}")
        return False


if __name__ == "__main__":
    if TEST_DIR.exists():
        shutil.rmtree(TEST_DIR)
    TEST_DIR.mkdir(parents=True)

    results = []
    for agent in ["gemini", "cursor"]:
        test_dir = run_agent(agent)
        success = verify_output(test_dir)
        results.append(success)

    if all(results):
        print("\nALL TESTS PASSED")
        sys.exit(0)
    else:
        print("\nSOME TESTS FAILED")
        sys.exit(1)
