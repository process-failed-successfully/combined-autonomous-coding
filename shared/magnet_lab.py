"""
Magnet Lab
==========

Provides utilities for parsing, building, and generating Magnet URIs from torrents.
"""

import hashlib
import sys
from urllib.parse import parse_qs, urlencode, urlparse, unquote

from shared.bencode_lab import BencodeManager

class MagnetLabManager:
    """Manages Magnet URI operations."""

    @staticmethod
    def parse(uri: str) -> dict:
        """Parses a Magnet URI into its components."""
        if not uri.startswith("magnet:?"):
            raise ValueError("Invalid Magnet URI: must start with 'magnet:?'")

        parsed = urlparse(uri)
        query_params = parse_qs(parsed.query)

        result = {}
        for key, value in query_params.items():
            if len(value) == 1:
                result[key] = value[0]
            else:
                result[key] = value

        # Convenience extractions
        if 'xt' in result:
            result['info_hash'] = result['xt']
            if isinstance(result['xt'], list):
                result['info_hash'] = result['xt'][0]

            # Extract just the hash if it's URN based
            if result['info_hash'].startswith('urn:btih:'):
                result['hash'] = result['info_hash'][9:]
            elif result['info_hash'].startswith('urn:sha1:'):
                result['hash'] = result['info_hash'][9:]

        if 'dn' in result:
            result['name'] = result['dn']
            if isinstance(result['dn'], list):
                result['name'] = result['dn'][0]

        if 'tr' in result:
            result['trackers'] = result['tr']
            if not isinstance(result['trackers'], list):
                result['trackers'] = [result['trackers']]

        return result

    @staticmethod
    def build(data: dict) -> str:
        """Builds a Magnet URI from components."""
        if 'xt' not in data and 'hash' in data:
            data['xt'] = f"urn:btih:{data['hash']}"
        elif 'xt' not in data:
            raise ValueError("Magnet URI requires 'xt' (exact topic) or 'hash'")

        params = []

        # xt is usually first
        xt = data['xt']
        if isinstance(xt, list):
            for x in xt:
                params.append(('xt', x))
        else:
            params.append(('xt', xt))

        # dn is usually second
        if 'dn' in data:
            params.append(('dn', data['dn']))
        elif 'name' in data:
            params.append(('dn', data['name']))

        # tr can be multiple
        if 'tr' in data:
            tr = data['tr']
            if isinstance(tr, list):
                for t in tr:
                    params.append(('tr', t))
            else:
                params.append(('tr', tr))
        elif 'trackers' in data:
            tr = data['trackers']
            if isinstance(tr, list):
                for t in tr:
                    params.append(('tr', t))
            else:
                params.append(('tr', tr))

        # other fields
        ignore_keys = {'xt', 'dn', 'tr', 'hash', 'name', 'trackers', 'info_hash'}
        for k, v in data.items():
            if k not in ignore_keys:
                if isinstance(v, list):
                    for item in v:
                        params.append((k, item))
                else:
                    params.append((k, v))

        query = urlencode(params)
        return f"magnet:?{query}"

    @staticmethod
    def from_torrent(torrent_data: bytes) -> str:
        """Generates a Magnet URI from a .torrent file content."""
        manager = BencodeManager()
        decoded = manager.decode(torrent_data)

        # Bencode dictionaries might have string or bytes keys depending on decode implementation
        info_key = 'info' if 'info' in decoded else b'info'
        if info_key not in decoded:
            raise ValueError("Invalid torrent file: missing 'info' dictionary")

        info_dict = decoded[info_key]
        encoded_info = manager.encode(info_dict)

        info_hash = hashlib.sha1(encoded_info).hexdigest()

        magnet_data = {
            'xt': f"urn:btih:{info_hash}"
        }

        # Name
        name_key = 'name' if 'name' in info_dict else b'name'
        if name_key in info_dict:
            name_val = info_dict[name_key]
            if isinstance(name_val, bytes):
                try:
                    magnet_data['dn'] = name_val.decode('utf-8')
                except UnicodeDecodeError:
                    pass
            else:
                magnet_data['dn'] = str(name_val)

        # Trackers
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
                trackers.append(str(val))

        announce_list_key = 'announce-list' if 'announce-list' in decoded else b'announce-list'
        if announce_list_key in decoded:
            for tier in decoded[announce_list_key]:
                for tracker in tier:
                    if isinstance(tracker, bytes):
                        try:
                            tracker_str = tracker.decode('utf-8')
                            if tracker_str not in trackers:
                                trackers.append(tracker_str)
                        except UnicodeDecodeError:
                            pass
                    else:
                        tracker_str = str(tracker)
                        if tracker_str not in trackers:
                            trackers.append(tracker_str)

        if trackers:
            magnet_data['tr'] = trackers

        return MagnetLabManager.build(magnet_data)

def run_magnet_lab_logic(args):
    """CLI logic for magnet-lab."""
    manager = MagnetLabManager()

    if args.action == "parse":
        input_data = args.uri
        if not input_data and not sys.stdin.isatty():
            input_data = sys.stdin.read().strip()

        if not input_data:
            print("Error: No URI provided.", file=sys.stderr)
            return False

        try:
            parsed = manager.parse(input_data)
            import json
            print(json.dumps(parsed, indent=2))
            return True
        except Exception as e:
            print(f"Error parsing Magnet URI: {e}", file=sys.stderr)
            return False

    elif args.action == "build":
        input_data = args.data
        if not input_data and not sys.stdin.isatty():
            input_data = sys.stdin.read().strip()

        if not input_data:
            print("Error: No JSON data provided.", file=sys.stderr)
            return False

        try:
            import json
            data = json.loads(input_data)
            uri = manager.build(data)
            print(uri)
            return True
        except json.JSONDecodeError:
            print("Error: Input must be valid JSON.", file=sys.stderr)
            return False
        except Exception as e:
            print(f"Error building Magnet URI: {e}", file=sys.stderr)
            return False

    elif args.action == "from-torrent":
        try:
            if not sys.stdin.isatty():
                torrent_data = sys.stdin.buffer.read()
            elif hasattr(args, 'file') and args.file:
                with open(args.file, 'rb') as f:
                    torrent_data = f.read()
            else:
                print("Error: No torrent data provided.", file=sys.stderr)
                return False

            uri = manager.from_torrent(torrent_data)
            print(uri)
            return True
        except Exception as e:
            print(f"Error generating Magnet URI: {e}", file=sys.stderr)
            return False

    return True
