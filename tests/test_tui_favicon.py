import pytest
from pathlib import Path
import tempfile

Image = pytest.importorskip("PIL.Image")

from shared.tui import AgentTUI  # noqa: E402


@pytest.fixture
def temp_project_dir():
    from shared.database import init_db
    with tempfile.TemporaryDirectory() as d:
        path = Path(d)
        init_db(path / ".agent_db.sqlite")
        yield path


@pytest.mark.asyncio
async def test_favicon_lab_tui_load_and_generate(temp_project_dir):
    app = AgentTUI(project_dir=temp_project_dir, start_tab="tab-favicon")

    async with app.run_test(headless=True):
        # Verify the tab loaded successfully
        assert app.query_one("#favicon-image-input") is not None

        # Prepare a valid source image
        img_path = temp_project_dir / "logo.png"
        with open(str(img_path), "wb") as f:
            img = Image.new("RGBA", (512, 512), color="red")
            img.save(f, format="PNG")

        app.query_one("#favicon-image-input").value = "logo.png"
        app.query_one("#favicon-output-input").value = "out_dir"

        # Directly call the method to bypass event routing issues in tests
        tab = app.query_one("FaviconLabTab")
        tab.generate_favicons()

        output_text = str(app.query_one("#favicon-output").render())
        assert "Generated" in output_text

        tab.show_html()
        html_output = str(app.query_one("#favicon-output").render())
        assert "apple-touch-icon" in html_output


@pytest.mark.asyncio
async def test_favicon_lab_tui_empty_input(temp_project_dir):
    app = AgentTUI(project_dir=temp_project_dir, start_tab="tab-favicon")

    async with app.run_test(headless=True):
        app.query_one("#favicon-image-input").value = ""

        tab = app.query_one("FaviconLabTab")
        tab.generate_favicons()

        output_text = str(app.query_one("#favicon-output").render())
        assert "Error: Source image path is required" in output_text


@pytest.mark.asyncio
async def test_favicon_lab_tui_invalid_image(temp_project_dir):
    app = AgentTUI(project_dir=temp_project_dir, start_tab="tab-favicon")

    async with app.run_test(headless=True):
        app.query_one("#favicon-image-input").value = "missing.png"

        tab = app.query_one("FaviconLabTab")
        tab.generate_favicons()

        output_text = str(app.query_one("#favicon-output").render())
        assert "Error: Source image 'missing.png' not found" in output_text
