import os
import subprocess
import sys
from pathlib import Path


def test_did_you_mean_suggestion():
    """
    Test that running main.py with an invalid command suggests closely matching valid commands.
    """
    root_dir = Path(__file__).parent.parent
    main_script = root_dir / "main.py"

    env = os.environ.copy()
    env["PYTHONPATH"] = str(root_dir)

    # Run with an invalid command that is close to 'json'
    result = subprocess.run(
        [sys.executable, str(main_script), "jsno"],
        capture_output=True,
        text=True,
        env=env
    )

    assert result.returncode == 2

    # Standard argparse output should be there
    assert "invalid choice: 'jsno'" in result.stderr

    # Our new DidYouMean suggestion should be there
    assert "Did you mean:" in result.stderr
    assert "'json'" in result.stderr


def test_did_you_mean_no_suggestion():
    """
    Test that completely bogus commands don't crash and just fall back to no suggestions.
    """
    root_dir = Path(__file__).parent.parent
    main_script = root_dir / "main.py"

    env = os.environ.copy()
    env["PYTHONPATH"] = str(root_dir)

    # Run with a command that has no close matches
    result = subprocess.run(
        [sys.executable, str(main_script), "xyz123thisisnotacommandatall"],
        capture_output=True,
        text=True,
        env=env
    )

    assert result.returncode == 2
    assert "invalid choice: 'xyz123thisisnotacommandatall'" in result.stderr

    # There shouldn't be a suggestion for something completely random
    assert "Did you mean:" not in result.stderr
