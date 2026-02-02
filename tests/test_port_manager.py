import unittest
import socket
import threading
import time
import subprocess
import sys
import psutil
from shared.port_manager import PortManager

def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

class TestPortManager(unittest.TestCase):

    def test_get_process_on_port_self(self):
        """Test finding the current process listening on a port."""
        port = get_free_port()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('127.0.0.1', port))
        sock.listen(1)

        try:
            info = PortManager.get_process_on_port(port)
            self.assertIsNotNone(info)
            self.assertEqual(info['pid'],  psutil.Process().pid)
        finally:
            sock.close()

    def test_list_listening_ports(self):
        """Test listing ports includes our port."""
        port = get_free_port()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('127.0.0.1', port))
        sock.listen(1)

        try:
            ports = PortManager.list_listening_ports()
            found = any(p['port'] == port for p in ports)
            self.assertTrue(found, f"Port {port} not found in listing")
        finally:
            sock.close()

    def test_wait_for_port_open(self):
        """Test waiting for a port to open."""
        port = get_free_port()

        def start_server():
            time.sleep(0.5)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(('127.0.0.1', port))
            s.listen(1)
            time.sleep(2) # Keep it open for a bit
            s.close()

        t = threading.Thread(target=start_server)
        t.start()

        try:
            # Should return True within timeout
            result = PortManager.wait_for_port(port, state="open", timeout=5)
            self.assertTrue(result)
        finally:
            t.join()

    def test_kill_process_on_port(self):
        """Test killing a subprocess listening on a port."""
        port = get_free_port()

        # Create a python script that listens on the port
        code = f"""
import socket
import time
import sys

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('127.0.0.1', {port}))
s.listen(1)
print("listening")
sys.stdout.flush()
while True:
    time.sleep(1)
"""
        # Start subprocess
        proc = subprocess.Popen([sys.executable, "-c", code], stdout=subprocess.PIPE, text=True)

        try:
            # Wait for it to start listening
            line = proc.stdout.readline()
            self.assertIn("listening", line)

            # Verify it's there
            info = PortManager.get_process_on_port(port)
            self.assertIsNotNone(info)
            self.assertEqual(info['pid'], proc.pid)

            # Kill it
            success = PortManager.kill_process_on_port(port)
            self.assertTrue(success)

            # Verify it's gone
            # Give it a moment to die
            try:
                gone, alive = psutil.wait_procs([psutil.Process(proc.pid)], timeout=3)
                self.assertTrue(len(gone) == 1 or proc.poll() is not None)
            except psutil.NoSuchProcess:
                # Process is already gone, which is success
                pass

        finally:
            if proc.poll() is None:
                try:
                    proc.kill()
                except OSError:
                    pass

if __name__ == '__main__':
    unittest.main()
