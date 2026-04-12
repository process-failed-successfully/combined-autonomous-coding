import sys
import json
from typing import Dict, Any, List, Optional

try:
    import pymongo
    from pymongo.errors import ConnectionFailure, PyMongoError
    from bson.objectid import ObjectId
    from bson import json_util
except ImportError:
    pymongo = None
    ConnectionFailure = Exception
    PyMongoError = Exception
    ObjectId = None
    json_util = None


class MongoLabManager:
    """
    Manages MongoDB operations.
    """
    def __init__(self, url: str = "mongodb://localhost:27017/"):
        self.url = url
        self.client = None

    def connect(self) -> bool:
        """Establishes a connection to the MongoDB server."""
        if pymongo is None:
            print("Error: 'pymongo' library not installed. Please run 'pip install pymongo'.", file=sys.stderr)
            return False

        try:
            self.client = pymongo.MongoClient(self.url, serverSelectionTimeoutMS=2000)
            self.client.admin.command('ping')
            return True
        except ConnectionFailure as e:
            print(f"Error connecting to MongoDB at {self.url}: {e}", file=sys.stderr)
            return False
        except Exception as e:
            print(f"Unexpected error: {e}", file=sys.stderr)
            return False

    def list_dbs(self) -> List[str]:
        """Lists databases."""
        if not self.client and not self.connect():
            return []
        try:
            return self.client.list_database_names()
        except PyMongoError as e:
            print(f"Error listing databases: {e}", file=sys.stderr)
            return []

    def list_cols(self, db_name: str) -> List[str]:
        """Lists collections in a database."""
        if not self.client and not self.connect():
            return []
        try:
            db = self.client[db_name]
            return db.list_collection_names()
        except PyMongoError as e:
            print(f"Error listing collections for db '{db_name}': {e}", file=sys.stderr)
            return []

    def find(self, db_name: str, col_name: str, query: Dict[str, Any] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Finds documents in a collection."""
        if query is None:
            query = {}
        if not self.client and not self.connect():
            return []
        try:
            db = self.client[db_name]
            col = db[col_name]
            cursor = col.find(query).limit(limit)
            return list(cursor)
        except PyMongoError as e:
            print(f"Error finding documents: {e}", file=sys.stderr)
            return []

    def insert(self, db_name: str, col_name: str, doc: Dict[str, Any]) -> str:
        """Inserts a document."""
        if not self.client and not self.connect():
            return ""
        try:
            db = self.client[db_name]
            col = db[col_name]
            result = col.insert_one(doc)
            return str(result.inserted_id)
        except PyMongoError as e:
            print(f"Error inserting document: {e}", file=sys.stderr)
            return ""

    def delete(self, db_name: str, col_name: str, doc_id: str) -> bool:
        """Deletes a document by its ID."""
        if not self.client and not self.connect():
            return False
        if ObjectId is None:
            return False
        try:
            db = self.client[db_name]
            col = db[col_name]
            result = col.delete_one({"_id": ObjectId(doc_id)})
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error deleting document: {e}", file=sys.stderr)
            return False

def run_mongo_lab_logic(args):
    """CLI logic for Mongo Lab."""

    # Determine URL
    url = args.url or "mongodb://localhost:27017/"
    manager = MongoLabManager(url)

    if args.action == "connect":
        if manager.connect():
            print(f"✅ Connected to {url}")
            sys.exit(0)
        else:
            sys.exit(1)

    elif args.action == "list-dbs":
        dbs = manager.list_dbs()
        if dbs:
            for db in sorted(dbs):
                print(db)
        sys.exit(0)

    elif args.action == "list-cols":
        if not args.db:
            print("Error: --db required.", file=sys.stderr)
            sys.exit(1)
        cols = manager.list_cols(args.db)
        if cols:
            for col in sorted(cols):
                print(col)
        sys.exit(0)

    elif args.action == "find":
        if not args.db or not args.col:
            print("Error: --db and --col required.", file=sys.stderr)
            sys.exit(1)

        query = {}
        if hasattr(args, "query") and args.query:
             try:
                 query = json_util.loads(args.query) if json_util else json.loads(args.query)
             except Exception as e:
                 print(f"Error parsing query: {e}", file=sys.stderr)
                 sys.exit(1)

        limit = getattr(args, "limit", 100)
        docs = manager.find(args.db, args.col, query, limit=limit)

        print(json_util.dumps(docs, indent=2) if json_util else json.dumps(docs, indent=2, default=str))
        sys.exit(0)

    elif args.action == "insert":
        if not args.db or not args.col or not args.doc:
            print("Error: --db, --col, and --doc required.", file=sys.stderr)
            sys.exit(1)

        try:
            doc = json_util.loads(args.doc) if json_util else json.loads(args.doc)
        except Exception as e:
            print(f"Error parsing document: {e}", file=sys.stderr)
            sys.exit(1)

        inserted_id = manager.insert(args.db, args.col, doc)
        if inserted_id:
            print(f"Inserted document with ID: {inserted_id}")
            sys.exit(0)
        else:
            sys.exit(1)

    elif args.action == "delete":
        if not args.db or not args.col or not args.id:
            print("Error: --db, --col, and --id required.", file=sys.stderr)
            sys.exit(1)

        success = manager.delete(args.db, args.col, args.id)
        if success:
            print(f"Deleted document with ID: {args.id}")
            sys.exit(0)
        else:
            print(f"Failed to delete document with ID: {args.id}", file=sys.stderr)
            sys.exit(1)

    else:
        if args.action != "tui":
            print(f"Unknown action: {args.action}", file=sys.stderr)
            sys.exit(1)
