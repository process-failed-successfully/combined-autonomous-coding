import socket
import struct
import threading
import time
import random
import psutil
from dataclasses import dataclass
from typing import List, Callable, Optional


@dataclass
class Packet:
    timestamp: float
    src_mac: str
    dst_mac: str
    proto_l2: int  # EtherType
    src_ip: str
    dst_ip: str
    proto_l3: int  # IP Protocol
    src_port: int
    dst_port: int
    payload_len: int
    info: str
    raw_data: bytes


class PacketParser:
    """Parses raw Ethernet frames."""

    def parse(self, raw_data: bytes) -> Packet:
        timestamp = time.time()

        # Ethernet Header (14 bytes)
        if len(raw_data) < 14:
            return Packet(timestamp, "", "", 0, "", "", 0, 0, 0, 0, "Truncated", raw_data)

        eth_header = raw_data[:14]
        eth = struct.unpack('!6s6sH', eth_header)
        dst_mac = self.mac_addr(eth[0])
        src_mac = self.mac_addr(eth[1])
        proto_l2 = socket.ntohs(eth[2])

        src_ip = ""
        dst_ip = ""
        proto_l3 = 0
        src_port = 0
        dst_port = 0
        info = ""
        payload_len = len(raw_data)

        # Only parse IPv4 for now (EtherType 0x0800 -> ntohs -> 8)
        # Note: on Big Endian systems ntohs(0x0800) is 0x0800 (2048)
        # on Little Endian ntohs(0x0800) is 0x0008 (8)
        # We assume standard x86/ARM Little Endian environment mostly, but to be safe:
        # 0x0800 is 2048.
        # If we use struct.unpack('!H'), we get 2048.
        # socket.ntohs(2048) on LE is 8.
        # socket.ntohs(2048) on BE is 2048.

        is_ip = (proto_l2 == 8) or (proto_l2 == 2048)

        if is_ip and len(raw_data) >= 34:
            try:
                ip_header = raw_data[14:34]
                iph = struct.unpack('!BBHHHBBH4s4s', ip_header)

                version_ihl = iph[0]
                ihl = version_ihl & 0xF
                iph_length = ihl * 4

                # ttl = iph[5]  <-- unused
                proto_l3 = iph[6]
                src_ip = socket.inet_ntoa(iph[8])
                dst_ip = socket.inet_ntoa(iph[9])

                # Protocol Handling
                if proto_l3 == 6:  # TCP
                    if len(raw_data) >= 14 + iph_length + 20:
                        tcp_header = raw_data[14 + iph_length: 14 + iph_length + 20]
                        tcph = struct.unpack('!HHLLBBHHH', tcp_header)
                        src_port = tcph[0]
                        dst_port = tcph[1]
                        info = f"TCP {src_port} -> {dst_port} [SEQ={tcph[2]} ACK={tcph[3]}]"
                    else:
                        info = "TCP (Truncated)"

                elif proto_l3 == 17:  # UDP
                    if len(raw_data) >= 14 + iph_length + 8:
                        udp_header = raw_data[14 + iph_length: 14 + iph_length + 8]
                        udph = struct.unpack('!HHHH', udp_header)
                        src_port = udph[0]
                        dst_port = udph[1]
                        info = f"UDP {src_port} -> {dst_port} Len={udph[2]}"
                    else:
                        info = "UDP (Truncated)"

                elif proto_l3 == 1:  # ICMP
                    if len(raw_data) >= 14 + iph_length + 4:
                        icmp_header = raw_data[14 + iph_length: 14 + iph_length + 4]
                        icmph = struct.unpack('!BBH', icmp_header)
                        icmp_type = icmph[0]
                        code = icmph[1]
                        info = f"ICMP Type={icmp_type} Code={code}"
                    else:
                        info = "ICMP (Truncated)"
                else:
                    info = f"IP Proto {proto_l3}"
            except Exception:
                info = "IP Parse Error"

        else:
            info = f"EtherType {proto_l2}"

        return Packet(
            timestamp=timestamp,
            src_mac=src_mac,
            dst_mac=dst_mac,
            proto_l2=proto_l2,
            src_ip=src_ip,
            dst_ip=dst_ip,
            proto_l3=proto_l3,
            src_port=src_port,
            dst_port=dst_port,
            payload_len=payload_len,
            info=info,
            raw_data=raw_data
        )

    def mac_addr(self, a: bytes) -> str:
        return "%.2x:%.2x:%.2x:%.2x:%.2x:%.2x" % (a[0], a[1], a[2], a[3], a[4], a[5])


class SnifferManager:
    """Manages packet capture."""

    def __init__(self):
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.parser = PacketParser()
        self.sock: Optional[socket.socket] = None

    def get_interfaces(self) -> List[str]:
        """Returns list of network interfaces."""
        return list(psutil.net_if_addrs().keys())

    def start_capture(self, interface: str, callback: Callable[[Packet], None]) -> None:
        """Starts capturing packets on the given interface."""
        if self.running:
            return

        try:
            # Create raw socket (requires root/CAP_NET_ADMIN)
            if not hasattr(socket, 'AF_PACKET'):
                raise OSError("AF_PACKET not supported on this OS.")

            self.sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.ntohs(3))
            self.sock.bind((interface, 0))

        except PermissionError:
            raise PermissionError("Permission denied. Run with sudo or --privileged.")
        except Exception as e:
            raise e

        self.running = True
        self.thread = threading.Thread(target=self._capture_loop, args=(callback,), daemon=True)
        self.thread.start()

    def start_demo_capture(self, callback: Callable[[Packet], None]) -> None:
        """Starts generating fake traffic for demo purposes."""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._demo_loop, args=(callback,), daemon=True)
        self.thread.start()

    def stop_capture(self) -> None:
        """Stops the capture thread."""
        self.running = False
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None

        if self.thread and self.thread.is_alive():
            try:
                self.thread.join(timeout=1.0)
            except RuntimeError:
                pass  # Can happen if join is called from same thread

    def _capture_loop(self, callback: Callable[[Packet], None]) -> None:
        while self.running and self.sock:
            try:
                raw_data, addr = self.sock.recvfrom(65535)
                packet = self.parser.parse(raw_data)
                callback(packet)
            except OSError:
                break
            except Exception:
                continue

    def _demo_loop(self, callback: Callable[[Packet], None]) -> None:
        """Generates random fake packets."""
        while self.running:
            time.sleep(random.uniform(0.1, 1.0))

            # Pack 0x0800 (IPv4)
            # struct.pack('!H', 2048) -> b'\x08\x00'
            eth = struct.pack('!6s6sH', b'\x00' * 6, b'\xff' * 6, 2048)

            # IP Header
            src_ip = socket.inet_aton(f"192.168.1.{random.randint(1, 254)}")
            dst_ip = socket.inet_aton(f"10.0.0.{random.randint(1, 254)}")
            proto = random.choice([6, 17, 1])  # TCP, UDP, ICMP

            # Version 4, IHL 5 -> 0x45 (69)
            ip = struct.pack('!BBHHHBBH4s4s', 69, 0, 40, 54321, 0, 64, proto, 0, src_ip, dst_ip)

            payload = b"Demo Payload " + str(random.randint(0, 1000)).encode()

            raw_data = eth + ip

            if proto == 6:  # TCP
                tcp = struct.pack('!HHLLBBHHH', random.randint(1024, 65535), 80, 0, 0, 80, 0, 8192, 0, 0)
                raw_data += tcp + payload
            elif proto == 17:  # UDP
                udp = struct.pack('!HHHH', random.randint(1024, 65535), 53, 0, 0)
                raw_data += udp + payload
            else:  # ICMP
                icmp = struct.pack('!BBH', 8, 0, 0)  # Echo Request
                raw_data += icmp + payload

            packet = self.parser.parse(raw_data)
            callback(packet)
