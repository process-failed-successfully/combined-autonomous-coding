import subprocess
import sys
import shutil
import json
from typing import Optional, List, Dict, Any, Union

class GrpcLabManager:
    """
    Manages gRPC interactions using `grpcurl`.
    """

    def __init__(self):
        pass

    def check_grpcurl(self) -> bool:
        """Checks if grpcurl is installed."""
        # Use a local variable for mypy narrowing
        path = shutil.which("grpcurl")
        if path is None:
            return False
        return True

    def _run_grpcurl(self, args: List[str]) -> str:
        """Helper to run grpcurl commands."""
        path = shutil.which("grpcurl")
        if path is None:
             raise FileNotFoundError("grpcurl not found. Please install it (e.g., 'go install github.com/fullstorydev/grpcurl/cmd/grpcurl@latest' or via package manager).")

        cmd = [path] + args
        try:
            # nosec: Subprocess is trusted here as we check shutil.which and control args
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            # Try to return stderr as the error message
            error_msg = e.stderr.strip() if e.stderr else str(e)
            raise RuntimeError(f"grpcurl error: {error_msg}")

    def list_services(self, host: str, plaintext: bool = False, authority: Optional[str] = None) -> List[str]:
        """Lists available services on the host."""
        args = []
        if plaintext:
            args.append("-plaintext")
        if authority:
            args.extend(["-authority", authority])

        args.extend([host, "list"])

        output = self._run_grpcurl(args)
        return output.splitlines()

    def list_methods(self, host: str, service: str, plaintext: bool = False, authority: Optional[str] = None) -> List[str]:
        """Lists methods of a specific service."""
        args = []
        if plaintext:
            args.append("-plaintext")
        if authority:
            args.extend(["-authority", authority])

        args.extend([host, "list", service])

        output = self._run_grpcurl(args)
        return output.splitlines()

    def describe(self, host: str, symbol: str, plaintext: bool = False, authority: Optional[str] = None) -> str:
        """Describes a service, method, or type."""
        args = []
        if plaintext:
            args.append("-plaintext")
        if authority:
            args.extend(["-authority", authority])

        args.extend([host, "describe", symbol])

        return self._run_grpcurl(args)

    def call(self, host: str, method: str, data: Optional[Union[str, Dict]] = None, plaintext: bool = False, authority: Optional[str] = None) -> str:
        """Calls a gRPC method."""
        args = []
        if plaintext:
            args.append("-plaintext")
        if authority:
            args.extend(["-authority", authority])

        if data:
            if isinstance(data, dict):
                json_data = json.dumps(data)
            else:
                json_data = data
            args.extend(["-d", json_data])

        args.extend([host, method])

        return self._run_grpcurl(args)


def run_grpc_lab_logic(args):
    """
    CLI Entry point for gRPC Lab.
    """
    manager = GrpcLabManager()

    if not manager.check_grpcurl():
        print("❌ Error: 'grpcurl' command not found.", file=sys.stderr)
        print("Please install it to use grpc-lab.", file=sys.stderr)
        print("  Mac: brew install grpcurl", file=sys.stderr)
        print("  Linux: go install github.com/fullstorydev/grpcurl/cmd/grpcurl@latest (or check package manager)", file=sys.stderr)
        sys.exit(1)

    try:
        if args.action == "list":
            if args.service:
                methods = manager.list_methods(args.host, args.service, plaintext=args.plaintext, authority=args.authority)
                if not methods:
                    print(f"No methods found for service '{args.service}'.")
                else:
                    print(f"--- Methods for {args.service} ---")
                    for m in methods:
                        print(m)
            else:
                services = manager.list_services(args.host, plaintext=args.plaintext, authority=args.authority)
                if not services:
                    print(f"No services found on {args.host}.")
                else:
                    print(f"--- Services on {args.host} ---")
                    for s in services:
                        print(s)

        elif args.action == "describe":
            if not args.symbol:
                 print("Error: --symbol required for describe.", file=sys.stderr)
                 sys.exit(1)

            desc = manager.describe(args.host, args.symbol, plaintext=args.plaintext, authority=args.authority)
            print(f"--- Describe: {args.symbol} ---")
            print(desc)

        elif args.action == "call":
            if not args.method:
                 print("Error: --method required for call.", file=sys.stderr)
                 sys.exit(1)

            print(f"Calling {args.method} on {args.host}...")
            result = manager.call(args.host, args.method, data=args.data, plaintext=args.plaintext, authority=args.authority)
            print(result)

        else:
            print(f"Unknown action: {args.action}", file=sys.stderr)
            sys.exit(1)

    except RuntimeError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)
