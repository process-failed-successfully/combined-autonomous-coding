import json
import shutil
import subprocess
import sys
import os
from pathlib import Path

# Config
SCRIPT_DIR = Path(__file__).parent
TEST_DIR = Path("tests_output/creation_test_run")
SOURCE_DIR = SCRIPT_DIR / "creation_test"
EXPECTED_OUTPUT = {"London": 45.0, "New York": 25.0, "Paris": 30.0, "Tokyo": 100.0}


def run_agent(agent_type):
    """Run the agent using docker-compose."""
    # Resolve paths to absolute to ensure Docker volume mounting works
    test_dir_agent = (TEST_DIR / agent_type).resolve()

    if test_dir_agent.exists():
        shutil.rmtree(test_dir_agent)
    test_dir_agent.mkdir(parents=True)

    # Copy input files
    # SOURCE_DIR needs to be absolute for reliable relative_to calc later,
    # though we can just resolve it
    source_dir_abs = SOURCE_DIR.resolve()
    shutil.copy(source_dir_abs / "input.csv", test_dir_agent / "input.csv")

    repo_root = SCRIPT_DIR.parent.resolve()

    # Calculate spec path inside container
    # The repo is mounted at /app/combined-autonomous-coding (since ..:/app and repo name is combined-autonomous-coding)
    # We strictly adhere to the structure implied by docker-compose.yml

    # Relative path of spec from repo root
    rel_spec_path = (source_dir_abs / "app_spec.txt").relative_to(repo_root)
    container_spec_path = Path("/app/combined-autonomous-coding") / rel_spec_path

    # Docker Compose Command
    # We map the test directory to /workspace
    # Note: WORKSPACE_DIR is needed for docker-compose.yml interpolation, so
    # it must be in the process env.
    cmd = [
        "docker",
        "compose",
        "run",
        "--rm",
        # We don't strictly need -e here if variables are passed via shell env and configured in compose to pass-through,
        # but -e ensures it overrides anything else for the container process.
        # However, for the volume usage in docker-compose.yml, we MUST set it in subprocess env.
        "agent",
        "python3",
        "/app/combined-autonomous-coding/main.py",
        "--project-dir",
        "/workspace",
        "--spec",
        str(container_spec_path),
        "--agent",
        agent_type,
        "--max-iterations",
        "5",  # Give it enough turns to plan, implement, and run
        "--verbose",
        "--verify-creation",
    ]

    # Prepare environment for docker-compose
    cmd_env = os.environ.copy()
    cmd_env["WORKSPACE_DIR"] = str(test_dir_agent)
    cmd_env["PROJECT_NAME"] = f"{agent_type}_test"

    print(f"Running {agent_type} agent via Docker: {' '.join(cmd)}")
    try:
        # We run from repo root so docker-compose can find the YAML file
        subprocess.run(cmd, check=False, cwd=repo_root, env=cmd_env)
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
                print(
                    f"FAIL: Wrong average for {city}. Expected {avg}, got {data[city]}"
                )
                matches = False

        if len(data) != len(EXPECTED_OUTPUT):
            print(
                f"FAIL: Output has {len(data)} cities, expected {len(EXPECTED_OUTPUT)}"
            )
            matches = False

        if matches:
            print(f"SUCCESS: Output for {test_dir.name} matches expected data.")
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
    for agent in ["gemini", "cursor", "openrouter"]:
        test_dir = run_agent(agent)
        success = verify_output(test_dir)
        results.append(success)

    if all(results):
        print("\nALL TESTS PASSED")
        sys.exit(0)
    else:
        print("\nSOME TESTS FAILED")
        sys.exit(1)
