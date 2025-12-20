import inspect

from agents.gemini.client import GeminiClient
from agents.cursor.client import CursorClient
from agents.gemini.agent import run_agent_session as run_gemini_session
from agents.cursor.agent import run_agent_session as run_cursor_session


def test_client_parity():
    """
    Ensure GeminiClient and CursorClient have consistent interfaces.
    """
    # 1. Check run_command signature
    gemini_sig = inspect.signature(GeminiClient.run_command)
    cursor_sig = inspect.signature(CursorClient.run_command)

    assert (
        "status_callback" in gemini_sig.parameters
    ), "GeminiClient.run_command missing status_callback"
    assert (
        "status_callback" in cursor_sig.parameters
    ), "CursorClient.run_command missing status_callback"

    # Check they are both async
    assert inspect.iscoroutinefunction(GeminiClient.run_command)
    assert inspect.iscoroutinefunction(CursorClient.run_command)


def test_agent_session_parity():
    """
    Ensure agent session runners have parity in arguments.
    """
    gemini_sig = inspect.signature(run_gemini_session)
    cursor_sig = inspect.signature(run_cursor_session)

    # Check common arguments
    common_args = [
        "client",
        "prompt",
        "history",
        "status_callback",
    ]

    for arg in common_args:
        assert arg in gemini_sig.parameters, f"Gemini run_agent_session missing {arg}"
        assert arg in cursor_sig.parameters, f"Cursor run_agent_session missing {arg}"


def test_client_decoupling():
    """
    Ensure Clients do not depend on agent_client (tight coupling check).
    """
    # Simply inspecting init to ensure they only take config
    gemini_init = inspect.signature(GeminiClient.__init__)
    cursor_init = inspect.signature(CursorClient.__init__)

    assert list(gemini_init.parameters.keys()) == [
        "self",
        "config",
    ], "GeminiClient should only take config"
    assert list(cursor_init.parameters.keys()) == [
        "self",
        "config",
    ], "CursorClient should only take config"


if __name__ == "__main__":
    # Allow running directly
    try:
        test_client_parity()
        test_agent_session_parity()
        test_client_decoupling()
        print("Parity Tests Passed!")
    except AssertionError as e:
        print(f"Parity Test Failed: {e}")
        exit(1)
