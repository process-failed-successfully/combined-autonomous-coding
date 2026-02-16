import unittest
from unittest.mock import MagicMock, patch
from shared.whois_lab import WhoisLabManager

class TestWhoisLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = WhoisLabManager()

    @patch("socket.create_connection")
    def test_query_success(self, mock_create_connection):
        # Setup mock socket
        mock_sock = MagicMock()
        mock_create_connection.return_value.__enter__.return_value = mock_sock

        # Mock recv behavior
        # recv needs to return bytes, then empty bytes to signal EOF
        mock_sock.recv.side_effect = [b"Domain Name: example.com\n", b""]

        response = self.manager.query("example.com", "whois.iana.org")

        self.assertIn("Domain Name: example.com", response)
        mock_sock.sendall.assert_called_with(b"example.com\r\n")
        mock_create_connection.assert_called_with(("whois.iana.org", 43), timeout=10)

    @patch("socket.create_connection")
    def test_lookup_no_referral(self, mock_create_connection):
        mock_sock = MagicMock()
        mock_create_connection.return_value.__enter__.return_value = mock_sock
        mock_sock.recv.side_effect = [b"Domain Name: example.com\nNo referral here.", b""]

        result = self.manager.lookup("example.com")
        self.assertIn("Domain Name: example.com", result)
        self.assertEqual(mock_create_connection.call_count, 1)

    @patch("socket.create_connection")
    def test_lookup_with_referral(self, mock_create_connection):
        # We need distinct mock sockets for each call or complex side_effects

        # We will use side_effect on create_connection to return different mocks
        mock_sock1 = MagicMock()
        mock_sock1.recv.side_effect = [b"refer: whois.referral.com\n", b""]

        mock_sock2 = MagicMock()
        mock_sock2.recv.side_effect = [b"Domain Name: example.com\nAuthoritative Answer", b""]

        # Context managers are tricky with side_effect.
        # create_connection returns a context manager.
        # So we need objects that have __enter__ returning our mocks.

        cm1 = MagicMock()
        cm1.__enter__.return_value = mock_sock1

        cm2 = MagicMock()
        cm2.__enter__.return_value = mock_sock2

        mock_create_connection.side_effect = [cm1, cm2]

        result = self.manager.lookup("example.com")

        self.assertIn("refer: whois.referral.com", result)
        self.assertIn("Authoritative Answer", result)
        self.assertEqual(mock_create_connection.call_count, 2)

        # Verify calls
        args_list = mock_create_connection.call_args_list
        self.assertEqual(args_list[0][0][0], ("whois.iana.org", 43))
        self.assertEqual(args_list[1][0][0], ("whois.referral.com", 43))

    @patch("shared.whois_lab.WhoisLabManager.lookup")
    def test_check_availability_available(self, mock_lookup):
        mock_lookup.return_value = "No match for domain example.xyz"

        result = self.manager.check_availability("example.xyz")
        self.assertTrue(result["available"])
        self.assertEqual(result["domain"], "example.xyz")

    @patch("shared.whois_lab.WhoisLabManager.lookup")
    def test_check_availability_taken(self, mock_lookup):
        mock_lookup.return_value = "Domain Name: google.com\nRegistry Domain ID: ..."

        result = self.manager.check_availability("google.com")
        self.assertFalse(result["available"])

if __name__ == '__main__':
    unittest.main()
