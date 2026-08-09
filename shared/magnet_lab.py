import urllib.parse
import hashlib
import sys
import json
from pathlib import Path
from shared.bencode_lab import BencodeManager

class MagnetLabManager:
    """Manages Magnet URI parsing and building, including from .torrent files."""

    @staticmethod
    def parse(uri: str) -> dict:
        """Parses a magnet URI into a dictionary of its components."""
        if not uri.startswith("magnet:?"):
            return {"success": False, "error": "Not a valid magnet URI."}

        query = uri[8:]
        parsed = urllib.parse.parse_qs(query)

        result = {
            "xt": parsed.get("xt", []),
            "dn": parsed.get("dn", [""])[0],
            "tr": parsed.get("tr", []),
            "ws": parsed.get("ws", []),
        }

        # Try to extract exact length if present
        if "xl" in parsed:
            try:
                result["xl"] = int(parsed["xl"][0])
            except ValueError:
                result["xl"] = None

        return {"success": True, "result": result}

    @staticmethod
    def build(info_hash: str, name: str = "", trackers: list = None) -> dict:
        """Builds a magnet URI from components."""
        if trackers is None:
            trackers = []

        if not info_hash.startswith("urn:btih:"):
            # Assume it's a raw hex info hash
            if len(info_hash) == 40:
                xt = f"urn:btih:{info_hash}"
            else:
                return {"success": False, "error": "Invalid info_hash. Must be a 40-character hex string or start with 'urn:btih:'."}
        else:
            xt = info_hash

        params = [f"xt={xt}"]

        if name:
            params.append(f"dn={urllib.parse.quote(name)}")

        for tr in trackers:
            if tr:
                params.append(f"tr={urllib.parse.quote(tr)}")

        uri = "magnet:?" + "&".join(params)
        return {"success": True, "uri": uri}

    @staticmethod
    def from_torrent(filepath: str) -> dict:
        """Reads a .torrent file and returns a magnet URI."""
        path = Path(filepath)
        if not path.is_file():
            return {"success": False, "error": f"File not found: {filepath}"}

        try:
            with open(path, 'rb') as f:
                data = f.read()

            decoded = BencodeManager.decode(data)

            # Look for the 'info' dict
            info = None
            if b'info' in decoded:
                info = decoded[b'info']
            elif 'info' in decoded:
                info = decoded['info']

            if info is None:
                return {"success": False, "error": "Invalid torrent file: missing 'info' dictionary."}

            # Re-encode the info dictionary to compute its SHA-1 hash
            # We must be careful because BencodeManager.encode expects python dicts.
            # BencodeManager.decode returns a mix of byte keys/values depending on parsing.
            # But wait, to get the EXACT info hash, we should slice the original file if possible,
            # or re-encode using our BencodeManager.

            # Since BencodeManager.encode has strict typing, let's use it.
            info_encoded = BencodeManager.encode(info)
            info_hash = hashlib.sha1(info_encoded).hexdigest()

            # Extract name
            name = ""
            if b'name' in info:
                name = info[b'name'].decode('utf-8', errors='replace')
            elif 'name' in info:
                # Value could be bytes
                name_val = info['name']
                if isinstance(name_val, bytes):
                    name = name_val.decode('utf-8', errors='replace')
                else:
                    name = str(name_val)

            # Extract trackers
            trackers = []
            if b'announce' in decoded:
                tr_val = decoded[b'announce']
                if isinstance(tr_val, bytes):
                    trackers.append(tr_val.decode('utf-8', errors='replace'))
                else:
                    trackers.append(str(tr_val))
            elif 'announce' in decoded:
                tr_val = decoded['announce']
                if isinstance(tr_val, bytes):
                    trackers.append(tr_val.decode('utf-8', errors='replace'))
                else:
                    trackers.append(str(tr_val))

            # Handle announce-list
            announce_list = []
            if b'announce-list' in decoded:
                announce_list = decoded[b'announce-list']
            elif 'announce-list' in decoded:
                announce_list = decoded['announce-list']

            for tier in announce_list:
                for tr_val in tier:
                    if isinstance(tr_val, bytes):
                        tr_str = tr_val.decode('utf-8', errors='replace')
                    else:
                        tr_str = str(tr_val)
                    if tr_str not in trackers:
                        trackers.append(tr_str)

            return MagnetLabManager.build(info_hash, name, trackers)

        except Exception as e:
            return {"success": False, "error": f"Failed to process torrent file: {str(e)}"}

def run_magnet_lab_logic(args):
    """CLI logic for magnet-lab."""
    manager = MagnetLabManager()

    if args.action == "parse":
        if not args.uri:
            print("Error: --uri is required for parsing.", file=sys.stderr)
            sys.exit(1)
        result = manager.parse(args.uri)
        if result["success"]:
            print(json.dumps(result["result"], indent=2))
        else:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "build":
        if not args.info_hash:
            print("Error: --info-hash is required for building.", file=sys.stderr)
            sys.exit(1)

        name = getattr(args, "name", "")
        trackers = getattr(args, "trackers", [])

        result = manager.build(args.info_hash, name, trackers)
        if result["success"]:
            print(result["uri"])
        else:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "from-torrent":
        if not args.file:
            print("Error: --file is required for from-torrent.", file=sys.stderr)
            sys.exit(1)

        result = manager.from_torrent(args.file)
        if result["success"]:
            print(result["uri"])
        else:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"Error: Unknown action {args.action}", file=sys.stderr)
        sys.exit(1)
