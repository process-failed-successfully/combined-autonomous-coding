import mimetypes
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List


class MimeLabManager:
    """
    Manages MIME type lookups and file signature (magic number) detection.
    """

    # Common file signatures (magic numbers) for robust detection
    MAGIC_NUMBERS = {
        b'\x89PNG\r\n\x1a\n': 'image/png',
        b'\xff\xd8\xff': 'image/jpeg',
        b'GIF87a': 'image/gif',
        b'GIF89a': 'image/gif',
        b'%PDF': 'application/pdf',
        b'PK\x03\x04': 'application/zip',
        b'Rar!\x1a\x07\x00': 'application/x-rar-compressed',
        b'\x1f\x8b\x08': 'application/gzip',
        b'\x42\x5a\x68': 'application/x-bzip2',
        b'\x7f\x45\x4c\x46': 'application/x-elf',
        b'\x4d\x5a': 'application/x-msdownload',  # EXE, DLL
        b'\x00\x00\x00\x18ftypmp42': 'video/mp4',
        b'\x00\x00\x00\x20ftypisom': 'video/mp4',
        b'\x1a\x45\xdf\xa3': 'video/webm',
        b'OggS': 'audio/ogg',  # Or video/ogg
        b'\x49\x44\x33': 'audio/mpeg',  # MP3 with ID3
        b'\xff\xfb': 'audio/mpeg',  # MP3 without ID3
        b'\x52\x49\x46\x46': 'audio/wav',  # Actually RIFF, typically WAV or AVI
        b'BM': 'image/bmp',
        b'\x00\x00\x01\x00': 'image/x-icon',  # ICO
        b'{\n': 'application/json',  # Very basic json guess
        b'{"': 'application/json',  # Very basic json guess
        b'<?xml': 'application/xml',
        b'<!DOCTYPE': 'application/xml',
        b'<html': 'text/html',
        b'<!DOCTYPE html': 'text/html',
    }

    def __init__(self):
        mimetypes.init()
        # Add some modern missing ones
        mimetypes.add_type('application/json', '.json')
        mimetypes.add_type('application/yaml', '.yaml')
        mimetypes.add_type('application/yaml', '.yml')
        mimetypes.add_type('text/markdown', '.md')
        mimetypes.add_type('image/webp', '.webp')

    def lookup_by_extension(self, ext: str) -> Optional[str]:
        """Looks up the MIME type for a given file extension."""
        if not ext.startswith('.'):
            ext = '.' + ext
        # Strict=False to include non-standard ones added by the OS
        return mimetypes.guess_type('test' + ext, strict=False)[0]

    def lookup_by_mime(self, mime_type: str) -> List[str]:
        """Looks up all extensions for a given MIME type."""
        # guess_all_extensions returns extensions for the type
        extensions = mimetypes.guess_all_extensions(mime_type, strict=False)
        return list(set(extensions))  # Remove duplicates

    def detect_file(self, filepath: Path) -> Dict[str, Any]:
        """
        Detects the MIME type of a file using both extension and magic numbers.
        Returns a dict with 'extension_based', 'magic_based', 'is_match', and 'confidence'.
        """
        if not filepath.exists() or not filepath.is_file():
            raise FileNotFoundError(f"File not found: {filepath}")

        ext_type = self.lookup_by_extension(filepath.suffix)

        magic_type = None
        try:
            # Read first 100 bytes for magic number detection
            with open(filepath, 'rb') as f:
                header = f.read(100)

            for magic, mime in self.MAGIC_NUMBERS.items():
                if header.startswith(magic):
                    magic_type = mime
                    break

            # Special handling for RIFF
            if header.startswith(b'\x52\x49\x46\x46'):
                if header[8:12] == b'WAVE':
                    magic_type = 'audio/wav'
                elif header[8:12] == b'AVI ':
                    magic_type = 'video/x-msvideo'
                elif header[8:12] == b'WEBP':
                    magic_type = 'image/webp'

            # Special handling for ZIP-based formats (DOCX, etc.)
            if magic_type == 'application/zip' and ext_type:
                # If magic says zip, but ext says something specific like docx,
                # we can trust the extension more if it's a known zip-based format.
                zip_based_types = [
                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                    'application/epub+zip',
                    'application/java-archive'
                ]
                if ext_type in zip_based_types:
                    magic_type = ext_type  # Upgrade the magic type to match the specific format

        except Exception:
            pass  # If we can't read the file, magic_type stays None

        # Determine best guess
        best_guess = magic_type or ext_type or "application/octet-stream"
        confidence = "High" if magic_type else ("Medium" if ext_type else "Low")

        # If magic and ext disagree significantly, confidence drops
        if magic_type and ext_type and magic_type != ext_type:
            # Check if they share the same major type (e.g. text/html vs text/xml)
            if magic_type.split('/')[0] != ext_type.split('/')[0]:
                confidence = "Low (Conflict)"

        return {
            "best_guess": best_guess,
            "extension_based": ext_type,
            "magic_based": magic_type,
            "confidence": confidence,
            "size_bytes": filepath.stat().st_size
        }


def run_mime_lab_logic(args) -> bool:
    """CLI Entry point for Mime Lab."""

    if getattr(args, 'action', None) == "tui":
        from shared.tui import AgentTUI
        print("Launching Mime Lab TUI...")
        app = AgentTUI(project_dir=args.project_dir, start_tab="tab-mime")
        import asyncio
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            asyncio.ensure_future(app.run_async())
        else:
            app.run()
        sys.exit(0)

    manager = MimeLabManager()

    if args.action == "lookup":
        result = manager.lookup_by_extension(args.extension)
        if result:
            print(f"Extension '{args.extension}' maps to: {result}")
        else:
            print(f"Unknown extension: {args.extension}")
            return False

    elif args.action == "reverse":
        results = manager.lookup_by_mime(args.mime)
        if results:
            print(f"MIME type '{args.mime}' uses extensions: {', '.join(results)}")
        else:
            print(f"Unknown MIME type or no extensions mapped: {args.mime}")
            return False

    elif args.action == "detect":
        try:
            info = manager.detect_file(Path(args.file))
            print(f"--- File Type Detection for: {args.file} ---")
            print(f"Best Guess:      {info['best_guess']}")
            print(f"Confidence:      {info['confidence']}")
            print(f"By Extension:    {info['extension_based'] or 'Unknown'}")
            print(f"By Magic Number: {info['magic_based'] or 'Unknown'}")
            print(f"Size:            {info['size_bytes']} bytes")
        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            return False
        except Exception as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            return False

    else:
        print(f"Unknown action: {args.action}", file=sys.stderr)
        return False

    return True
