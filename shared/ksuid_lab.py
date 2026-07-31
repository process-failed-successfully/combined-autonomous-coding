import sys
import time
import os
import struct
from typing import List, Dict, Any, Optional

KSUID_EPOCH = 1400000000
BASE62_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"

class KsuidLabManager:
    """Manages KSUID operations (generation, inspection)."""

    def _base62_encode(self, num: int, min_len: int = 27) -> str:
        if num == 0:
            return BASE62_ALPHABET[0] * min_len
        res = []
        while num > 0:
            num, rem = divmod(num, 62)
            res.append(BASE62_ALPHABET[rem])
        while len(res) < min_len:
            res.append(BASE62_ALPHABET[0])
        return "".join(reversed(res))

    def _base62_decode(self, s: str) -> int:
        num = 0
        for char in s:
            num = num * 62 + BASE62_ALPHABET.index(char)
        return num

    def generate(self, count: int = 1) -> List[str]:
        """Generates KSUIDs."""
        results = []
        for _ in range(count):
            timestamp = int(time.time()) - KSUID_EPOCH
            payload = os.urandom(16)
            packed = struct.pack(">I", timestamp) + payload
            num = int.from_bytes(packed, byteorder="big")
            k = self._base62_encode(num, 27)
            results.append(k)
        return results

    def inspect(self, ksuid_str: str) -> Dict[str, Any]:
        """Decodes and inspects a KSUID."""
        if len(ksuid_str) != 27:
            return {"valid": False, "error": "Invalid KSUID length. Must be 27 characters."}

        try:
            num = self._base62_decode(ksuid_str)
            packed = num.to_bytes(20, byteorder="big")
        except ValueError:
            return {"valid": False, "error": "Invalid KSUID format. Must be base62 encoded."}
        except OverflowError:
            return {"valid": False, "error": "Invalid KSUID format. Payload too large."}

        ts = struct.unpack(">I", packed[:4])[0]
        payload = packed[4:]

        info = {
            "valid": True,
            "ksuid": ksuid_str,
            "timestamp": ts,
            "timestamp_iso": None,
            "payload_hex": payload.hex(),
        }

        try:
            from datetime import datetime, timezone
            dt = datetime.fromtimestamp(ts + KSUID_EPOCH, tz=timezone.utc)
            info["timestamp_iso"] = dt.isoformat()
        except Exception:
            pass

        return info


def run_ksuid_lab_logic(args):
    """CLI handler for KSUID Lab."""
    manager = KsuidLabManager()

    if args.action == "generate":
        try:
            results = manager.generate(count=args.count)
            for res in results:
                print(res)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "bulk":
        try:
            results = manager.generate(count=args.count)
            for res in results:
                print(res)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "inspect":
        info = manager.inspect(args.ksuid)
        if not info["valid"]:
            print(f"Error: {info['error']}", file=sys.stderr)
            sys.exit(1)

        print(f"--- KSUID Inspection: {args.ksuid} ---")
        print(f"  Valid:         {info['valid']}")
        print(f"  Timestamp:     {info['timestamp']}")
        if info.get("timestamp_iso"):
            print(f"  Date (UTC):    {info['timestamp_iso']}")
        print(f"  Payload (Hex): {info['payload_hex']}")
