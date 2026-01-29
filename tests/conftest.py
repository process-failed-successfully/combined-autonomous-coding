import sys
import pytest
from unittest.mock import MagicMock

@pytest.fixture(scope="function", autouse=True)
def ensure_rich_not_mocked():
    """Defensively ensure rich is not mocked in sys.modules."""
    for mod_name in ["rich", "rich.console", "rich.markdown", "rich.prompt", "rich.bar"]:
        if mod_name in sys.modules and isinstance(sys.modules[mod_name], MagicMock):
            del sys.modules[mod_name]
    yield
