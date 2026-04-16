import sys
import json
from typing import Dict, Any, List, Optional

try:
    import pymongo
    from bson.objectid import ObjectId
except ImportError:
    pymongo = None


class MongoLabManager:
    """
    Manages MongoDB operations.
    """
    def __init__(self, uri: str = "mongodb://localhost:27017/"):
        self.uri = uri
        self.client = None

    def connect(self) -> bool:
        """Establishes a connection to the MongoDB server."""
        if pymongo is None:
            print("Error: 'pymongo' library not installed. Please run 'pip install pymongo'.", file=sys.stderr)
            return False

        try:
            self.client = pymongo.MongoClient(self.uri, serverSelectionTimeoutMS=5000)
            # The ismaster command is cheap and does not require auth.
            self.client.admin.command('ismaster')
            return True
        except Exception as e:
            print(f"Error connecting to MongoDB at {self.uri}: {e}", file=sys.stderr)
            self.client = None
            return False

    def list_dbs(self) -> List[str]:
        """Lists all database names."""
        if not self.client and not self.connect():
            return []
        try:
            return self.client.list_database_names()
        except Exception as e:
            print(f"Error listing databases: {e}", file=sys.stderr)
            return []

    def list_cols(self, db_name: str) -> List[str]:
        """Lists all collection names in a given database."""
        if not self.client and not self.connect():
            return []
        try:
            db = self.client[db_name]
            return db.list_collection_names()
        except Exception as e:
            print(f"Error listing collections for db '{db_name}': {e}", file=sys.stderr)
            return []

    def find(self, db_name: str, col_name: str, query: Dict[str, Any] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Finds documents in a collection matching a query."""
        if not self.client and not self.connect():
            return []
        if query is None:
            query = {}

        try:
            db = self.client[db_name]
            col = db[col_name]
            cursor = col.find(query).limit(limit)
            results = []
            for doc in cursor:
                if '_id' in doc and isinstance(doc['_id'], ObjectId):
                    doc['_id'] = str(doc['_id'])
                results.append(doc)
            return results
        except Exception as e:
            print(f"Error executing find query: {e}", file=sys.stderr)
            return []

    def insert(self, db_name: str, col_name: str, document: Dict[str, Any]) -> Optional[str]:
        """Inserts a document into a collection."""
        if not self.client and not self.connect():
            return None
        try:
            db = self.client[db_name]
            col = db[col_name]
            result = col.insert_one(document)
            return str(result.inserted_id)
        except Exception as e:
            print(f"Error inserting document: {e}", file=sys.stderr)
            return None

    def delete(self, db_name: str, col_name: str, query: Dict[str, Any]) -> int:
        """Deletes documents matching a query."""
        if not self.client and not self.connect():
            return 0
        try:
            db = self.client[db_name]
            col = db[col_name]
            result = col.delete_many(query)
            return result.deleted_count
        except Exception as e:
            print(f"Error deleting documents: {e}", file=sys.stderr)
            return 0


def _parse_json(json_str: str) -> Dict[str, Any]:
    if not json_str:
        return {}
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)


def run_mongo_lab_logic(args) -> bool:
    """CLI logic for MongoDB Lab."""

    uri = getattr(args, 'uri', None) or "mongodb://localhost:27017/"
    manager = MongoLabManager(uri)

    if args.action == "connect":
        if manager.connect():
            print(f"✅ Connected to {uri}")
            return True
        else:
            return False

    elif args.action == "list-dbs":
        dbs = manager.list_dbs()
        if dbs:
            for i, db in enumerate(sorted(dbs)):
                print(f"{i+1}) \"{db}\"")
        else:
            print("(empty)")
        return True

    elif args.action == "list-cols":
        if not args.db:
            print("Error: --db required.", file=sys.stderr)
            return False
        cols = manager.list_cols(args.db)
        if cols:
            for i, col in enumerate(sorted(cols)):
                print(f"{i+1}) \"{col}\"")
        else:
            print("(empty)")
        return True

    elif args.action == "find":
        if not args.db or not args.col:
            print("Error: --db and --col required.", file=sys.stderr)
            return False

        query = _parse_json(getattr(args, 'query', "{}"))
        limit = getattr(args, 'limit', 50)

        docs = manager.find(args.db, args.col, query, limit)
        if docs:
            print(json.dumps(docs, indent=2))
        else:
            print("[]")
        return True

    elif args.action == "insert":
        if not args.db or not args.col or not args.doc:
            print("Error: --db, --col, and --doc required.", file=sys.stderr)
            return False

        doc = _parse_json(args.doc)
        inserted_id = manager.insert(args.db, args.col, doc)
        if inserted_id:
            print(f"Inserted document with ID: {inserted_id}")
            return True
        else:
            return False

    elif args.action == "delete":
        if not args.db or not args.col or not args.query:
            print("Error: --db, --col, and --query required.", file=sys.stderr)
            return False

        query = _parse_json(args.query)
        if not query:
            print("Error: query cannot be empty for delete. Safety first.", file=sys.stderr)
            return False

        deleted_count = manager.delete(args.db, args.col, query)
        print(f"Deleted {deleted_count} document(s).")
        return True

    else:
        print(f"Unknown action: {args.action}", file=sys.stderr)
        return False
