import sys
from pathlib import Path
sys.path.append('.')
from tests.test_tui_jwt import TestJwtLabTab
from unittest.mock import MagicMock
t = TestJwtLabTab('test_crack_token')
t.setUp()

mock_app = MagicMock()
def call_from_thread_mock(func, *args, **kwargs):
    func(*args, **kwargs)
mock_app.call_from_thread = call_from_thread_mock
type(t.tab).app = mock_app

print(t.mock_manager.crack_token.call_count)
t.tab.crack_token_worker("token.part.three", "wordlist.txt")
print(t.mock_manager.crack_token.call_count)
