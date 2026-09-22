"""
Magnet Lab
==========

Utilities for parsing and building Magnet URIs, and generating them from torrent files.
"""

import urllib.parse
import hashlib
import sys
import json
from typing import Dict, Any, List, Optional
from shared.bencode_lab import BencodeManager

class MagnetLabManager:
    """Manages Magnet URI operations."""

    @staticmethod
    def parse(magnet_uri: str) -> Dict[str, Any]:
        """Parses a Magnet URI into a dictionary."""
        if not magnet_uri.startswith("magnet:?"):
            raise ValueError("Invalid Magnet URI: must start with 'magnet:?'")

        query = magnet_uri[8:]
        parsed_qs = urllib.parse.parse_qs(query)

        result = {
            "xt": parsed_qs.get("xt", []),
            "dn": parsed_qs.get("dn", [None])[0],
            "tr": parsed_qs.get("tr", []),
            "ws": parsed_qs.get("ws", []),
            "xs": parsed_qs.get("xs", [])
        }

        # Clean up empty optional fields
        result = {k: v for k, v in result.items() if v}
        return result

    @staticmethod
    def build(xt: str, dn: Optional[str] = None, tr: Optional[List[str]] = None) -> str:
        """Builds a Magnet URI from parameters."""
        if not xt:
             raise ValueError("Exact Topic (xt) is required, e.g., urn:btih:...")

        params = [("xt", xt)]
        if dn:
            params.append(("dn", dn))
        if tr:
            for tracker in tr:
                params.append(("tr", tracker))

        # By default urlencode encodes `:`. So urn:btih... will be urn%3Abtih...
        # The test expects standard urlencoding (which escapes `:`)
        query_string = urllib.parse.urlencode(params)
        return f"magnet:?{query_string}"

    @staticmethod
    def from_torrent(torrent_data: bytes) -> str:
        """Generates a Magnet URI from raw torrent file data."""
        decoded = BencodeManager.decode(torrent_data)

        if "info" not in decoded:
            raise ValueError("Invalid torrent file: missing 'info' dictionary")

        info_dict = decoded["info"]

        encoded_info = BencodeManager.encode(info_dict)
        info_hash = hashlib.sha1(encoded_info).hexdigest()
        xt = f"urn:btih:{info_hash}"

        dn = None
        if "name" in info_dict:
             name_val = info_dict["name"]
             if isinstance(name_val, bytes):
                  try:
                      dn = name_val.decode('utf-8')
                  except UnicodeDecodeError:
                      dn = None
             else:
                  dn = str(name_val)

        trackers = []
        if "announce" in decoded:
             ann = decoded["announce"]
             if isinstance(ann, bytes):
                 try:
                     trackers.append(ann.decode('utf-8'))
                 except UnicodeDecodeError:
                     pass

        if "announce-list" in decoded:
             for ann_tier in decoded["announce-list"]:
                  for ann in ann_tier:
                       if isinstance(ann, bytes):
                            try:
                                tracker_str = ann.decode('utf-8')
                                if tracker_str not in trackers:
                                    trackers.append(tracker_str)
                            except UnicodeDecodeError:
                                pass

        return MagnetLabManager.build(xt=xt, dn=dn, tr=trackers)


def run_magnet_lab_logic(args):
    """CLI logic for magnet-lab."""
    manager = MagnetLabManager()

    if args.action == "parse":
        try:
            result = manager.parse(args.uri)
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(f"Error parsing magnet URI: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "build":
        try:
            result = manager.build(xt=args.xt, dn=args.dn, tr=args.tr)
            print(result)
        except Exception as e:
            print(f"Error building magnet URI: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "from-torrent":
        try:
            with open(args.torrent_file, 'rb') as f:
                 torrent_data = f.read()
            result = manager.from_torrent(torrent_data)
            print(result)
        except Exception as e:
            print(f"Error generating from torrent: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "tui":
        try:
            from shared.tui_magnet import run_tui
            run_tui()
        except ImportError as e:
            print(f"Error loading TUI: {e}", file=sys.stderr)
            sys.exit(1)
