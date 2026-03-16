import json
import base64
import sys
import msgpack
import binascii


class MsgpackManager:
    """Manages encoding and decoding of MessagePack data."""

    def encode(self, json_str: str) -> str:
        """
        Encodes a JSON string to MessagePack.
        Returns the MessagePack data as a Base64 encoded string.
        """
        try:
            data = json.loads(json_str)
            packed = msgpack.packb(data, use_bin_type=True)
            return base64.b64encode(packed).decode('utf-8')
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON input: {e}")
        except Exception as e:
            raise ValueError(f"MessagePack encoding error: {e}")

    def decode(self, b64_str: str) -> str:
        """
        Decodes a Base64 encoded MessagePack string to a JSON string.
        """
        try:
            packed = base64.b64decode(b64_str)
            data = msgpack.unpackb(packed, raw=False)
            return json.dumps(data, indent=2)
        except binascii.Error as e:
            raise ValueError(f"Invalid Base64 input: {e}")
        except Exception as e:
            raise ValueError(f"MessagePack decoding error: {e}")


def run_msgpack_lab_logic(args) -> bool:
    """CLI logic for Msgpack Lab."""
    manager = MsgpackManager()

    if getattr(args, "action", None) == "tui" or getattr(args, "tui", False):
        from shared.tui import AgentTUI
        print("Launching MessagePack Lab TUI...")
        app = AgentTUI(project_dir=getattr(args, 'project_dir', None), start_tab="tab-msgpack")
        app.run()
        sys.exit(0)

    try:
        if args.action == "encode":
            input_data = getattr(args, "data", None)
            if not input_data:
                if not sys.stdin.isatty():
                    input_data = sys.stdin.read().strip()
                else:
                    print("Error: Input data required. Pass via --data or stdin.", file=sys.stderr)
                    return False

            result = manager.encode(input_data)
            print(result)
            return True

        elif args.action == "decode":
            input_data = getattr(args, "data", None)
            if not input_data:
                if not sys.stdin.isatty():
                    input_data = sys.stdin.read().strip()
                else:
                    print("Error: Input data required. Pass via --data or stdin.", file=sys.stderr)
                    return False

            result = manager.decode(input_data)
            print(result)
            return True

        else:
            print(f"Unknown action: {args.action}", file=sys.stderr)
            return False

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return False
