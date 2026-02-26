"""
PCAP Lab
========

Utilities for analyzing PCAP (Packet Capture) files.
Parses packet headers and basic Ethernet/IP/TCP/UDP structures using struct module.
"""

import struct
import sys
import os
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Generator, Tuple
from collections import Counter

class PcapReader:
    """Reads and parses PCAP files."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.byte_order = '<'  # Default to little-endian
        self.magic_number = b''
        self.version_major = 0
        self.version_minor = 0
        self.thiszone = 0
        self.sigfigs = 0
        self.snaplen = 0
        self.network = 0  # LinkType

    def read_global_header(self, f) -> bool:
        """Reads the Global Header (24 bytes)."""
        header_fmt = 'IHHiIII'  # Default, assume standard
        header_len = 24

        data = f.read(header_len)
        if len(data) < header_len:
            return False

        # Determine byte order from magic number
        magic = data[:4]
        if magic == b'\xa1\xb2\xc3\xd4':  # Big-endian, microsecond
            self.byte_order = '>'
        elif magic == b'\xd4\xc3\xb2\xa1':  # Little-endian, microsecond
            self.byte_order = '<'
        elif magic == b'\xa1\xb2\x3c\x4d':  # Big-endian, nanosecond
            self.byte_order = '>'
        elif magic == b'\x4d\x3c\xb2\xa1':  # Little-endian, nanosecond
            self.byte_order = '<'
        else:
            # Unknown magic, default to little but warn?
            pass

        # Re-parse with correct endianness
        fmt = self.byte_order + 'IHHiIII'
        unpacked = struct.unpack(fmt, data)

        self.magic_number = magic
        self.version_major = unpacked[1]
        self.version_minor = unpacked[2]
        self.thiszone = unpacked[3]
        self.sigfigs = unpacked[4]
        self.snaplen = unpacked[5]
        self.network = unpacked[6]

        return True

    def read_packet(self, f) -> Optional[Dict[str, Any]]:
        """Reads the next packet header and data."""
        # Packet Header: 16 bytes
        # ts_sec (4), ts_usec (4), incl_len (4), orig_len (4)
        header_fmt = self.byte_order + 'IIII'
        header_len = 16

        header_data = f.read(header_len)
        if len(header_data) < header_len:
            return None

        ts_sec, ts_usec, incl_len, orig_len = struct.unpack(header_fmt, header_data)

        # Read packet data
        packet_data = f.read(incl_len)
        if len(packet_data) < incl_len:
            return None

        # Parse Ethernet/IP headers if possible (Network=1 is Ethernet)
        parsed_info = self._parse_ethernet(packet_data)

        return {
            "ts_sec": ts_sec,
            "ts_usec": ts_usec,
            "incl_len": incl_len,
            "orig_len": orig_len,
            "data": packet_data,
            "info": parsed_info
        }

    def _parse_ethernet(self, data: bytes) -> Dict[str, Any]:
        """Parses Ethernet, IP, and Transport headers."""
        info = {
            "src_mac": "00:00:00:00:00:00",
            "dst_mac": "00:00:00:00:00:00",
            "ethertype": 0,
            "src_ip": None,
            "dst_ip": None,
            "proto": None,
            "src_port": None,
            "dst_port": None,
            "summary": "Unknown"
        }

        if len(data) < 14:
            return info

        # Ethernet Header (14 bytes)
        # Dst MAC (6), Src MAC (6), EtherType (2)
        dst_mac = data[:6]
        src_mac = data[6:12]
        ethertype = struct.unpack('!H', data[12:14])[0]  # Network byte order (Big-endian)

        info["dst_mac"] = ':'.join(f'{b:02x}' for b in dst_mac)
        info["src_mac"] = ':'.join(f'{b:02x}' for b in src_mac)
        info["ethertype"] = ethertype

        # IPv4 (EtherType 0x0800)
        if ethertype == 0x0800:
            self._parse_ipv4(data[14:], info)
        # ARP (EtherType 0x0806)
        elif ethertype == 0x0806:
            info["proto"] = "ARP"
            info["summary"] = "ARP Request/Reply"
        # IPv6 (EtherType 0x86DD)
        elif ethertype == 0x86DD:
            info["proto"] = "IPv6"
            info["summary"] = "IPv6 Packet"
        else:
            info["summary"] = f"Ethernet type 0x{ethertype:04x}"

        return info

    def _parse_ipv4(self, data: bytes, info: Dict[str, Any]):
        """Parses IPv4 Header."""
        if len(data) < 20:
            return

        # First byte: Version (4 bits) + IHL (4 bits)
        ver_ihl = data[0]
        version = ver_ihl >> 4
        ihl = ver_ihl & 0x0F
        header_len = ihl * 4

        if len(data) < header_len:
            return

        # Protocol (Byte 9)
        protocol = data[9]

        # Source IP (Bytes 12-15)
        src_ip = data[12:16]
        # Dest IP (Bytes 16-19)
        dst_ip = data[16:20]

        info["src_ip"] = '.'.join(str(b) for b in src_ip)
        info["dst_ip"] = '.'.join(str(b) for b in dst_ip)

        proto_map = {1: "ICMP", 6: "TCP", 17: "UDP"}
        info["proto"] = proto_map.get(protocol, str(protocol))

        payload = data[header_len:]

        if protocol == 6: # TCP
            self._parse_tcp(payload, info)
        elif protocol == 17: # UDP
            self._parse_udp(payload, info)
        elif protocol == 1: # ICMP
            info["summary"] = "ICMP Packet"
        else:
            info["summary"] = f"IPv4 Protocol {protocol}"

    def _parse_tcp(self, data: bytes, info: Dict[str, Any]):
        """Parses TCP Header."""
        if len(data) < 20:
            return

        # Src Port (0-1), Dst Port (2-3)
        src_port, dst_port = struct.unpack('!HH', data[:4])
        info["src_port"] = src_port
        info["dst_port"] = dst_port
        info["summary"] = f"TCP {src_port} -> {dst_port}"

    def _parse_udp(self, data: bytes, info: Dict[str, Any]):
        """Parses UDP Header."""
        if len(data) < 8:
            return

        src_port, dst_port = struct.unpack('!HH', data[:4])
        info["src_port"] = src_port
        info["dst_port"] = dst_port
        info["summary"] = f"UDP {src_port} -> {dst_port}"


class PcapLabManager:
    """Manages PCAP analysis operations."""

    def analyze(self, file_path: Path) -> Dict[str, Any]:
        """Analyzes a PCAP file and returns statistics."""
        if not file_path.exists():
            return {"error": f"File not found: {file_path}"}

        stats = {
            "packet_count": 0,
            "duration": 0.0,
            "start_time": None,
            "end_time": None,
            "protocols": Counter(),
            "src_ips": Counter(),
            "dst_ips": Counter(),
            "top_talkers": []
        }

        reader = PcapReader(file_path)
        with open(file_path, "rb") as f:
            if not reader.read_global_header(f):
                return {"error": "Invalid PCAP file or empty."}

            while True:
                pkt = reader.read_packet(f)
                if not pkt:
                    break

                stats["packet_count"] += 1
                ts = pkt["ts_sec"] + (pkt["ts_usec"] / 1_000_000.0)

                if stats["start_time"] is None or ts < stats["start_time"]:
                    stats["start_time"] = ts
                if stats["end_time"] is None or ts > stats["end_time"]:
                    stats["end_time"] = ts

                info = pkt["info"]
                proto = info.get("proto") or "Other"
                stats["protocols"][proto] += 1

                if info.get("src_ip"):
                    stats["src_ips"][info["src_ip"]] += 1
                if info.get("dst_ip"):
                    stats["dst_ips"][info["dst_ip"]] += 1

        if stats["start_time"] and stats["end_time"]:
            stats["duration"] = stats["end_time"] - stats["start_time"]

        # Convert counters to dicts for JSON serialization
        stats["top_talkers"] = stats["src_ips"].most_common(5)
        # Convert counters to regular dicts
        stats["protocols"] = dict(stats["protocols"])
        stats["src_ips"] = dict(stats["src_ips"].most_common(10))
        stats["dst_ips"] = dict(stats["dst_ips"].most_common(10))

        return stats

    def list_packets(self, file_path: Path, limit: int = 20) -> Generator[Dict[str, Any], None, None]:
        """Yields packet summaries."""
        if not file_path.exists():
            return

        reader = PcapReader(file_path)
        with open(file_path, "rb") as f:
            if not reader.read_global_header(f):
                return

            count = 0
            while count < limit:
                pkt = reader.read_packet(f)
                if not pkt:
                    break

                info = pkt["info"]
                ts = time.strftime('%H:%M:%S', time.localtime(pkt["ts_sec"]))
                ts_ms = f"{ts}.{pkt['ts_usec']:06d}"

                yield {
                    "no": count + 1,
                    "time": ts_ms,
                    "src": info.get("src_ip") or info.get("src_mac"),
                    "dst": info.get("dst_ip") or info.get("dst_mac"),
                    "proto": info.get("proto") or "ETH",
                    "len": pkt["incl_len"],
                    "summary": info.get("summary")
                }
                count += 1

    def filter_packets(self, file_path: Path, proto: Optional[str] = None,
                       src: Optional[str] = None, dst: Optional[str] = None,
                       limit: int = 50) -> Generator[Dict[str, Any], None, None]:
        """Yields filtered packets."""
        if not file_path.exists():
            return

        reader = PcapReader(file_path)
        with open(file_path, "rb") as f:
            if not reader.read_global_header(f):
                return

            count = 0
            while True:
                pkt = reader.read_packet(f)
                if not pkt:
                    break

                info = pkt["info"]

                # Apply filters
                if proto and info.get("proto", "").lower() != proto.lower():
                    continue
                if src and info.get("src_ip") != src:
                    continue
                if dst and info.get("dst_ip") != dst:
                    continue

                if count >= limit:
                    break

                ts = time.strftime('%H:%M:%S', time.localtime(pkt["ts_sec"]))
                ts_ms = f"{ts}.{pkt['ts_usec']:06d}"

                yield {
                    "no": count + 1,
                    "time": ts_ms,
                    "src": info.get("src_ip") or info.get("src_mac"),
                    "dst": info.get("dst_ip") or info.get("dst_mac"),
                    "proto": info.get("proto") or "ETH",
                    "len": pkt["incl_len"],
                    "summary": info.get("summary")
                }
                count += 1


def run_pcap_lab_logic(args):
    """CLI Entry point for PCAP Lab."""
    file_path = Path(args.file)
    manager = PcapLabManager()

    if args.action == "analyze":
        print(f"--- Analyzing {file_path} ---")
        stats = manager.analyze(file_path)

        if "error" in stats:
            print(f"❌ Error: {stats['error']}")
            sys.exit(1)

        print(f"Total Packets: {stats['packet_count']}")
        print(f"Duration:      {stats['duration']:.2f} seconds")
        if stats['start_time']:
            print(f"Start Time:    {time.ctime(stats['start_time'])}")
        if stats['end_time']:
            print(f"End Time:      {time.ctime(stats['end_time'])}")

        print("\nProtocol Distribution:")
        for proto, count in stats['protocols'].items():
            print(f"  {proto:<10}: {count}")

        print("\nTop Talkers (Src IP):")
        for ip, count in stats['top_talkers']:
            print(f"  {ip:<15}: {count}")

    elif args.action == "list":
        print(f"--- Listing first {args.limit} packets from {file_path} ---")
        print(f"{'No.':<5} | {'Time':<15} | {'Source':<18} | {'Destination':<18} | {'Proto':<6} | {'Len':<5} | {'Summary'}")
        print("-" * 100)

        for pkt in manager.list_packets(file_path, limit=args.limit):
            print(f"{pkt['no']:<5} | {pkt['time']:<15} | {pkt['src']:<18} | {pkt['dst']:<18} | {pkt['proto']:<6} | {pkt['len']:<5} | {pkt['summary']}")

    elif args.action == "filter":
        print(f"--- Filtering {file_path} ---")
        filters = []
        if args.proto: filters.append(f"proto={args.proto}")
        if args.src: filters.append(f"src={args.src}")
        if args.dst: filters.append(f"dst={args.dst}")
        print(f"Filters: {', '.join(filters)}")

        print(f"{'No.':<5} | {'Time':<15} | {'Source':<18} | {'Destination':<18} | {'Proto':<6} | {'Len':<5} | {'Summary'}")
        print("-" * 100)

        for pkt in manager.filter_packets(file_path, proto=args.proto, src=args.src, dst=args.dst, limit=args.limit):
            print(f"{pkt['no']:<5} | {pkt['time']:<15} | {pkt['src']:<18} | {pkt['dst']:<18} | {pkt['proto']:<6} | {pkt['len']:<5} | {pkt['summary']}")

    sys.exit(0)
