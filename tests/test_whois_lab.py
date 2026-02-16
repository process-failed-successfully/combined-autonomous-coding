import unittest
from unittest.mock import MagicMock, patch
from shared.whois_lab import WhoisLabManager

class TestWhoisLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = WhoisLabManager()

    @patch("socket.create_connection")
    def test_lookup_simple(self, mock_create_connection):
        # Mock socket
        mock_socket = MagicMock()
        mock_create_connection.return_value.__enter__.return_value = mock_socket

        # Simulate response
        mock_socket.recv.side_effect = [b"Domain Name: EXAMPLE.COM\n", b""]

        result = self.manager.lookup("example.com")

        self.assertEqual(result["domain"], "example.com")
        self.assertIn("whois.iana.org", result["chain"])
        self.assertIn("Domain Name: EXAMPLE.COM", result["content"])

        # Verify socket calls
        mock_create_connection.assert_called_with(("whois.iana.org", 43), timeout=10)
        mock_socket.sendall.assert_called_with(b"example.com\r\n")

    @patch("socket.create_connection")
    def test_lookup_referral(self, mock_create_connection):
        # Mock socket
        mock_socket = MagicMock()
        mock_create_connection.return_value.__enter__.return_value = mock_socket

        # Simulate referral response from IANA, then final response
        def recv_side_effect(size):
            # This is tricky because we reuse the mock for multiple calls.
            # We can use side_effect on create_connection to return different mocks,
            # or just manage the recv side_effect carefully if we knew the order.
            # But the manager creates a NEW connection each time.
            pass

        # Better approach: mock create_connection to return different context managers
        # or use side_effect on the context manager return value.

        mock_socket_1 = MagicMock()
        mock_socket_1.recv.side_effect = [b"refer: whois.verisign-grs.com\n", b""]

        mock_socket_2 = MagicMock()
        mock_socket_2.recv.side_effect = [b"Domain Name: GOOGLE.COM\n", b""]

        # Configure create_connection to return different sockets
        # create_connection returns a context manager (the object with __enter__)
        # So we need two mocks that act as context managers

        cm_1 = MagicMock()
        cm_1.__enter__.return_value = mock_socket_1

        cm_2 = MagicMock()
        cm_2.__enter__.return_value = mock_socket_2

        mock_create_connection.side_effect = [cm_1, cm_2]

        result = self.manager.lookup("google.com")

        self.assertEqual(len(result["chain"]), 2)
        self.assertEqual(result["chain"][0], "whois.iana.org")
        self.assertEqual(result["chain"][1], "whois.verisign-grs.com")
        self.assertIn("Domain Name: GOOGLE.COM", result["content"])

    @patch("shared.whois_lab.WhoisLabManager.lookup")
    def test_check_availability_available(self, mock_lookup):
        mock_lookup.return_value = {
            "domain": "available.com",
            "chain": [],
            "content": "No match for domain \"AVAILABLE.COM\"."
        }

        result = self.manager.check_availability("available.com")
        self.assertTrue(result["available"])

    @patch("shared.whois_lab.WhoisLabManager.lookup")
    def test_check_availability_taken(self, mock_lookup):
        mock_lookup.return_value = {
            "domain": "taken.com",
            "chain": [],
            "content": "Domain Name: TAKEN.COM"
        }

        result = self.manager.check_availability("taken.com")
        self.assertFalse(result["available"])

if __name__ == "__main__":
    unittest.main()
