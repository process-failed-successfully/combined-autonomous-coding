from shared.html2md_lab import HtmlToMarkdownParser, Html2MdManager, run_html2md_logic
import argparse
import tempfile
import pytest

def test_convert():
    manager = Html2MdManager()

    # Headers
    assert manager.convert("<h1>H1</h1>") == "# H1"
    assert manager.convert("<h6>H6</h6>") == "###### H6"

    # Text formatting
    assert manager.convert("<p>This is <b>bold</b>, <strong>strong</strong>, <i>italic</i>, and <em>em</em>.</p>") == "This is **bold**, **strong**, *italic*, and *em*."

    # Links
    assert manager.convert("<a href='https://example.com'>Link</a>") == "[Link](https://example.com)"

    # Lists
    assert manager.convert("<ul><li>One</li><li>Two</li></ul>") == "- One\n- Two"
    assert manager.convert("<ol><li>First</li><li>Second</li></ol>") == "1. First\n2. Second"

    # Code blocks
    assert manager.convert("<code>inline</code>") == "`inline`"
    assert manager.convert("<pre><code>block\nof\ncode</code></pre>") == "```\nblock\nof\ncode\n```"

    # Blockquotes
    assert manager.convert("<blockquote>Quote</blockquote>") == "> Quote"

def test_cli_logic_text():
    args = argparse.Namespace(text="<p>Test</p>", file=None, output=None, action="convert")
    assert run_html2md_logic(args) == True

def test_cli_logic_file():
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("<p>File Content</p>")
        f.close()

        args = argparse.Namespace(text=None, file=f.name, output=None, action="convert")
        assert run_html2md_logic(args) == True

def test_cli_logic_output():
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f_in, tempfile.NamedTemporaryFile(mode="w", delete=False) as f_out:
        f_in.write("<p>File Content</p>")
        f_in.close()
        f_out.close()

        args = argparse.Namespace(text=None, file=f_in.name, output=f_out.name, action="convert")
        assert run_html2md_logic(args) == True

        with open(f_out.name, 'r') as f_read:
            assert f_read.read() == "File Content"
