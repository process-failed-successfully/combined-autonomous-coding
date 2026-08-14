import sys
import json
from typing import Dict, Any, List, Optional

try:
    from elasticsearch import Elasticsearch
except ImportError:
    Elasticsearch = None


class ElasticLabManager:
    """
    Manages Elasticsearch operations.
    """
    def __init__(self, host: str = "http://localhost:9200"):
        self.host = host
        self.client = None

    def connect(self) -> bool:
        """Establishes a connection to the Elasticsearch server."""
        if Elasticsearch is None:
            print("Error: 'elasticsearch' library not installed. Please run 'pip install elasticsearch'.", file=sys.stderr)
            return False

        try:
            self.client = Elasticsearch(self.host)
            # Check connection
            if not self.client.ping():
                return False
            return True
        except Exception as e:
            print(f"Error connecting to Elasticsearch at {self.host}: {e}", file=sys.stderr)
            return False

    def info(self) -> Dict[str, Any]:
        """Gets cluster info."""
        if not self.client and not self.connect():
            return {}
        try:
            return dict(self.client.info())
        except Exception as e:
            print(f"Error getting cluster info: {e}", file=sys.stderr)
            return {}

    def health(self) -> Dict[str, Any]:
        """Gets cluster health."""
        if not self.client and not self.connect():
            return {}
        try:
            return dict(self.client.cluster.health())
        except Exception as e:
            print(f"Error getting cluster health: {e}", file=sys.stderr)
            return {}

    def indices(self) -> List[Dict[str, Any]]:
        """Gets list of indices."""
        if not self.client and not self.connect():
            return []
        try:
            result = self.client.cat.indices(format="json")
            return list(result)
        except Exception as e:
            print(f"Error getting indices: {e}", file=sys.stderr)
            return []

    def search(self, index: str, query: str) -> Dict[str, Any]:
        """Runs a search query."""
        if not self.client and not self.connect():
            return {}
        try:
            # Parse query as JSON if possible
            if isinstance(query, str):
                try:
                    q = json.loads(query)
                except json.JSONDecodeError:
                    q = {"query": {"query_string": {"query": query}}}
            else:
                q = query

            result = self.client.search(index=index, **q)
            return dict(result)
        except Exception as e:
            print(f"Error searching index '{index}': {e}", file=sys.stderr)
            return {}


def run_elastic_lab_logic(args):
    """CLI logic for Elastic Lab."""

    host = args.host or "http://localhost:9200"
    manager = ElasticLabManager(host)

    if args.action == "connect":
        if manager.connect():
            print(f"✅ Connected to Elasticsearch at {host}")
            sys.exit(0)
        else:
            print(f"❌ Failed to connect to Elasticsearch at {host}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "info":
        info = manager.info()
        if not info:
            sys.exit(1)
        print(json.dumps(info, indent=2))
        sys.exit(0)

    elif args.action == "health":
        health = manager.health()
        if not health:
            sys.exit(1)
        print(json.dumps(health, indent=2))
        sys.exit(0)

    elif args.action == "indices":
        indices = manager.indices()
        if not indices:
            print("No indices found.")
            sys.exit(0)

        print(f"{'Health':<10} | {'Status':<10} | {'Index':<25} | {'Docs':<10} | {'Size'}")
        print("-" * 75)
        for idx in indices:
            health = idx.get("health", "?")
            status = idx.get("status", "?")
            index = idx.get("index", "?")
            docs = idx.get("docs.count", "0")
            size = idx.get("store.size", "0b")
            print(f"{health:<10} | {status:<10} | {index:<25} | {docs:<10} | {size}")
        sys.exit(0)

    elif args.action == "search":
        if not args.index:
            print("Error: --index required.", file=sys.stderr)
            sys.exit(1)

        query = args.query if hasattr(args, "query") and args.query else '{"query": {"match_all": {}}}'

        result = manager.search(args.index, query)
        if not result:
            sys.exit(1)

        print(json.dumps(result, indent=2))
        sys.exit(0)

    else:
        print(f"Unknown action: {args.action}", file=sys.stderr)
        sys.exit(1)
