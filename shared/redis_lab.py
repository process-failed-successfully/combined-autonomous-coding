import sys
from typing import Dict, Any, List, Optional

try:
    import redis
except ImportError:
    redis = None


class RedisLabManager:
    """
    Manages Redis operations.
    """
    def __init__(self, url: str = "redis://localhost:6379/0"):
        self.url = url
        self.client = None

    def connect(self) -> bool:
        """Establishes a connection to the Redis server."""
        if redis is None:
            print("Error: 'redis' library not installed. Please run 'pip install redis'.", file=sys.stderr)
            return False

        try:
            self.client = redis.Redis.from_url(self.url, decode_responses=True)
            self.client.ping()
            return True
        except redis.ConnectionError as e:
            print(f"Error connecting to Redis at {self.url}: {e}", file=sys.stderr)
            return False
        except Exception as e:
            print(f"Unexpected error: {e}", file=sys.stderr)
            return False

    def get(self, key: str) -> Optional[str]:
        """Gets a value."""
        if not self.client and not self.connect():
            return None
        try:
            return self.client.get(key)
        except Exception as e:
            print(f"Error getting key '{key}': {e}", file=sys.stderr)
            return None

    def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """Sets a value."""
        if not self.client and not self.connect():
            return False
        try:
            return self.client.set(key, value, ex=ex)
        except Exception as e:
            print(f"Error setting key '{key}': {e}", file=sys.stderr)
            return False

    def delete(self, key: str) -> int:
        """Deletes a key."""
        if not self.client and not self.connect():
            return 0
        try:
            return self.client.delete(key)
        except Exception as e:
            print(f"Error deleting key '{key}': {e}", file=sys.stderr)
            return 0

    def keys(self, pattern: str = "*") -> List[str]:
        """Lists keys matching a pattern."""
        if not self.client and not self.connect():
            return []
        try:
            return self.client.keys(pattern)
        except Exception as e:
            print(f"Error listing keys: {e}", file=sys.stderr)
            return []

    def flush(self) -> bool:
        """Flushes the database."""
        if not self.client and not self.connect():
            return False
        try:
            return self.client.flushdb()
        except Exception as e:
            print(f"Error flushing DB: {e}", file=sys.stderr)
            return False

    def info(self) -> Dict[str, Any]:
        """Returns server info."""
        if not self.client and not self.connect():
            return {}
        try:
            return self.client.info()
        except Exception as e:
            print(f"Error getting info: {e}", file=sys.stderr)
            return {}

    def get_type(self, key: str) -> str:
        """Returns the Redis type of a key (string, list, set, zset, hash, etc.)."""
        if not self.client and not self.connect():
            return "none"
        try:
            return self.client.type(key)
        except Exception as e:
            print(f"Error getting type for '{key}': {e}", file=sys.stderr)
            return "error"

    def get_ttl(self, key: str) -> int:
        """Returns the Time-To-Live of a key."""
        if not self.client and not self.connect():
            return -2
        try:
            return self.client.ttl(key)
        except Exception as e:
            print(f"Error getting ttl for '{key}': {e}", file=sys.stderr)
            return -2

    def get_value(self, key: str) -> Any:
        """Fetches the value based on key type."""
        if not self.client and not self.connect():
            return None
        try:
            key_type = self.client.type(key)
            if key_type == "string":
                return self.client.get(key)
            elif key_type == "list":
                return self.client.lrange(key, 0, -1)
            elif key_type == "set":
                return list(self.client.smembers(key))
            elif key_type == "zset":
                return self.client.zrange(key, 0, -1, withscores=True)
            elif key_type == "hash":
                return self.client.hgetall(key)
            else:
                return f"[Unknown Type: {key_type}]"
        except Exception as e:
            print(f"Error getting value for '{key}': {e}", file=sys.stderr)
            return None

    def rename(self, old_key: str, new_key: str) -> bool:
        """Renames a key."""
        if not self.client and not self.connect():
            return False
        try:
            return self.client.rename(old_key, new_key)
        except Exception as e:
            print(f"Error renaming '{old_key}' to '{new_key}': {e}", file=sys.stderr)
            return False

    def scan_keys(self, pattern: str = "*", count: int = 100) -> List[str]:
        """Scans keys safely."""
        if not self.client and not self.connect():
            return []
        keys = []
        try:
            cursor = '0'
            while cursor != 0:
                cursor, data = self.client.scan(cursor=cursor, match=pattern, count=count)
                keys.extend(data)
                # Safeguard against huge scans in TUI, maybe limit?
                # For now, we trust the caller (TUI) to handle or paginate if needed.
                if len(keys) > 1000:  # Soft limit for TUI responsiveness
                    break
            return keys
        except Exception as e:
            print(f"Error scanning keys: {e}", file=sys.stderr)
            return []


def run_redis_lab_logic(args):
    """CLI logic for Redis Lab."""

    # Determine URL
    url = args.url or "redis://localhost:6379/0"
    manager = RedisLabManager(url)

    if args.action == "connect":
        if manager.connect():
            print(f"✅ Connected to {url}")
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
            print("(nil)")  # Standard redis-cli behavior
        sys.exit(0)

    elif args.action == "set":
        if not args.key or args.value is None:
            print("Error: --key and --value required.", file=sys.stderr)
            sys.exit(1)
        if manager.set(args.key, args.value, ex=args.ex):
            print("OK")
            sys.exit(0)
        else:
            sys.exit(1)

    elif args.action == "del":
        if not args.key:
            print("Error: --key required.", file=sys.stderr)
            sys.exit(1)
        count = manager.delete(args.key)
        print(f"(integer) {count}")
        sys.exit(0)

    elif args.action == "keys":
        keys = manager.keys(args.pattern)
        if not keys:
            print("(empty list or set)")
        else:
            for i, k in enumerate(sorted(keys)):
                print(f"{i+1}) \"{k}\"")
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

    elif args.action == "info":
        info = manager.info()
        if not info:
            sys.exit(1)

        # Print relevant sections
        # Redis-py info returns a flat dict, but keys are prefixed or standard

        # Just print everything nicely
        print(f"--- Redis Info ({url}) ---")
        print(f"Version: {info.get('redis_version', 'unknown')}")
        print(f"Mode:    {info.get('redis_mode', 'unknown')}")
        print(f"OS:      {info.get('os', 'unknown')}")
        print(f"Uptime:  {info.get('uptime_in_days', '?')} days")
        print(f"Clients: {info.get('connected_clients', '?')}")
        print(f"Memory:  {info.get('used_memory_human', '?')}")
        # db0 might be keyspace dict
        keys_count = '?'
        if isinstance(info.get('db0'), dict):
            keys_count = info.get('db0', {}).get('keys', 0)
        print(f"Keys:    {keys_count}")

        sys.exit(0)

    else:
        print(f"Unknown action: {args.action}", file=sys.stderr)
        sys.exit(1)
