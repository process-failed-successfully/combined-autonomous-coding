import sys
from tests.test_favicon_lab import test_favicon_manager_generate

import pytest
class DummyArgs:
    def __init__(self):
        pass

def mock_tmp_path():
    from pathlib import Path
    import tempfile
    return Path(tempfile.mkdtemp())

try:
    tmp = mock_tmp_path()
    from PIL import Image
    img_path = tmp / "test_logo.png"
    img = Image.new('RGB', (100, 100), color='red')
    img.save(img_path)

    test_favicon_manager_generate(str(img_path), tmp)
except Exception as e:
    import traceback
    traceback.print_exc()
