import socket
import re
import sys
from typing import Optional, Dict, Any, List

class WhoisLabManager:
    """
    Manages WHOIS queries using raw TCP sockets on port 43.
    Supports recursive referrals.
    """
    def __init__(self):
        self.iana_server = "whois.iana.org"
        self.port = 43
        self.timeout = 10

    def _query(self, server: str, query: str) -> str:
        """
        Performs a raw WHOIS query against a specific server.
        """
        try:
            with socket.create_connection((server, self.port), timeout=self.timeout) as sock:
                # WHOIS protocol: <query>\r\n
                sock.sendall(f"{query}\r\n".encode("utf-8"))

                # Read response
                response = b""
                while True:
                    data = sock.recv(4096)
                    if not data:
                        break
                    response += data

                return response.decode("utf-8", errors="ignore")
        except Exception as e:
            return f"Error querying {server}: {str(e)}"

    def lookup(self, domain: str) -> Dict[str, Any]:
        """
        Performs a recursive WHOIS lookup.
        Starts at IANA, follows referrals.
        """
        # 1. Query IANA to find the TLD server
        tld_server = self.iana_server
        current_server = tld_server
        full_response = ""
        referral_chain = []

        # We limit recursion depth to avoid loops
        for _ in range(5):
            response = self._query(current_server, domain)
            full_response += f"\n--- Response from {current_server} ---\n{response}"
            referral_chain.append(current_server)

            # Check for referral
            # Common patterns:
            # "refer: whois.nic.google"
            # "whois: whois.nic.google"
            # "ReferralServer: whois://whois.nic.google"

            # Simple regex for referral
            # We look for lines starting with 'refer:' or 'whois:' or 'ReferralServer:'
            # and extract the hostname.

            new_server = None

            # Pattern 1: refer: <server>
            match = re.search(r"(?i)^(?:refer|whois|ReferralServer):\s*(?:whois://)?([a-zA-Z0-9.-]+)", response, re.MULTILINE)
            if match:
                new_server = match.group(1).strip()

            if not new_server:
                # Sometimes it's embedded in text, but let's stick to standard headers first.
                # If no referral, we are done.
                break

            if new_server == current_server:
                # Avoid self-referral loop
                break

            current_server = new_server

        return {
            "domain": domain,
            "chain": referral_chain,
            "content": full_response
        }

    def check_availability(self, domain: str) -> Dict[str, Any]:
        """
        Checks if a domain is available by looking for 'not found' patterns.
        """
        result = self.lookup(domain)
        content = result["content"].lower()

        # Common "not found" patterns
        not_found_patterns = [
            "no match",
            "not found",
            "no entries found",
            "status: free",
            "no data found",
            "domain not found"
        ]

        is_available = any(pattern in content for pattern in not_found_patterns)

        return {
            "domain": domain,
            "available": is_available,
            "chain": result["chain"]
        }

def run_whois_lab_logic(args):
    """
    CLI entry point for WHOIS Lab.
    """
    manager = WhoisLabManager()

    if args.action == "lookup":
        print(f"--- WHOIS Lookup: {args.domain} ---")
        result = manager.lookup(args.domain)
        print(f"Referral Chain: {' -> '.join(result['chain'])}")
        print(result['content'])
        sys.exit(0)

    elif args.action == "check":
        print(f"--- WHOIS Availability Check: {args.domain} ---")
        result = manager.check_availability(args.domain)
        status = "AVAILABLE" if result['available'] else "TAKEN (or unknown)"
        color = "\033[92m" if result['available'] else "\033[91m"
        reset = "\033[0m"

        print(f"Domain: {args.domain}")
        print(f"Status: {color}{status}{reset}")
        print(f"Checked via: {' -> '.join(result['chain'])}")
        sys.exit(0)

    else:
        print(f"Unknown action: {args.action}", file=sys.stderr)
        sys.exit(1)
