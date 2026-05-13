import sys
from pathlib import Path
sys.path.append('.')
import textual
def dummy_work(*args, **kwargs):
    def decorator(func):
        return func
    return decorator
textual.work = dummy_work
from shared.tui_jwt import JwtLabTab
t = JwtLabTab()
print(t.crack_token_worker)
