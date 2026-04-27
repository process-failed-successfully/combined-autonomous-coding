import argparse
import sys
import hashlib
import base64
import crypt
import os
try:
    import bcrypt
except ImportError:
    bcrypt = None

class HtpasswdManager:
    """Manages the generation of .htpasswd formatted credentials."""

    def generate(self, username: str, password: str, algorithm: str = "bcrypt") -> dict:
        """
        Generates an htpasswd entry.
        Algorithm options: bcrypt, md5, sha1, crypt, plain
        """
        if algorithm == "bcrypt":
            if not bcrypt:
                return {"success": False, "error": "bcrypt library not installed. Install with 'pip install bcrypt'."}
            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            entry = f"{username}:{hashed.decode('utf-8')}"
            return {"success": True, "entry": entry, "algorithm": algorithm}

        elif algorithm == "md5":
            # APR1-MD5 implementation (simplified or fallback to crypt if available for apr1)
            # Actually standard htpasswd -m uses apr1, which is tricky to implement without passlib.
            # We will use crypt if it supports $apr1$ or fallback to a standard md5-crypt $1$
            salt = base64.b64encode(os.urandom(6)).decode('utf-8')[:8]
            # Standard md5 crypt format
            try:
                hashed = crypt.crypt(password, f"$1${salt}$")
                entry = f"{username}:{hashed}"
                return {"success": True, "entry": entry, "algorithm": "md5-crypt"}
            except Exception as e:
                return {"success": False, "error": f"crypt.crypt MD5 failed: {e}"}

        elif algorithm == "sha1":
            # {SHA} base64(sha1(password))
            sha = hashlib.sha1(password.encode('utf-8')).digest()
            b64_sha = base64.b64encode(sha).decode('utf-8')
            entry = f"{username}:{{SHA}}{b64_sha}"
            return {"success": True, "entry": entry, "algorithm": algorithm}

        elif algorithm == "crypt":
            # standard UNIX crypt(3)
            salt = base64.b64encode(os.urandom(2)).decode('utf-8')[:2]
            try:
                hashed = crypt.crypt(password, salt)
                entry = f"{username}:{hashed}"
                return {"success": True, "entry": entry, "algorithm": algorithm}
            except Exception as e:
                return {"success": False, "error": f"crypt.crypt failed: {e}"}

        elif algorithm == "plain":
            # Not recommended, but supported
            entry = f"{username}:{password}"
            return {"success": True, "entry": entry, "algorithm": algorithm}

        else:
            return {"success": False, "error": f"Unknown algorithm: {algorithm}"}

def run_htpasswd_lab_logic(args: argparse.Namespace) -> bool:
    """CLI logic for htpasswd lab."""
    if not args.username or not args.password:
        print("Error: Username and password are required.", file=sys.stderr)
        return False

    manager = HtpasswdManager()
    result = manager.generate(args.username, args.password, algorithm=args.algorithm)

    if result["success"]:
        print(result["entry"])
        return True
    else:
        print(f"Error: {result.get('error', 'Unknown error')}", file=sys.stderr)
        return False
