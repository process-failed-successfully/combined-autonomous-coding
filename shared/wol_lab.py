import sys
import socket
import re
from typing import Optional

class WolLabManager:
    """
    Manages Wake-on-LAN operations.
    """

    def validate_mac(self, mac_address: str) -> str:
        """
        Validates and normalizes a MAC address.
        """
        # Remove common separators
        cleaned = re.sub(r'[:-]', '', mac_address).lower()
        if len(cleaned) != 12:
            raise ValueError(f"Invalid MAC address length: {mac_address}")

        if not re.match(r'^[0-9a-f]{12}$', cleaned):
            raise ValueError(f"Invalid characters in MAC address: {mac_address}")

        return cleaned

    def build_magic_packet(self, mac_address: str) -> bytes:
        """
        Builds the Wake-on-LAN Magic Packet.
        """
        cleaned_mac = self.validate_mac(mac_address)

        # A magic packet is 6 bytes of FF followed by 16 repetitions of the target MAC
        header = b'\xff' * 6
        mac_bytes = bytes.fromhex(cleaned_mac)
        payload = mac_bytes * 16

        return header + payload

    def wake(self, mac_address: str, ip_address: str = "255.255.255.255", port: int = 9) -> bool:
        """
        Sends the Magic Packet to the target MAC address.
        """
        try:
            packet = self.build_magic_packet(mac_address)

            # Use a UDP broadcast socket
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                sock.sendto(packet, (ip_address, port))
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to send Wake-on-LAN packet: {e}")

def run_wol_lab_logic(args) -> bool:
    """CLI logic for wol-lab."""
    manager = WolLabManager()

    try:
        print(f"Sending Wake-on-LAN Magic Packet to MAC: {args.mac} (IP: {args.ip}, Port: {args.port})")
        manager.wake(mac_address=args.mac, ip_address=args.ip, port=args.port)
        print("✅ Magic Packet sent successfully.")
        return True
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return False
