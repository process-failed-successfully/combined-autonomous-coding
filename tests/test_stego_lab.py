import pytest
import os
import tempfile
from unittest.mock import patch
from shared.stego_lab import StegoManager, run_stego_lab_logic

try:
    from PIL import Image
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False


class DummyArgs:
    def __init__(self, action, image=None, message=None, output=None):
        self.action = action
        self.image = image
        self.message = message
        self.output = output


@pytest.fixture
def temp_image():
    """Fixture to create a temporary image for testing."""
    if not HAS_PILLOW:
        pytest.skip("Pillow is required for Stego Lab tests.")

    fd, path = tempfile.mkstemp(suffix=".png")
    os.close(fd)

    img = Image.new('RGB', (100, 100), color='white')
    img.save(path)

    yield path

    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def temp_output():
    """Fixture to create a temporary output path."""
    fd, path = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.remove(path)


@pytest.mark.skipif(not HAS_PILLOW, reason="Pillow is required for Stego Lab tests.")
def test_stego_manager_hide_extract(temp_image, temp_output):
    manager = StegoManager()
    secret_message = "Agentic AI is awesome!"

    # Hide message
    success = manager.hide(temp_image, secret_message, temp_output)
    assert success is True

    # Extract message
    extracted_message = manager.extract(temp_output)
    assert extracted_message == secret_message


@pytest.mark.skipif(not HAS_PILLOW, reason="Pillow is required for Stego Lab tests.")
def test_stego_manager_message_too_large(temp_image, temp_output):
    manager = StegoManager()
    # Image is 100x100 = 10000 pixels. Each pixel has 3 LSBs = 30000 bits capacity.
    # Max size = ~3750 characters.
    huge_message = "A" * 4000

    with pytest.raises(ValueError, match="Message is too large to fit in this image"):
        manager.hide(temp_image, huge_message, temp_output)


@pytest.mark.skipif(not HAS_PILLOW, reason="Pillow is required for Stego Lab tests.")
def test_stego_manager_extract_no_message(temp_image):
    manager = StegoManager()
    with pytest.raises(ValueError, match="No hidden message found or corrupted data"):
        manager.extract(temp_image)


@patch('sys.exit')
@patch('builtins.print')
def test_run_stego_lab_logic_hide(mock_print, mock_exit, temp_image, temp_output):
    if not HAS_PILLOW:
        pytest.skip("Pillow is required for Stego Lab tests.")

    args = DummyArgs(action="hide", image=temp_image, message="Secret", output=temp_output)
    run_stego_lab_logic(args)
    mock_exit.assert_called_with(0)
    assert os.path.exists(temp_output)


@patch('sys.exit')
@patch('builtins.print')
def test_run_stego_lab_logic_extract(mock_print, mock_exit, temp_image, temp_output):
    if not HAS_PILLOW:
        pytest.skip("Pillow is required for Stego Lab tests.")

    manager = StegoManager()
    manager.hide(temp_image, "Secret", temp_output)

    args = DummyArgs(action="extract", image=temp_output)
    run_stego_lab_logic(args)
    mock_exit.assert_called_with(0)
