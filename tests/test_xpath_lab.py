from unittest.mock import patch
import pytest
import argparse
import io

from shared.xpath_lab import XpathLabManager, run_xpath_lab_logic


@pytest.fixture
def manager():
    return XpathLabManager()


def test_evaluate_success(manager):
    xml_data = """<root>
        <book id="1">
            <title>Book A</title>
            <author>Author A</author>
        </book>
        <book id="2">
            <title>Book B</title>
            <author>Author B</author>
        </book>
    </root>"""

    result = manager.evaluate(xml_data, ".//book")
    assert result["success"] is True
    assert len(result["result"]) == 2
    assert result["result"][0]["tag"] == "book"
    assert result["result"][0]["attributes"]["id"] == "1"

    # Test text retrieval
    result2 = manager.evaluate(xml_data, ".//title")
    assert result2["success"] is True
    assert len(result2["result"]) == 2
    assert result2["result"][0]["text"] == "Book A"


def test_evaluate_empty_input(manager):
    result = manager.evaluate("", ".//book")
    assert result["success"] is False
    assert "Empty XML data" in result["error"]


def test_evaluate_empty_expression(manager):
    result = manager.evaluate("<root></root>", "")
    assert result["success"] is False
    assert "Empty XPath expression" in result["error"]


def test_evaluate_invalid_xml(manager):
    result = manager.evaluate("<root><unclosed>", ".//book")
    assert result["success"] is False
    assert "Invalid XML" in result["error"]


def test_evaluate_invalid_xpath(manager):
    xml_data = "<root></root>"
    result = manager.evaluate(xml_data, "////")
    assert result["success"] is False
    # Depending on ElementTree version, it throws SyntaxError
    assert "Invalid XPath expression" in result["error"]


@patch('sys.stdout', new_callable=io.StringIO)
def test_cli_evaluate_file(mock_stdout, tmp_path):
    # Create temp file
    test_file = tmp_path / "test.xml"
    test_file.write_text("<root><item>Hello</item></root>")

    args = argparse.Namespace(input=str(test_file), expression=".//item")
    success = run_xpath_lab_logic(args)

    assert success is True
    output = mock_stdout.getvalue()
    assert "Hello" in output


@patch('sys.stderr', new_callable=io.StringIO)
def test_cli_evaluate_file_not_found(mock_stderr, tmp_path):
    args = argparse.Namespace(input=str(tmp_path / "missing.xml"), expression=".//item")
    success = run_xpath_lab_logic(args)

    assert success is False
    assert "not found" in mock_stderr.getvalue()


@patch('sys.stdin.isatty', return_value=True)
@patch('sys.stderr', new_callable=io.StringIO)
def test_cli_evaluate_stdin_tty(mock_stderr, mock_isatty):
    args = argparse.Namespace(input="-", expression=".//item")
    success = run_xpath_lab_logic(args)

    assert success is False
    assert "No input provided on stdin" in mock_stderr.getvalue()


@patch('sys.stdin')
@patch('sys.stdout', new_callable=io.StringIO)
@patch('sys.stdin.isatty', return_value=False)
def test_cli_evaluate_stdin(mock_isatty, mock_stdout, mock_stdin):
    mock_stdin.read.return_value = "<root><item>HelloStdin</item></root>"
    args = argparse.Namespace(input="-", expression=".//item")

    # We also need to patch sys.stdin.isatty for the check
    with patch('sys.stdin.isatty', return_value=False):
        success = run_xpath_lab_logic(args)

    assert success is True
    assert "HelloStdin" in mock_stdout.getvalue()


@patch('sys.stderr', new_callable=io.StringIO)
def test_cli_evaluate_error(mock_stderr, tmp_path):
    test_file = tmp_path / "test.xml"
    test_file.write_text("<root><item>Hello</item></root>")

    args = argparse.Namespace(input=str(test_file), expression="////")
    success = run_xpath_lab_logic(args)

    assert success is False
    assert "Error:" in mock_stderr.getvalue()


def test_evaluate_generic_exception(manager):
    with patch("defusedxml.ElementTree.fromstring", side_effect=Exception("Generic Error")):
        result = manager.evaluate("<root></root>", ".//book")
        assert result["success"] is False
        assert "Generic Error" in result["error"]
