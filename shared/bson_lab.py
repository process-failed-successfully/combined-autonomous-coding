import json
import sys
import argparse
try:
    import bson
    HAS_BSON = True
except ImportError:
    bson = None
    HAS_BSON = False


class BsonManager:
    """Manages BSON encoding and decoding."""

    @staticmethod
    def encode(data_str: str) -> bytes:
        if not bson:
            raise ImportError("bson module is not installed. Please install 'pymongo' or 'bson' package.")
        try:
            data_dict = json.loads(data_str)
            if not isinstance(data_dict, dict):
                raise ValueError("BSON encoding requires a JSON object (dictionary) at the root level.")
            return bson.encode(data_dict)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON input: {e}")

    @staticmethod
    def decode(data_bytes: bytes) -> str:
        if not bson:
            raise ImportError("bson module is not installed. Please install 'pymongo' or 'bson' package.")
        try:
            # bson.decode returns a dict
            data_dict = bson.decode(data_bytes)

            # Use a custom encoder to handle datetime/ObjectId if necessary
            class BsonEncoder(json.JSONEncoder):
                def default(self, obj):
                    if hasattr(obj, 'isoformat'):
                        return obj.isoformat()
                    try:
                        from bson.objectid import ObjectId
                        if isinstance(obj, ObjectId):
                            return str(obj)
                    except ImportError:
                        pass
                    return super().default(obj)

            return json.dumps(data_dict, indent=2, cls=BsonEncoder)
        except Exception as e:
            raise ValueError(f"Invalid BSON input: {e}")


def run_bson_lab_logic(args: argparse.Namespace) -> bool:
    """CLI logic for the BSON Lab."""
    if not bson:
        print("Error: The 'bson' library is required for this command. Run 'pip install pymongo'.", file=sys.stderr)
        return False

    manager = BsonManager()

    if getattr(args, "action", None) == "encode":
        if not hasattr(args, "data") or not args.data:
            print("Error: --data is required for encoding.", file=sys.stderr)
            return False

        try:
            encoded = manager.encode(args.data)
            # Print as hex for readability, or save to file
            print(encoded.hex())
            return True
        except Exception as e:
            print(f"BSON Encode Error: {e}", file=sys.stderr)
            return False

    elif getattr(args, "action", None) == "decode":
        if not hasattr(args, "data") or not args.data:
            print("Error: --data is required for decoding.", file=sys.stderr)
            return False

        try:
            # Assume input is hex string from CLI
            data_bytes = bytes.fromhex(args.data)
            decoded = manager.decode(data_bytes)
            print(decoded)
            return True
        except Exception as e:
            print(f"BSON Decode Error: {e}", file=sys.stderr)
            return False

    print("Error: Invalid action. Use 'encode' or 'decode'.", file=sys.stderr)
    return False
