import os
import pytest
import zipfile
import tarfile
from pathlib import Path
from shared.archive_lab import ArchiveLabManager

@pytest.fixture
def manager(tmp_path):
    return ArchiveLabManager(tmp_path)

@pytest.fixture
def sample_files(tmp_path):
    # Create some dummy files
    f1 = tmp_path / "file1.txt"
    f1.write_text("Hello World")

    d1 = tmp_path / "dir1"
    d1.mkdir()
    f2 = d1 / "file2.txt"
    f2.write_text("Nested file content")

    return [f1, d1]

def test_create_zip(manager, tmp_path, sample_files):
    archive_path = tmp_path / "test.zip"
    manager.create(archive_path, sample_files)

    assert archive_path.exists()
    assert zipfile.is_zipfile(archive_path)

    # Check contents
    contents = manager.list_contents(archive_path)
    names = [c['name'] for c in contents]
    assert "file1.txt" in names
    # Note: different OS/methods might store dir entries differently or not at all
    # zipfile often doesn't store explicit dir entries unless added
    # but we added 'dir1' explicitly so it should iterate and add 'dir1/file2.txt'
    # Windows paths might be different, but python zipfile handles / usually.
    assert any("file2.txt" in n for n in names)

def test_create_tar(manager, tmp_path, sample_files):
    archive_path = tmp_path / "test.tar"
    manager.create(archive_path, sample_files)

    assert archive_path.exists()
    assert tarfile.is_tarfile(archive_path)

    contents = manager.list_contents(archive_path)
    names = [c['name'] for c in contents]
    assert "file1.txt" in names
    assert any("file2.txt" in n for n in names)

def test_create_tar_gz(manager, tmp_path, sample_files):
    archive_path = tmp_path / "test.tar.gz"
    manager.create(archive_path, sample_files)

    assert archive_path.exists()
    assert tarfile.is_tarfile(archive_path)

def test_extract_zip(manager, tmp_path, sample_files):
    archive_path = tmp_path / "test_extract.zip"
    manager.create(archive_path, sample_files)

    dest_dir = tmp_path / "extracted"
    manager.extract(archive_path, dest_dir)

    assert (dest_dir / "file1.txt").exists()
    assert (dest_dir / "file1.txt").read_text() == "Hello World"
    assert (dest_dir / "dir1" / "file2.txt").exists()

def test_extract_tar(manager, tmp_path, sample_files):
    archive_path = tmp_path / "test_extract.tar"
    manager.create(archive_path, sample_files)

    dest_dir = tmp_path / "extracted_tar"
    manager.extract(archive_path, dest_dir)

    assert (dest_dir / "file1.txt").exists()
    assert (dest_dir / "dir1" / "file2.txt").exists()

def test_add_to_zip(manager, tmp_path, sample_files):
    archive_path = tmp_path / "test_add.zip"
    # Create initial
    f1 = sample_files[0]
    manager.create(archive_path, [f1])

    # Add new file
    new_file = tmp_path / "new.txt"
    new_file.write_text("New Content")
    manager.add(archive_path, [new_file])

    contents = manager.list_contents(archive_path)
    names = [c['name'] for c in contents]
    assert "file1.txt" in names
    assert "new.txt" in names

def test_add_to_tar(manager, tmp_path, sample_files):
    archive_path = tmp_path / "test_add.tar"
    f1 = sample_files[0]
    manager.create(archive_path, [f1])

    new_file = tmp_path / "new.txt"
    new_file.write_text("New Content")
    manager.add(archive_path, [new_file])

    contents = manager.list_contents(archive_path)
    names = [c['name'] for c in contents]
    assert "file1.txt" in names
    assert "new.txt" in names

def test_add_to_compressed_tar_fails(manager, tmp_path, sample_files):
    archive_path = tmp_path / "test_fail.tar.gz"
    manager.create(archive_path, sample_files)

    new_file = tmp_path / "new.txt"
    new_file.write_text("New Content")

    with pytest.raises(NotImplementedError):
        manager.add(archive_path, [new_file])

def test_invalid_archive(manager, tmp_path):
    bad_file = tmp_path / "bad.txt"
    bad_file.write_text("Not an archive")

    with pytest.raises(ValueError):
        manager.list_contents(bad_file)

def test_missing_file(manager, tmp_path):
    with pytest.raises(FileNotFoundError):
        manager.list_contents(tmp_path / "nonexistent.zip")
