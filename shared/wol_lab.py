import socket
import re
import sys
import argparse
from typing import Optional, Tuple

class WolLabManager:
    """
    Manages Wake-on-LAN operations, including creating and sending magic packets.
    """

    @staticmethod
    def _clean_mac(mac: str) -> str:
        """
        Cleans a MAC address string by removing colons, hyphens, and dots.
        Also validates that the resulting string is 12 hex characters.
        """
        cleaned = re.sub(r'[:\-.]', '', mac)
        if len(cleaned) != 12 or not all(c in '0123456789abcdefABCDEF' for c in cleaned):
            raise ValueError(f"Invalid MAC address format: {mac}")
        return cleaned

    def create_magic_packet(self, mac: str) -> bytes:
        """
        Creates a Wake-on-LAN magic packet for the given MAC address.
        The packet is 102 bytes: 6 bytes of 0xFF followed by 16 repetitions of the MAC address.
        """
        cleaned_mac = self._clean_mac(mac)

        # 6 bytes of 0xFF
        header = b'\xff' * 6

        # 16 repetitions of the MAC address
        # convert hex string to bytes
        mac_bytes = bytes.fromhex(cleaned_mac)
        payload = mac_bytes * 16

        return header + payload

    def send_magic_packet(self, mac: str, ip: str = "255.255.255.255", port: int = 9) -> bool:
        """
        Creates and sends a magic packet to the target MAC address over UDP.
        Returns True if successful.
        """
        try:
            packet = self.create_magic_packet(mac)

            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                s.sendto(packet, (ip, port))
            return True
        except Exception as e:
            print(f"Error sending magic packet: {e}", file=sys.stderr)
            return False

def run_wol_lab_logic(args: argparse.Namespace) -> None:
    """
    CLI handler for Wol Lab.
    """
    manager = WolLabManager()

    mac = args.mac
    ip = args.ip
    port = args.port

    print(f"--- Sending Wake-on-LAN Magic Packet ---")
    print(f"Target MAC: {mac}")
    print(f"Target IP:  {ip}")
    print(f"Target Port: {port}")

    success = manager.send_magic_packet(mac, ip, port)

    if success:
        print("\n✅ Magic packet sent successfully.")
        sys.exit(0)
    else:
        print("\n❌ Failed to send magic packet.", file=sys.stderr)
        sys.exit(1)
