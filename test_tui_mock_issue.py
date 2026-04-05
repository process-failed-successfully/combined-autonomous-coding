import pytest
from unittest.mock import patch
import shared.tui

@patch("shared.tui.scan_project")
def test_mock(mock_scan):
    print("mock_scan called:", mock_scan.called)

test_mock()
