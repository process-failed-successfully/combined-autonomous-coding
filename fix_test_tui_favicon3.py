with open('tests/test_tui_favicon.py', 'r') as f:
    content = f.read()

# Mock textual.work before importing AgentTUI
new_content = """import pytest
import textual

def dummy_work(*args, **kwargs):
    return lambda func: func

textual.work = dummy_work
""" + content

with open('tests/test_tui_favicon.py', 'w') as f:
    f.write(new_content)
