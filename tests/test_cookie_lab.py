import subprocess
import sys
import os
from shared.cookie_lab import CookieLabManager


def test_cookie_parse():
    manager = CookieLabManager()

    # Test valid parsing
    res = manager.parse_cookie("session_id=12345; Path=/; Secure; HttpOnly; SameSite=Lax")
    assert "error" not in res
    assert "cookies" in res
    assert "session_id" in res["cookies"]

    morsel = res["cookies"]["session_id"]
    assert morsel["value"] == "12345"
    assert morsel["path"] == "/"
    assert morsel["secure"] is True
    assert morsel["httponly"] is True
    assert morsel["samesite"] == "Lax"


def test_cookie_generate():
    manager = CookieLabManager()

    # Test cookie generation
    res = manager.generate_cookie("user_id", "abc", path="/app", secure=True, httponly=True)
    assert "set_cookie" in res
    output = res["set_cookie"]

    assert "user_id=abc" in output
    assert "Path=/app" in output
    assert "Secure" in output
    assert "HttpOnly" in output


def test_cookie_lab_cli():
    env = os.environ.copy()
    if 'PYTHONPATH' in env:
        env['PYTHONPATH'] = f".{os.pathsep}{env['PYTHONPATH']}"
    else:
        env['PYTHONPATH'] = "."

    # Test parse via CLI
    res = subprocess.run(
        [sys.executable, "main.py", "cookie-lab", "parse", "--string", "test_key=test_val"],
        env=env,
        capture_output=True, text=True
    )
    assert res.returncode == 0
    assert "test_key" in res.stdout
    assert "test_val" in res.stdout

    # Test generate via CLI
    res2 = subprocess.run(
        [sys.executable, "main.py", "cookie-lab", "generate", "--key", "session", "--value", "xyz", "--secure"],
        env=env,
        capture_output=True, text=True
    )
    assert res2.returncode == 0
    assert "session=xyz" in res2.stdout
    assert "Secure" in res2.stdout
