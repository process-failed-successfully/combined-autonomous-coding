import pytest
from pathlib import Path
from shared.svg_lab import SvgLabManager

@pytest.fixture
def svg_manager():
    return SvgLabManager()

def test_validate_valid_svg(tmp_path, svg_manager):
    svg_file = tmp_path / "valid.svg"
    svg_file.write_text("<svg xmlns=\"http://www.w3.org/2000/svg\"><circle cx=\"50\" cy=\"50\" r=\"40\" /></svg>")

    assert svg_manager.validate(svg_file) is True

def test_validate_invalid_svg(tmp_path, svg_manager):
    svg_file = tmp_path / "invalid.svg"
    svg_file.write_text("<not-svg><foo/></not-svg>")

    assert svg_manager.validate(svg_file) is False

def test_minify_svg_removes_whitespace(tmp_path, svg_manager):
    svg_file = tmp_path / "to_minify.svg"
    original_svg = """
    <svg xmlns="http://www.w3.org/2000/svg">
        <!-- This is a comment -->
        <circle cx="50" cy="50" r="40" />
    </svg>
    """
    svg_file.write_text(original_svg)
    out_file = tmp_path / "minified.svg"

    assert svg_manager.minify(svg_file, out_file) is True

    minified = out_file.read_text()
    # It should not have the comment
    assert "This is a comment" not in minified
    # It should not have multiple spaces
    assert "    " not in minified
    # It should compress lines
    assert ">\n" not in minified
