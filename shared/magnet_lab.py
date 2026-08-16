"""
Magnet Lab
==========

Provides utilities for parsing, building, and generating Magnet URIs.
"""

import sys
import urllib.parse
from shared.bencode_lab import BencodeManager
import hashlib

class MagnetLabManager:
    """Manages Magnet URI operations."""

    @staticmethod
    def parse(uri: str) -> dict:
        """Parses a magnet URI into its components."""
        if not uri.startswith("magnet:?"):
            raise ValueError("Invalid magnet URI: must start with 'magnet:?'")

        query = uri[8:]
        parsed = urllib.parse.parse_qs(query)

        result = {}
        if 'xt' in parsed:
            result['xt'] = parsed['xt']
        if 'dn' in parsed:
            result['dn'] = parsed['dn'][0]
        if 'tr' in parsed:
            result['tr'] = parsed['tr']
        if 'xl' in parsed:
            try:
                result['xl'] = int(parsed['xl'][0])
            except ValueError:
                result['xl'] = parsed['xl'][0]

        return result

    @staticmethod
    def build(components: dict) -> str:
        """Builds a magnet URI from components."""
        params = []

        if 'xt' in components:
            xts = components['xt'] if isinstance(components['xt'], list) else [components['xt']]
            for xt in xts:
                params.append(f"xt={urllib.parse.quote(xt, safe=':')}")

        if 'dn' in components:
            params.append(f"dn={urllib.parse.quote(str(components['dn']))}")

        if 'xl' in components:
            params.append(f"xl={components['xl']}")

        if 'tr' in components:
            trs = components['tr'] if isinstance(components['tr'], list) else [components['tr']]
            for tr in trs:
                params.append(f"tr={urllib.parse.quote(tr)}")

        if not params:
            raise ValueError("At least one component (usually 'xt') is required to build a magnet URI")

        return "magnet:?" + "&".join(params)

    @staticmethod
    def from_torrent(torrent_data: bytes) -> str:
        """Generates a magnet URI from torrent file data."""
        manager = BencodeManager()
        try:
            decoded = manager.decode(torrent_data)
        except Exception as e:
            raise ValueError(f"Failed to decode torrent data: {e}")

        if 'info' not in decoded and b'info' not in decoded:
            raise ValueError("Invalid torrent: missing 'info' dictionary")

        info_key = 'info' if 'info' in decoded else b'info'
        info_dict = decoded[info_key]

        encoded_info = manager.encode(info_dict)
        info_hash = hashlib.sha1(encoded_info).hexdigest()

        components = {
            'xt': f"urn:btih:{info_hash}"
        }

        # Try to get name
        name_key = 'name' if 'name' in info_dict else b'name'
        if name_key in info_dict:
            name_val = info_dict[name_key]
            if isinstance(name_val, bytes):
                try:
                    components['dn'] = name_val.decode('utf-8')
                except UnicodeDecodeError:
                    pass
            else:
                components['dn'] = name_val

        # Try to get trackers
        trackers = []
        announce_key = 'announce' if 'announce' in decoded else b'announce'
        if announce_key in decoded:
            val = decoded[announce_key]
            if isinstance(val, bytes):
                try:
                    trackers.append(val.decode('utf-8'))
                except UnicodeDecodeError:
                    pass
            else:
                trackers.append(val)

        announce_list_key = 'announce-list' if 'announce-list' in decoded else b'announce-list'
        if announce_list_key in decoded:
            for tier in decoded[announce_list_key]:
                for tr in tier:
                    if isinstance(tr, bytes):
                        try:
                            tr_str = tr.decode('utf-8')
                            if tr_str not in trackers:
                                trackers.append(tr_str)
                        except UnicodeDecodeError:
                            pass
                    else:
                        if tr not in trackers:
                            trackers.append(tr)

        if trackers:
            components['tr'] = trackers

        return MagnetLabManager.build(components)

def run_magnet_lab_logic(args):
    """CLI logic for magnet-lab."""
    manager = MagnetLabManager()

    if args.action == "parse":
        if not args.uri:
            print("Error: --uri is required for parse action.", file=sys.stderr)
            return False

        try:
            import json
            parsed = manager.parse(args.uri)
            print(json.dumps(parsed, indent=2))
            return True
        except Exception as e:
            print(f"Error parsing magnet URI: {e}", file=sys.stderr)
            return False

    elif args.action == "build":
        components = {}
        if args.xt:
            components['xt'] = args.xt
        if args.dn:
            components['dn'] = args.dn
        if args.tr:
            components['tr'] = args.tr
        if args.xl:
            components['xl'] = args.xl

        try:
            uri = manager.build(components)
            print(uri)
            return True
        except Exception as e:
            print(f"Error building magnet URI: {e}", file=sys.stderr)
            return False

    elif args.action == "from-torrent":
        if not args.file:
            print("Error: --file is required for from-torrent action.", file=sys.stderr)
            return False

        try:
            with open(args.file, 'rb') as f:
                torrent_data = f.read()
            uri = manager.from_torrent(torrent_data)
            print(uri)
            return True
        except FileNotFoundError:
            print(f"Error: Torrent file not found: {args.file}", file=sys.stderr)
            return False
        except Exception as e:
            print(f"Error generating magnet URI from torrent: {e}", file=sys.stderr)
            return False

    return True
