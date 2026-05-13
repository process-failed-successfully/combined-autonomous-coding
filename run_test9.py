import sys
from pathlib import Path
sys.path.append('.')
from tests.test_tui_jwt import TestJwtLabTab
from unittest.mock import MagicMock
t = TestJwtLabTab('test_crack_token')
t.setUp()
t.tab.crack_token_worker('foo', 'bar')
