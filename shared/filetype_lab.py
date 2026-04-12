import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional

# A dictionary of common magic bytes.
# Keys are bytes objects representing the magic signature.
# Values are dicts with extension, mime, and description.
MAGIC_BYTES = {
    b"\x89PNG\r\n\x1a\n": {"ext": "png", "mime": "image/png", "desc": "PNG image data"},
    b"\xff\xd8\xff": {"ext": "jpg", "mime": "image/jpeg", "desc": "JPEG image data"},
    b"GIF87a": {"ext": "gif", "mime": "image/gif", "desc": "GIF image data"},
    b"GIF89a": {"ext": "gif", "mime": "image/gif", "desc": "GIF image data"},
    b"%PDF-": {"ext": "pdf", "mime": "application/pdf", "desc": "PDF document"},
    b"PK\x03\x04": {"ext": "zip", "mime": "application/zip", "desc": "ZIP archive"},
    b"PK\x05\x06": {"ext": "zip", "mime": "application/zip", "desc": "ZIP archive (empty)"},
    b"PK\x07\x08": {"ext": "zip", "mime": "application/zip", "desc": "ZIP archive (spanned)"},
    b"Rar!\x1a\x07\x00": {"ext": "rar", "mime": "application/x-rar-compressed", "desc": "RAR archive v1.50+"},
    b"Rar!\x1a\x07\x01\x00": {"ext": "rar", "mime": "application/x-rar-compressed", "desc": "RAR archive v5.0+"},
    b"7z\xbc\xaf\x27\x1c": {"ext": "7z", "mime": "application/x-7z-compressed", "desc": "7-zip archive"},
    b"\x1f\x8b\x08": {"ext": "gz", "mime": "application/gzip", "desc": "GZIP compressed data"},
    b"BZh": {"ext": "bz2", "mime": "application/x-bzip2", "desc": "bzip2 compressed data"},
    b"\xFD7zXZ\x00": {"ext": "xz", "mime": "application/x-xz", "desc": "XZ compressed data"},
    b"\x04\x22\x4D\x18": {"ext": "lz4", "mime": "application/x-lz4", "desc": "LZ4 compressed data"},
    b"\x28\xB5\x2F\xFD": {"ext": "zst", "mime": "application/zstd", "desc": "Zstandard compressed data"},
    b"OggS": {"ext": "ogg", "mime": "application/ogg", "desc": "Ogg multimedia format"},
    b"fLaC": {"ext": "flac", "mime": "audio/flac", "desc": "FLAC audio data"},
    b"ID3": {"ext": "mp3", "mime": "audio/mpeg", "desc": "MP3 audio data (ID3v2)"},
    b"\xFF\xFB": {"ext": "mp3", "mime": "audio/mpeg", "desc": "MP3 audio data"},
    b"\xFF\xF3": {"ext": "mp3", "mime": "audio/mpeg", "desc": "MP3 audio data"},
    b"\xFF\xF2": {"ext": "mp3", "mime": "audio/mpeg", "desc": "MP3 audio data"},
    b"RIFF": {"ext": "wav/avi/webp", "mime": "audio/x-wav", "desc": "RIFF (little-endian) data"},
    b"\x00\x00\x01\xBA": {"ext": "mpg", "mime": "video/mpeg", "desc": "MPEG video data"},
    b"\x00\x00\x01\xB3": {"ext": "mpg", "mime": "video/mpeg", "desc": "MPEG video data"},
    b"\x4D\x5A": {"ext": "exe", "mime": "application/x-msdownload", "desc": "DOS/Windows executable (MZ)"},
    b"\x7FELF": {"ext": "elf", "mime": "application/x-executable", "desc": "ELF executable"},
    b"\xCE\xFA\xED\xFE": {"ext": "macho", "mime": "application/x-mach-binary", "desc": "Mach-O binary (32-bit)"},
    b"\xCF\xFA\xED\xFE": {"ext": "macho", "mime": "application/x-mach-binary", "desc": "Mach-O binary (64-bit)"},
    b"\xCA\xFE\xBA\xBE": {"ext": "class", "mime": "application/java-vm", "desc": "Java class file / Mach-O universal binary"},
    b"BM": {"ext": "bmp", "mime": "image/bmp", "desc": "BMP image data"},
    b"II*\x00": {"ext": "tif", "mime": "image/tiff", "desc": "TIFF image data (little-endian)"},
    b"MM\x00*": {"ext": "tif", "mime": "image/tiff", "desc": "TIFF image data (big-endian)"},
    b"{\\rtf1": {"ext": "rtf", "mime": "application/rtf", "desc": "Rich Text Format"},
    b"SQLite format 3\x00": {"ext": "sqlite", "mime": "application/vnd.sqlite3", "desc": "SQLite 3 database"},
    b"\x00\x01\x00\x00\x00": {"ext": "ttf", "mime": "font/ttf", "desc": "TrueType font"},
    b"OTTO": {"ext": "otf", "mime": "font/otf", "desc": "OpenType font"},
    b"wOFF": {"ext": "woff", "mime": "font/woff", "desc": "WOFF font"},
    b"wOF2": {"ext": "woff2", "mime": "font/woff2", "desc": "WOFF2 font"},
    b"#!/bin/bash": {"ext": "sh", "mime": "text/x-shellscript", "desc": "Bash script"},
    b"#!/bin/sh": {"ext": "sh", "mime": "text/x-shellscript", "desc": "Shell script"},
    b"#!/usr/bin/env python": {"ext": "py", "mime": "text/x-python", "desc": "Python script"},
    b"<?xml": {"ext": "xml", "mime": "application/xml", "desc": "XML document"},
    b"<!DOCTYPE html": {"ext": "html", "mime": "text/html", "desc": "HTML document"},
    b"\xef\xbb\xbf": {"ext": "txt", "mime": "text/plain", "desc": "UTF-8 encoded text with BOM"},
}


class FileTypeManager:
    """Manager to detect file types via magic bytes."""

    def detect(self, filepath: str) -> Dict[str, str]:
        """Reads the first few bytes of a file and detects its type."""
        path = Path(filepath)
        if not path.exists():
            return {"error": f"File '{filepath}' not found."}
        if not path.is_file():
            return {"error": f"Path '{filepath}' is not a regular file."}

        try:
            # We only need the first 32 bytes to identify most magic numbers
            with open(path, "rb") as f:
                head = f.read(32)
        except Exception as e:
            return {"error": f"Error reading file: {e}"}

        if not head:
            return {"ext": "", "mime": "application/x-empty", "desc": "Empty file"}

        # Special handling for ISO (CD-ROM)
        if len(head) >= 32 and b"CD001" in head[25:32] or (len(head)>=32 and head[25:30] == b"CD001"):
             return {"ext": "iso", "mime": "application/x-iso9660-image", "desc": "ISO 9660 CD-ROM filesystem data"}

        # Simple greedy matching: Find the longest matching magic bytes
        best_match = None
        best_len = 0

        for magic, info in MAGIC_BYTES.items():
            if head.startswith(magic):
                if len(magic) > best_len:
                    best_len = len(magic)
                    best_match = info

        # Additional RIFF detection
        if head.startswith(b"RIFF") and len(head) >= 12:
            chunk_type = head[8:12]
            if chunk_type == b"WAVE":
                best_match = {"ext": "wav", "mime": "audio/x-wav", "desc": "WAV audio data"}
            elif chunk_type == b"AVI ":
                best_match = {"ext": "avi", "mime": "video/x-msvideo", "desc": "AVI video data"}
            elif chunk_type == b"WEBP":
                best_match = {"ext": "webp", "mime": "image/webp", "desc": "WebP image data"}

        if best_match:
            return best_match

        # Text fallback
        try:
            head.decode("utf-8")
            # If it decodes successfully as UTF-8, it might be a text file
            # Let's check for non-printable characters.
            if any(b < 9 or (13 < b < 32) for b in head):
                pass # Probably not standard text
            else:
                return {"ext": "txt", "mime": "text/plain", "desc": "Text file (or unknown ASCII/UTF-8 data)"}
        except UnicodeDecodeError:
            pass

        return {"ext": "bin", "mime": "application/octet-stream", "desc": "Unknown binary data"}


def run_filetype_lab_logic(args) -> bool:
    """CLI handler for FileType Lab."""

    if getattr(args, "action", None) == "tui":
        try:
            from shared.tui import AgentTUI
            import asyncio
            app = AgentTUI(project_dir=Path.cwd(), initial_tab="tab-filetype")
            asyncio.run(app.run_async())
            return True
        except ImportError as e:
            print(f"Error launching TUI: {e}", file=sys.stderr)
            return False

    manager = FileTypeManager()
    filepath = getattr(args, "file", None)
    if not filepath:
        print("Error: A file path is required.", file=sys.stderr)
        return False

    result = manager.detect(filepath)
    if "error" in result:
        print(f"Error: {result['error']}", file=sys.stderr)
        return False

    print(f"File: {filepath}")
    print(f"Extension: {result.get('ext', 'N/A')}")
    print(f"MIME Type: {result.get('mime', 'N/A')}")
    print(f"Description: {result.get('desc', 'N/A')}")

    return True
