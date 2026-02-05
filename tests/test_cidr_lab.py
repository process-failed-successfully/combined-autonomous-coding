import unittest
from shared.cidr_lab import CidrLabManager

class TestCidrLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = CidrLabManager()

    def test_get_info_valid(self):
        """Test getting info for a valid CIDR."""
        result = self.manager.get_info("192.168.1.0/24")
        self.assertTrue(result["success"])
        self.assertEqual(result["network"], "192.168.1.0/24")
        self.assertEqual(result["netmask"], "255.255.255.0")
        self.assertEqual(result["num_hosts"], 256)
        self.assertEqual(result["usable_hosts"], 254)
        self.assertEqual(result["first_ip"], "192.168.1.1")
        self.assertEqual(result["last_ip"], "192.168.1.254")
        self.assertTrue(result["is_private"])

    def test_get_info_invalid(self):
        """Test getting info for an invalid CIDR."""
        result = self.manager.get_info("invalid_cidr")
        self.assertFalse(result["success"])
        self.assertIn("error", result)

    def test_check_contains_ip(self):
        """Test checking if a network contains an IP."""
        result = self.manager.check_contains("10.0.0.0/8", "10.1.2.3")
        self.assertTrue(result["success"])
        self.assertTrue(result["contains"])

        result = self.manager.check_contains("10.0.0.0/8", "11.1.2.3")
        self.assertTrue(result["success"])
        self.assertFalse(result["contains"])

    def test_check_contains_subnet(self):
        """Test checking if a network contains another subnet."""
        result = self.manager.check_contains("10.0.0.0/8", "10.1.0.0/16")
        self.assertTrue(result["success"])
        self.assertTrue(result["contains"])

        result = self.manager.check_contains("10.0.0.0/16", "10.0.0.0/8")
        self.assertTrue(result["success"])
        self.assertFalse(result["contains"])

    def test_check_overlap(self):
        """Test checking if two subnets overlap."""
        # Overlapping
        result = self.manager.check_overlap("192.168.1.0/24", "192.168.1.128/25")
        self.assertTrue(result["success"])
        self.assertTrue(result["overlaps"])

        # Not overlapping
        result = self.manager.check_overlap("192.168.1.0/24", "192.168.2.0/24")
        self.assertTrue(result["success"])
        self.assertFalse(result["overlaps"])

    def test_split_subnet(self):
        """Test splitting a subnet."""
        result = self.manager.split_subnet("192.168.1.0/24", 25)
        self.assertTrue(result["success"])
        self.assertEqual(result["count"], 2)
        self.assertIn("192.168.1.0/25", result["subnets"])
        self.assertIn("192.168.1.128/25", result["subnets"])

    def test_split_subnet_invalid_prefix(self):
        """Test splitting a subnet with an invalid prefix."""
        result = self.manager.split_subnet("192.168.1.0/24", 23)
        self.assertFalse(result["success"])
        self.assertIn("error", result)

if __name__ == '__main__':
    unittest.main()
