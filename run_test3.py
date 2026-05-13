import sys
from pathlib import Path
sys.path.append('.')
from tests.test_tui_jwt import TestJwtLabTab
t = TestJwtLabTab('test_crack_token')
t.setUp()
print(t.tab.crack_token_worker)
