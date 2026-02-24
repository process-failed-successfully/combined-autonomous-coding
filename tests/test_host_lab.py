import unittest
import shutil
import tempfile
import os
from pathlib import Path
from shared.host_lab import HostLabManager

class TestHostLabManager(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory
        self.test_dir = tempfile.mkdtemp()
        self.hosts_file = Path(self.test_dir) / "hosts"

        # Populate with some initial data
        with open(self.hosts_file, "w") as f:
            f.write("127.0.0.1\tlocalhost\n")
            f.write("::1\tlocalhost\n")
            f.write("# 1.2.3.4\told-host\n") # Commented entry
            f.write("10.0.0.1\tdev.local # Dev environment\n")
            f.write("\n") # Empty line
            f.write("# Just a comment\n")

        self.manager = HostLabManager(self.hosts_file)

    def tearDown(self):
        # Remove the directory after the test
        shutil.rmtree(self.test_dir)

    def test_list_entries(self):
        entries = self.manager.list_entries()

        # We expect:
        # 1. localhost (enabled)
        # 2. localhost ipv6 (enabled)
        # 3. old-host (disabled)
        # 4. dev.local (enabled)
        # 5. Empty/Comment line (comment type)

        active = [e for e in entries if e['type'] == 'entry' and e['enabled']]
        self.assertEqual(len(active), 3) # localhost, localhost ipv6, dev.local

        disabled = [e for e in entries if e['type'] == 'entry' and not e['enabled']]
        # Wait, my parsing logic in list_entries treats lines starting with # as active=False if they parse as IP host
        # "# 1.2.3.4 old-host" -> IP=1.2.3.4, Host=old-host, Enabled=False

        # Let's verify the disabled entry
        found_disabled = False
        for e in entries:
             if e['type'] == 'entry' and not e['enabled'] and 'old-host' in e['hosts']:
                 found_disabled = True
                 self.assertEqual(e['ip'], '1.2.3.4')
        self.assertTrue(found_disabled)

        # Verify comment extraction
        dev_entry = next(e for e in active if 'dev.local' in e['hosts'])
        self.assertEqual(dev_entry['comment'], 'Dev environment')

    def test_add_entry(self):
        success = self.manager.add_entry("192.168.1.50", "staging.local", "Staging Server")
        self.assertTrue(success)

        # Verify content
        with open(self.hosts_file, "r") as f:
            content = f.read()

        self.assertIn("192.168.1.50\tstaging.local\t# Staging Server", content)

        # Test duplicate prevention
        success_dup = self.manager.add_entry("192.168.1.51", "staging.local")
        self.assertFalse(success_dup)

    def test_remove_entry(self):
        # Remove active entry
        success = self.manager.remove_entry("dev.local")
        self.assertTrue(success)

        with open(self.hosts_file, "r") as f:
            content = f.read()
        self.assertNotIn("dev.local", content)

        # Remove commented entry
        success = self.manager.remove_entry("old-host")
        self.assertTrue(success)

        with open(self.hosts_file, "r") as f:
            content = f.read()
        self.assertNotIn("old-host", content)

        # Remove non-existent
        success = self.manager.remove_entry("non-existent.local")
        self.assertFalse(success)

    def test_toggle_entry(self):
        # Disable
        success = self.manager.toggle_entry("dev.local")
        self.assertTrue(success)

        with open(self.hosts_file, "r") as f:
            lines = f.readlines()

        # Should be commented out
        found = False
        for line in lines:
            if "dev.local" in line and line.strip().startswith("#"):
                found = True
        self.assertTrue(found)

        # Enable back
        success = self.manager.toggle_entry("dev.local")
        self.assertTrue(success)

        with open(self.hosts_file, "r") as f:
            lines = f.readlines()

        found = False
        for line in lines:
            if "dev.local" in line and not line.strip().startswith("#"):
                found = True
        self.assertTrue(found)

    def test_backup(self):
        backup_path = self.manager.backup()
        self.assertIsNotNone(backup_path)
        self.assertTrue(backup_path.exists())
        self.assertTrue(backup_path.name.startswith("hosts.bak."))

    def test_check_host(self):
        # Mocking socket.gethostbyname would be ideal, but for integration let's try localhost
        res = self.manager.check_host("localhost")
        self.assertEqual(res['status'], 'ok')
        self.assertIn(res['ip'], ['127.0.0.1', '::1'])

        res_fail = self.manager.check_host("non-existent-domain-12345.local")
        self.assertEqual(res_fail['status'], 'error')

if __name__ == '__main__':
    unittest.main()
