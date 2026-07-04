import sys
from typing import Dict, Any, List, Optional, Tuple

try:
    import pymemcache
    from pymemcache.client.base import Client
except ImportError:
    pymemcache = None
    Client = None


class MemcachedLabManager:
    """
    Manages Memcached operations.
    """
    def __init__(self, host: str = "localhost", port: int = 11211):
        self.host = host
        self.port = port
        self.client = None

    def connect(self) -> bool:
        """Establishes a connection to the Memcached server."""
        if pymemcache is None:
            print("Error: 'pymemcache' library not installed. Please run 'pip install pymemcache'.", file=sys.stderr)
            return False

        try:
            self.client = Client((self.host, self.port))
            # Ping by getting a dummy key
            self.client.get('__ping__')
            return True
        except Exception as e:
            print(f"Error connecting to Memcached at {self.host}:{self.port}: {e}", file=sys.stderr)
            return False

    def get(self, key: str) -> Optional[str]:
        """Gets a value."""
        if not self.client and not self.connect():
            return None
        try:
            val = self.client.get(key)
            if val is not None:
                return val.decode('utf-8') if isinstance(val, bytes) else str(val)
            return None
        except Exception as e:
            print(f"Error getting key '{key}': {e}", file=sys.stderr)
            return None

    def set(self, key: str, value: str, ex: int = 0) -> bool:
        """Sets a value."""
        if not self.client and not self.connect():
            return False
        try:
            # pymemcache expects bytes or string
            return self.client.set(key, value.encode('utf-8'), expire=ex)
        except Exception as e:
            print(f"Error setting key '{key}': {e}", file=sys.stderr)
            return False

    def delete(self, key: str) -> bool:
        """Deletes a key."""
        if not self.client and not self.connect():
            return False
        try:
            # delete returns True if deleted, False if not found (in some versions, or None)
            res = self.client.delete(key)
            return True if res is not False else False
        except Exception as e:
            print(f"Error deleting key '{key}': {e}", file=sys.stderr)
            return False

    def flush(self) -> bool:
        """Flushes the database."""
        if not self.client and not self.connect():
            return False
        try:
            self.client.flush_all()
            return True
        except Exception as e:
            print(f"Error flushing Memcached: {e}", file=sys.stderr)
            return False

    def stats(self) -> Dict[str, Any]:
        """Returns server stats."""
        if not self.client and not self.connect():
            return {}
        try:
            stats = self.client.stats()
            # Keys are bytes, convert to string
            result = {}
            for k, v in stats.items():
                k_str = k.decode('utf-8') if isinstance(k, bytes) else str(k)
                v_str = v.decode('utf-8') if isinstance(v, bytes) else str(v)
                result[k_str] = v_str
            return result
        except Exception as e:
            print(f"Error getting stats: {e}", file=sys.stderr)
            return {}


def run_memcached_lab_logic(args):
    """CLI logic for Memcached Lab."""

    # Parse host/port
    host = args.host or "localhost"
    port = args.port or 11211

    manager = MemcachedLabManager(host, port)

    if args.action == "connect":
        if manager.connect():
            print(f"✅ Connected to Memcached at {host}:{port}")
            sys.exit(0)
        else:
            sys.exit(1)

    elif args.action == "get":
        if not args.key:
            print("Error: --key required.", file=sys.stderr)
            sys.exit(1)
        val = manager.get(args.key)
        if val is not None:
            print(val)
        else:
            print("(nil)")
        sys.exit(0)

    elif args.action == "set":
        if not args.key or args.value is None:
            print("Error: --key and --value required.", file=sys.stderr)
            sys.exit(1)
        if manager.set(args.key, args.value, ex=args.ex):
            print("STORED")
            sys.exit(0)
        else:
            print("NOT_STORED", file=sys.stderr)
            sys.exit(1)

    elif args.action == "del":
        if not args.key:
            print("Error: --key required.", file=sys.stderr)
            sys.exit(1)
        success = manager.delete(args.key)
        if success:
            print("DELETED")
        else:
            print("NOT_FOUND")
        sys.exit(0)

    elif args.action == "flush":
        if not args.force:
            confirm = input("Are you sure you want to flush the database? [y/N]: ").strip().lower()
            if confirm != 'y':
                print("Aborted.")
                sys.exit(0)

        if manager.flush():
            print("OK")
            sys.exit(0)
        else:
            sys.exit(1)

    elif args.action == "stats":
        stats = manager.stats()
        if not stats:
            sys.exit(1)

        print(f"--- Memcached Stats ({host}:{port}) ---")
        for k, v in sorted(stats.items()):
            print(f"{k}: {v}")
        sys.exit(0)

    else:
        print(f"Unknown action: {args.action}", file=sys.stderr)
        sys.exit(1)
