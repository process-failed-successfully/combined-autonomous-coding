import pytest
import os
from pathlib import Path
from shared.filetype_lab import FileTypeManager
from argparse import Namespace
from shared.filetype_lab import run_filetype_lab_logic

@pytest.fixture
def manager():
    return FileTypeManager()

def test_detect_png(manager, tmp_path):
    f = tmp_path / "test.png"
    f.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\x0D")
    result = manager.detect(str(f))
    assert result["ext"] == "png"
    assert result["mime"] == "image/png"

def test_detect_jpeg(manager, tmp_path):
    f = tmp_path / "test.jpg"
    f.write_bytes(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01")
    result = manager.detect(str(f))
    assert result["ext"] == "jpg"
    assert result["mime"] == "image/jpeg"

def test_detect_pdf(manager, tmp_path):
    f = tmp_path / "test.pdf"
    f.write_bytes(b"%PDF-1.4\n")
    result = manager.detect(str(f))
    assert result["ext"] == "pdf"
    assert result["mime"] == "application/pdf"

def test_detect_zip(manager, tmp_path):
    f = tmp_path / "test.zip"
    f.write_bytes(b"PK\x03\x04\n\x00\x00\x00")
    result = manager.detect(str(f))
    assert result["ext"] == "zip"
    assert result["mime"] == "application/zip"

def test_detect_txt(manager, tmp_path):
    f = tmp_path / "test.txt"
    f.write_bytes(b"Hello world, this is a simple text file.")
    result = manager.detect(str(f))
    assert result["ext"] == "txt"
    assert result["mime"] == "text/plain"

def test_detect_bin(manager, tmp_path):
    f = tmp_path / "test.bin"
    # Some random binary data that is not text and doesn't match any known magic bytes
    f.write_bytes(b"\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0A\x0B\x0C\x0D")
    result = manager.detect(str(f))
    assert result["ext"] == "bin"
    assert result["mime"] == "application/octet-stream"

def test_detect_empty(manager, tmp_path):
    f = tmp_path / "test.empty"
    f.write_bytes(b"")
    result = manager.detect(str(f))
    assert result["ext"] == ""
    assert result["mime"] == "application/x-empty"

def test_detect_not_found(manager):
    result = manager.detect("/path/that/does/not/exist.xyz")
    assert "error" in result

def test_run_filetype_lab_logic(tmp_path, capsys):
    f = tmp_path / "test.pdf"
    f.write_bytes(b"%PDF-1.4\n")
    args = Namespace(file=str(f), action=None)
    assert run_filetype_lab_logic(args) is True
    out, _ = capsys.readouterr()
    assert "Extension: pdf" in out
    assert "MIME Type: application/pdf" in out

def test_run_filetype_lab_logic_error(capsys):
    args = Namespace(file="/invalid/path", action=None)
    assert run_filetype_lab_logic(args) is False
    _, err = capsys.readouterr()
    assert "Error:" in err
