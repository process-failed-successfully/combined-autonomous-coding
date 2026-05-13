import sys
from pathlib import Path
sys.path.append('.')
from tests.test_tui_jwt import TestJwtLabTab
import inspect
from shared.tui_jwt import JwtLabTab
print(inspect.getsource(JwtLabTab.crack_token_worker))
