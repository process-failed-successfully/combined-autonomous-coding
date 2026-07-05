import argparse
import socket
import struct
import sys
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional


class NtpLabManager:
    """Manages NTP operations: querying an NTP server and parsing the response."""

    NTP_TIMESTAMP_DELTA = 2208988800  # 1970-01-01 00:00:00 - 1900-01-01 00:00:00 in seconds

    def _ntp_to_system_time(self, timestamp: int) -> float:
        """Converts NTP 64-bit timestamp to Python system timestamp."""
        seconds = timestamp >> 32
        fraction = timestamp & 0xFFFFFFFF
        return (seconds - self.NTP_TIMESTAMP_DELTA) + (fraction / 2**32)

    def _unpack_timestamp(self, data: bytes, offset: int) -> float:
        """Unpacks an NTP timestamp from the given data and offset."""
        timestamp, = struct.unpack('!Q', data[offset:offset+8])
        if timestamp == 0:
            return 0.0
        return self._ntp_to_system_time(timestamp)

    def format_timestamp(self, ts: float) -> str:
        if ts == 0.0:
            return "0"
        return datetime.fromtimestamp(ts, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S.%f %Z')

    def query(self, server: str, port: int = 123, timeout: int = 5) -> Dict[str, Any]:
        """Queries the specified NTP server and returns the parsed data."""
        # Standard NTPv4 Client packet: 0x23 (LI=0, VN=4, Mode=3) + 47 zero bytes
        # Let's use NTPv3 (0x1b) which is more widely compatible, but v4 is fine too.
        # We will use 0x1b (VN=3).
        packet = b'\x1b' + 47 * b'\0'

        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            client.settimeout(timeout)

            t1 = time.time()
            client.sendto(packet, (server, port))
            data, address = client.recvfrom(1024)
            t4 = time.time()

            client.close()

            if len(data) < 48:
                return {"valid": False, "error": f"Invalid NTP packet received (size {len(data)})"}

            # Parse response
            # Format: ! B (LI,VN,Mode), B (Stratum), B (Poll), b (Precision), I (Root Delay), I (Root Dispersion), 4s (Ref ID)
            unpacked = struct.unpack('!B B B b I I 4s', data[:16])

            li_vn_mode = unpacked[0]
            li = (li_vn_mode >> 6) & 0x03
            vn = (li_vn_mode >> 3) & 0x07
            mode = li_vn_mode & 0x07

            stratum = unpacked[1]
            poll = unpacked[2]
            precision = unpacked[3]

            # Unpack timestamps
            ref_ts = self._unpack_timestamp(data, 16)
            orig_ts = self._unpack_timestamp(data, 24)
            recv_ts = self._unpack_timestamp(data, 32)
            tx_ts = self._unpack_timestamp(data, 40)

            # Calculate offset and delay (standard SNTP calculations)
            if orig_ts == 0.0:
                orig_ts = t1

            offset = ((recv_ts - t1) + (tx_ts - t4)) / 2
            delay = (t4 - t1) - (tx_ts - recv_ts)

            # Decode ref ID
            ref_id_bytes = unpacked[6]
            if stratum <= 1:
                # String like "GPS\0"
                ref_id = ref_id_bytes.decode('ascii', errors='ignore').strip('\x00')
            else:
                # IPv4 address
                ref_id = f"{ref_id_bytes[0]}.{ref_id_bytes[1]}.{ref_id_bytes[2]}.{ref_id_bytes[3]}"

            return {
                "valid": True,
                "server": server,
                "address": address[0],
                "leap_indicator": li,
                "version": vn,
                "mode": mode,
                "stratum": stratum,
                "poll": poll,
                "precision": precision,
                "reference_id": ref_id,
                "reference_timestamp": ref_ts,
                "origin_timestamp": orig_ts,
                "receive_timestamp": recv_ts,
                "transmit_timestamp": tx_ts,
                "offset_ms": offset * 1000,
                "delay_ms": delay * 1000
            }

        except Exception as e:
            return {"valid": False, "error": str(e)}


def run_ntp_lab_logic(args: argparse.Namespace):
    """CLI handler for NTP Lab."""
    manager = NtpLabManager()

    if args.action == "query":
        result = manager.query(args.server, port=args.port, timeout=args.timeout)

        if not result.get("valid"):
            print(f"❌ NTP Error: {result.get('error')}", file=sys.stderr)
            sys.exit(1)

        print(f"--- NTP Response from {result['server']} ({result['address']}) ---")
        print(f"  Version:         {result['version']}")
        print(f"  Mode:            {result['mode']}")
        print(f"  Leap Indicator:  {result['leap_indicator']}")
        print(f"  Stratum:         {result['stratum']}")
        print(f"  Reference ID:    {result['reference_id']}")
        print(f"  Precision:       {result['precision']}")
        print(f"  Offset:          {result['offset_ms']:.3f} ms")
        print(f"  Delay:           {result['delay_ms']:.3f} ms")

        print("\n  Timestamps:")
        print(f"    Reference: {manager.format_timestamp(result['reference_timestamp'])}")
        print(f"    Origin:    {manager.format_timestamp(result['origin_timestamp'])}")
        print(f"    Receive:   {manager.format_timestamp(result['receive_timestamp'])}")
        print(f"    Transmit:  {manager.format_timestamp(result['transmit_timestamp'])}")
        sys.exit(0)
