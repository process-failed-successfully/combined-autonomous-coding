import socket
import sys
import re
from typing import Optional, List, Dict, Any

class WhoisLabManager:
    """
    Manages WHOIS lookups and domain availability checks.
    """

    def __init__(self):
        self.default_server = "whois.iana.org"
        self.port = 43
        self.timeout = 10

    def query(self, domain: str, server: str) -> str:
        """
        Performs a raw WHOIS query to the specified server.
        """
        response = b""
        try:
            with socket.create_connection((server, self.port), timeout=self.timeout) as s:
                s.sendall((domain + "\r\n").encode("utf-8"))
                while True:
                    data = s.recv(4096)
                    if not data:
                        break
                    response += data
        except Exception as e:
            return f"Error: {e}"

        try:
            return response.decode("utf-8", errors="ignore")
        except Exception:
             return response.decode("latin-1", errors="ignore")

    def lookup(self, domain: str, server: Optional[str] = None) -> str:
        """
        Performs a recursive WHOIS lookup, following referrals.
        """
        current_server = server or self.default_server
        trace = []

        # Avoid loops
        visited = set()

        # Max depth
        for _ in range(5):
            if current_server in visited:
                break
            visited.add(current_server)

            output = self.query(domain, current_server)
            trace.append(f"--- {current_server} ---")
            trace.append(output)

            # Check for error in output
            if "Error:" in output and len(output) < 50: # Simple heuristic
                return output

            # Try to find referral
            # Common patterns:
            # refer: whois.nic.co
            # Whois Server: whois.verisign-grs.com
            # Registrar Whois: whois.godaddy.com

            referral = None

            # Pattern 1: refer: <server> (IANA)
            match = re.search(r"refer:\s*([a-zA-Z0-9.-]+)", output, re.IGNORECASE)
            if match:
                referral = match.group(1)

            # Pattern 2: Whois Server: <server> (Verisign, etc)
            if not referral:
                match = re.search(r"Whois Server:\s*([a-zA-Z0-9.-]+)", output, re.IGNORECASE)
                if match:
                    referral = match.group(1)

            # Pattern 3: Registrar WHOIS Server: <server>
            if not referral:
                 match = re.search(r"Registrar WHOIS Server:\s*([a-zA-Z0-9.-]+)", output, re.IGNORECASE)
                 if match:
                     referral = match.group(1)

            if referral and referral != current_server:
                current_server = referral
            else:
                # No referral found, this is the authoritative answer (or we don't know where to go next)
                break

        return "\n".join(trace)

    def check_availability(self, domain: str) -> Dict[str, Any]:
        """
        Checks if a domain is available by analyzing WHOIS output.
        """
        output = self.lookup(domain)

        # Common patterns indicating availability
        # Note: This is not exhaustive and depends on the TLD.
        availability_patterns = [
            r"No match",
            r"Not found",
            r"DOMAIN NOT FOUND",
            r"No entries found",
            r"Status: free",
            r"Status: AVAILABLE",
            r"is available for registration",
            r"Object does not exist"
        ]

        available = False
        for pattern in availability_patterns:
            if re.search(pattern, output, re.IGNORECASE):
                available = True
                break

        return {
            "domain": domain,
            "available": available,
            "output": output
        }

def run_whois_lab_logic(args):
    """
    CLI entry point for Whois Lab.
    """
    manager = WhoisLabManager()

    if args.action == "lookup":
        print(f"--- WHOIS Lookup: {args.domain} ---")
        result = manager.lookup(args.domain, args.server)
        print(result)
        sys.exit(0)

    elif args.action == "check":
        print(f"--- Checking availability: {args.domain} ---")
        result = manager.check_availability(args.domain)

        if result["available"]:
            print(f"✅ Domain '{args.domain}' appears to be AVAILABLE.")
        else:
            print(f"❌ Domain '{args.domain}' appears to be TAKEN (or status unknown).")

        if args.verbose:
            print("\n--- Raw Output ---")
            print(result["output"])

        sys.exit(0 if result["available"] else 1)

    else:
        print(f"Unknown action: {args.action}", file=sys.stderr)
        sys.exit(1)
