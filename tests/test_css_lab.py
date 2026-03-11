from shared.css_lab import CssLabManager


def test_css_minify():
    manager = CssLabManager()
    css_content = """
    body {
        /* background color */
        background-color: #fff;
        color: #333;
    }

    .container {
        width: 100%;
        margin: 0 auto;
    }
    """
    minified = manager.minify(css_content)
    # The current minifier collapses spacing after colons as well
    expected = "body{background-color:#fff;color:#333}.container{width:100%;margin:0 auto}"
    assert minified == expected


def test_css_format():
    manager = CssLabManager()
    css_content = "body{background-color:#fff;color:#333;}.container{width:100%;margin:0 auto;}"
    formatted = manager.format(css_content)
    expected = """body {
  background-color:#fff;
  color:#333
}
.container {
  width:100%;
  margin:0 auto
}
"""
    assert formatted == expected


def test_css_lab_cli_minify(capsys):
    from shared.css_lab import run_css_lab_logic
    import argparse
    import io

    args = argparse.Namespace(
        action="minify",
        file=None,
    )

    # Mock stdin
    import sys
    original_stdin = sys.stdin
    sys.stdin = io.StringIO("body { color: red; }")
    # Simulate a tty so it doesn't fail the isatty check or just mock the check
    sys.stdin.isatty = lambda: False

    try:
        run_css_lab_logic(args)
    except SystemExit:
        pass
    finally:
        sys.stdin = original_stdin

    captured = capsys.readouterr()
    assert captured.out.strip() == "body{color:red}"
