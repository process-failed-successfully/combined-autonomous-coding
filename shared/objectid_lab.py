import sys
import re
from typing import List, Dict, Any

class ObjectIdLabManager:
    """Manages MongoDB ObjectId operations (generation, inspection, extraction)."""

    def generate(self, count: int = 1) -> List[str]:
        """Generates ObjectIds."""
        try:
            from bson.objectid import ObjectId
        except ImportError:
            raise ImportError("pymongo or bson is not installed. Run 'pip install pymongo'.")

        results = []
        for _ in range(count):
            results.append(str(ObjectId()))
        return results

    def inspect(self, objectid_str: str) -> Dict[str, Any]:
        """Inspects an ObjectId."""
        try:
            from bson.objectid import ObjectId
        except ImportError:
            return {"valid": False, "error": "pymongo or bson is not installed."}

        if not ObjectId.is_valid(objectid_str):
            return {"valid": False, "error": "Invalid ObjectId format."}

        try:
            oid = ObjectId(objectid_str)
            return {
                "valid": True,
                "objectid": str(oid),
                "generation_time": oid.generation_time.isoformat()
            }
        except Exception as e:
            return {"valid": False, "error": str(e)}

    def extract(self, text: str, unique: bool = False) -> List[str]:
        """Extracts valid ObjectIds from text."""
        try:
            from bson.objectid import ObjectId
        except ImportError:
            raise ImportError("pymongo or bson is not installed.")

        # ObjectId is a 24-character hex string
        pattern = r'\b[0-9a-fA-F]{24}\b'
        matches = re.findall(pattern, text)

        valid_oids = []
        for match in matches:
            if ObjectId.is_valid(match):
                valid_oids.append(match.lower())

        if unique:
            seen = set()
            unique_oids = []
            for oid in valid_oids:
                if oid not in seen:
                    unique_oids.append(oid)
                    seen.add(oid)
            return unique_oids

        return valid_oids

def run_objectid_lab_logic(args) -> bool:
    """CLI handler for ObjectId Lab."""
    manager = ObjectIdLabManager()

    if getattr(args, "action", None) in ["generate", "gen"]:
        try:
            results = manager.generate(count=args.count)
            for res in results:
                print(res)
            return True
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return False

    elif getattr(args, "action", None) == "inspect":
        info = manager.inspect(args.objectid)
        if not info.get("valid"):
            print(f"Error: {info.get('error')}", file=sys.stderr)
            return False

        print(f"--- ObjectId Inspection: {args.objectid} ---")
        print(f"  Valid:           {info['valid']}")
        print(f"  Generation Time: {info['generation_time']}")
        return True

    elif getattr(args, "action", None) == "extract":
        text_to_process = ""
        if hasattr(args, 'file') and args.file:
            from pathlib import Path
            try:
                text_to_process = Path(args.file).read_text(encoding="utf-8")
            except Exception as e:
                print(f"Error reading file: {e}", file=sys.stderr)
                return False
        elif hasattr(args, 'text') and args.text:
            text_to_process = args.text
        elif not sys.stdin.isatty():
            text_to_process = sys.stdin.read()
        else:
            print("Error: Provide text via --text, --file, or stdin.", file=sys.stderr)
            return False

        unique = getattr(args, 'unique', False)
        oids = manager.extract(text_to_process, unique=unique)

        if not oids:
            print("No ObjectIds found.")
            return True

        for oid in oids:
            print(oid)
        return True

    return False
