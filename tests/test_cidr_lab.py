import unittest
from shared.cidr_lab import CidrLabManager

class TestCidrLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = CidrLabManager()

    def test_get_info_valid_ipv4(self):
        info = self.manager.get_info("192.168.1.0/24")
        self.assertNotIn("error", info)
        self.assertEqual(info["cidr"], "192.168.1.0/24")
        self.assertEqual(info["netmask"], "255.255.255.0")
        self.assertEqual(info["num_addresses"], 256)
        self.assertEqual(info["first_host"], "192.168.1.1")
        self.assertEqual(info["last_host"], "192.168.1.254")

    def test_get_info_invalid_cidr(self):
        info = self.manager.get_info("invalid")
        self.assertIn("error", info)

    def test_contains_ip(self):
        result = self.manager.contains("10.0.0.0/8", "10.1.2.3")
        self.assertNotIn("error", result)
        self.assertTrue(result["contains"])
        self.assertEqual(result["type"], "address")

    def test_not_contains_ip(self):
        result = self.manager.contains("10.0.0.0/8", "192.168.1.1")
        self.assertNotIn("error", result)
        self.assertFalse(result["contains"])

    def test_contains_subnet(self):
        result = self.manager.contains("10.0.0.0/8", "10.1.0.0/16")
        self.assertNotIn("error", result)
        self.assertTrue(result["contains"])
        self.assertEqual(result["type"], "network")

    def test_overlaps_true(self):
        result = self.manager.overlaps("192.168.1.0/24", "192.168.0.0/16")
        self.assertNotIn("error", result)
        self.assertTrue(result["overlaps"])

    def test_overlaps_false(self):
        result = self.manager.overlaps("192.168.1.0/24", "10.0.0.0/8")
        self.assertNotIn("error", result)
        self.assertFalse(result["overlaps"])

    def test_subnet(self):
        result = self.manager.subnet("192.168.1.0/24", 25)
        self.assertNotIn("error", result)
        self.assertEqual(result["count"], 2)
        self.assertIn("192.168.1.0/25", result["subnets"])
        self.assertIn("192.168.1.128/25", result["subnets"])

    def test_subnet_invalid_prefix(self):
        result = self.manager.subnet("192.168.1.0/24", 23) # Smaller prefix than current
        self.assertIn("error", result)

if __name__ == '__main__':
    unittest.main()
