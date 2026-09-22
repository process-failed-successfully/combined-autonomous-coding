import urllib.parse
import hashlib
import sys
from typing import Dict, Any
from shared.bencode_lab import BencodeManager

class MagnetLabManager:
    """Manages Magnet URI operations."""

    @staticmethod
    def parse(uri: str) -> dict:
        """Parses a magnet URI into a dictionary."""
        if not uri.startswith("magnet:?"):
            return {"error": "Invalid magnet URI"}

        parsed = urllib.parse.urlparse(uri)
        qs = urllib.parse.parse_qs(parsed.query)

        return {"success": True, "parsed": qs}

    @staticmethod
    def build(params: dict) -> str:
        """Builds a magnet URI from parameters."""
        query_parts = []
        for k, v in params.items():
            if isinstance(v, list):
                for item in v:
                    query_parts.append(urllib.parse.urlencode({k: item}))
            else:
                query_parts.append(urllib.parse.urlencode({k: v}))

        return "magnet:?" + "&".join(query_parts)

    @staticmethod
    def from_torrent(torrent_path: str) -> dict:
        """Generates a magnet URI from a .torrent file."""
        try:
            with open(torrent_path, 'rb') as f:
                data = f.read()

            b = BencodeManager()
            decoded = b.decode(data)

            # Account for both string and bytes keys
            info = decoded.get('info') or decoded.get(b'info')
            if not info:
                return {"error": "No info dictionary found in torrent."}

            info_encoded = b.encode(info)
            info_hash = hashlib.sha1(info_encoded).hexdigest()

            xt = f"urn:btih:{info_hash}"

            dn = info.get('name') or info.get(b'name')
            if isinstance(dn, bytes):
                dn = dn.decode('utf-8', errors='ignore')

            tr = []

            announce = decoded.get('announce') or decoded.get(b'announce')
            if announce:
                if isinstance(announce, bytes):
                    announce = announce.decode('utf-8', errors='ignore')
                tr.append(announce)

            announce_list = decoded.get('announce-list') or decoded.get(b'announce-list')
            if announce_list:
                for tier in announce_list:
                    for tracker in tier:
                        if isinstance(tracker, bytes):
                            tracker = tracker.decode('utf-8', errors='ignore')
                        if tracker not in tr:
                            tr.append(tracker)

            params = {"xt": xt}
            if dn:
                params["dn"] = dn
            if tr:
                params["tr"] = tr

            uri = MagnetLabManager.build(params)
            return {"success": True, "uri": uri, "info_hash": info_hash, "name": dn, "trackers": tr}
        except Exception as e:
            return {"error": str(e)}

def run_magnet_lab_logic(args) -> bool:
    """CLI handler for Magnet Lab."""
    import json

    if args.action == "parse":
        result = MagnetLabManager.parse(args.uri)
        if result.get("success"):
            print(json.dumps(result["parsed"], indent=2))
            return True
        else:
            print(f"Error: {result.get('error')}", file=sys.stderr)
            return False

    elif args.action == "build":
        params = {}
        if args.xt:
            params["xt"] = args.xt
        if args.dn:
            params["dn"] = args.dn
        if args.tr:
            params["tr"] = args.tr

        if not params:
            print("Error: No parameters provided for build.", file=sys.stderr)
            return False

        uri = MagnetLabManager.build(params)
        print(uri)
        return True

    elif args.action == "from-torrent":
        result = MagnetLabManager.from_torrent(args.file)
        if result.get("success"):
            print(result["uri"])
            return True
        else:
            print(f"Error: {result.get('error')}", file=sys.stderr)
            return False

    return False
