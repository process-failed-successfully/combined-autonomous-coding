import argparse
import base64
import sys
import mimetypes
from urllib.parse import quote, unquote
from pathlib import Path
from typing import Dict, Any, Optional

class DataUriLabManager:
    """Manages Data URI generation and parsing."""

    def __init__(self):
        mimetypes.init()

    def encode_text(self, text: str, mime_type: str = "text/plain", use_base64: bool = True) -> str:
        """Encodes a text string into a Data URI."""
        if use_base64:
            encoded_data = base64.b64encode(text.encode('utf-8')).decode('utf-8')
            return f"data:{mime_type};base64,{encoded_data}"
        else:
            encoded_data = quote(text)
            return f"data:{mime_type},{encoded_data}"

    def encode_file(self, filepath: str, mime_type: Optional[str] = None) -> str:
        """Encodes a file into a Data URI using base64."""
        path = Path(filepath)
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"File not found: {filepath}")

        if not mime_type:
            mime_type, _ = mimetypes.guess_type(path)
            if not mime_type:
                mime_type = "application/octet-stream"

        with open(path, "rb") as f:
            file_data = f.read()

        encoded_data = base64.b64encode(file_data).decode('utf-8')
        return f"data:{mime_type};base64,{encoded_data}"

    def decode(self, data_uri: str) -> Dict[str, Any]:
        """Decodes a Data URI into its components."""
        if not data_uri.startswith("data:"):
            raise ValueError("Invalid Data URI format: must start with 'data:'")

        try:
            # Format: data:[<mediatype>][;base64],<data>
            header_and_data = data_uri[5:].split(",", 1)
            if len(header_and_data) != 2:
                raise ValueError("Invalid Data URI format: missing comma")

            header, data = header_and_data

            is_base64 = header.endswith(";base64")
            mime_type = header[:-7] if is_base64 else header
            if not mime_type:
                mime_type = "text/plain;charset=US-ASCII"

            if is_base64:
                decoded_bytes = base64.b64decode(data)
            else:
                decoded_bytes = unquote(data).encode('utf-8')

            return {
                "mime_type": mime_type,
                "is_base64": is_base64,
                "data": decoded_bytes,
                "raw_data_string": data
            }
        except Exception as e:
            raise ValueError(f"Failed to decode Data URI: {str(e)}")

def run_data_uri_lab_logic(args: argparse.Namespace) -> bool:
    """CLI logic for Data URI Lab."""

    if getattr(args, 'action', None) == "tui":
        from shared.tui import AgentTUI
        print("Launching Data URI Lab TUI...")
        app = AgentTUI(project_dir=getattr(args, 'project_dir', Path(".")), start_tab="tab-data-uri")

        # Support both asyncio running and standard blocking run depending on Textual version
        if hasattr(app, 'run_async'):
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
        else:
            app.run()
            sys.exit(0)
        return True

    manager = DataUriLabManager()

    try:
        if args.action == "encode":
            if getattr(args, 'file', None):
                result = manager.encode_file(args.file, args.mime)
                print(result)
            elif getattr(args, 'text', None):
                use_base64 = not getattr(args, 'no_base64', False)
                mime = args.mime or "text/plain"
                result = manager.encode_text(args.text, mime, use_base64)
                print(result)
            else:
                print("Error: must provide either --text or --file for encoding.", file=sys.stderr)
                return False

        elif args.action == "decode":
            if not getattr(args, 'uri', None):
                print("Error: must provide Data URI to decode.", file=sys.stderr)
                return False

            result = manager.decode(args.uri)

            if getattr(args, 'info_only', False):
                print(f"MIME Type: {result['mime_type']}")
                print(f"Base64 Encoded: {result['is_base64']}")
                print(f"Data Length: {len(result['data'])} bytes")
            else:
                if getattr(args, 'output', None):
                    with open(args.output, "wb") as f:
                        f.write(result['data'])
                    print(f"Data saved to {args.output}")
                else:
                    # Try to decode as string if it's text
                    try:
                        print(result['data'].decode('utf-8'))
                    except UnicodeDecodeError:
                        print("Warning: Data is binary, saving to file is recommended. Use --output <file>.", file=sys.stderr)
                        # Dump hex if binary
                        print(result['data'][:100].hex(), "..." if len(result['data']) > 100 else "")
        else:
            print(f"Unknown action: {args.action}", file=sys.stderr)
            return False

        return True
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return False
