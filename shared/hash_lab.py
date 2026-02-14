import hashlib
import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

class HashLabManager:
    """
    Manages hash operations: string, file, directory, compare, verify.
    """

    def __init__(self):
        self.algorithms = hashlib.algorithms_available

    def _get_hasher(self, algo: str):
        algo = algo.lower()
        if algo not in self.algorithms:
            # Fallback for guaranteed algorithms
            if algo in ["md5", "sha1", "sha224", "sha256", "sha384", "sha512"]:
                return hashlib.new(algo)
            raise ValueError(f"Algorithm '{algo}' not available.")
        return hashlib.new(algo)

    def hash_string(self, text: str, algo: str = "sha256") -> str:
        """Hashes a string."""
        h = self._get_hasher(algo)
        h.update(text.encode("utf-8"))
        return h.hexdigest()

    def hash_file(self, filepath: Union[str, Path], algo: str = "sha256") -> str:
        """Hashes a file (streaming)."""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"File '{path}' not found.")
        if not path.is_file():
            raise ValueError(f"Path '{path}' is not a file.")

        h = self._get_hasher(algo)
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    def hash_dir(self, dirpath: Union[str, Path], algo: str = "sha256", recursive: bool = False) -> Dict[str, str]:
        """Hashes all files in a directory."""
        path = Path(dirpath)
        if not path.exists():
            raise FileNotFoundError(f"Directory '{path}' not found.")
        if not path.is_dir():
            raise ValueError(f"Path '{path}' is not a directory.")

        results = {}
        if recursive:
            for root, _, files in os.walk(path):
                for file in files:
                    fp = Path(root) / file
                    try:
                        results[str(fp)] = self.hash_file(fp, algo)
                    except Exception as e:
                        results[str(fp)] = f"Error: {e}"
        else:
            for file in path.iterdir():
                if file.is_file():
                    try:
                        results[str(file)] = self.hash_file(file, algo)
                    except Exception as e:
                        results[str(file)] = f"Error: {e}"
        return results

    def compare_files(self, file1: Union[str, Path], file2: Union[str, Path], algo: str = "sha256") -> Dict[str, Any]:
        """Compares two files by hash."""
        f1 = Path(file1)
        f2 = Path(file2)

        if not f1.exists() or not f2.exists():
            raise FileNotFoundError("One or both files not found.")

        h1 = self.hash_file(f1, algo)
        h2 = self.hash_file(f2, algo)

        return {
            "match": h1 == h2,
            "file1": str(f1),
            "hash1": h1,
            "file2": str(f2),
            "hash2": h2,
            "algo": algo
        }

    def verify_checksums(self, checksum_file: Union[str, Path], algo: str = "sha256", root_dir: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
        """
        Verifies files against a checksum file.
        Format expected: `hash  filename` (standard shasum output).
        """
        cpath = Path(checksum_file)
        if not cpath.exists():
            raise FileNotFoundError(f"Checksum file '{cpath}' not found.")

        root = Path(root_dir) if root_dir else cpath.parent
        results = {"passed": [], "failed": [], "missing": [], "errors": []}

        try:
            with open(cpath, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue

                    # Split by whitespace (at least 2 spaces usually, but allow 1)
                    parts = line.split(maxsplit=1)
                    if len(parts) != 2:
                        # Maybe created manually? Try split by single space
                        parts = line.split(" ", 1)
                        if len(parts) != 2:
                            results["errors"].append(f"Invalid line format: {line}")
                            continue

                    expected_hash = parts[0].strip()
                    filename = parts[1].strip()

                    # Handle binary marker '*'
                    if filename.startswith("*"):
                        filename = filename[1:]

                    target_path = root / filename
                    if not target_path.exists():
                        results["missing"].append(filename)
                        continue

                    try:
                        actual_hash = self.hash_file(target_path, algo)
                        if actual_hash == expected_hash:
                            results["passed"].append(filename)
                        else:
                            results["failed"].append({"file": filename, "expected": expected_hash, "actual": actual_hash})
                    except Exception as e:
                        results["errors"].append(f"Error checking {filename}: {e}")
        except Exception as e:
            raise ValueError(f"Error reading checksum file: {e}")

        return results

def run_hash_lab_logic(args) -> bool:
    """CLI handler for Hash Lab."""
    manager = HashLabManager()

    # Default algo is sha256
    algo = getattr(args, "algo", "sha256")

    try:
        if args.action == "string":
            if not args.text:
                 # Read from stdin
                if not sys.stdin.isatty():
                    try:
                        content = sys.stdin.read()
                        # If simple string, strip newline? Usually yes for echo "foo" | hash
                        # But strictly, hash should hash exactly what it gets.
                        # However, user experience: `echo "foo" | hash string` -> hash("foo\n")
                        # We'll use strip() if it looks like a single line to be helpful,
                        # or args.text if provided.
                        print(manager.hash_string(content.strip(), algo))
                        return True
                    except Exception:
                        pass
                print("Error: Text required.", file=sys.stderr)
                return False

            print(manager.hash_string(args.text, algo))

        elif args.action == "file":
            print(f"--- Hashing File ({algo}) ---")
            print(f"File: {args.path}")
            result = manager.hash_file(args.path, algo)
            print(f"Hash: {result}")

        elif args.action == "dir":
            print(f"--- Hashing Directory ({algo}) ---")
            recursive = args.recursive
            print(f"Directory: {args.path} (Recursive: {recursive})")
            results = manager.hash_dir(args.path, algo, recursive)

            for f, h in sorted(results.items()):
                print(f"{h}  {f}")

        elif args.action == "compare":
            print(f"--- Comparing Files ({algo}) ---")
            res = manager.compare_files(args.file1, args.file2, algo)
            if res["match"]:
                print("✅ Files MATCH.")
            else:
                print("❌ Files do NOT match.")
            print(f"File 1 ({res['file1']}): {res['hash1']}")
            print(f"File 2 ({res['file2']}): {res['hash2']}")
            if not res["match"]:
                sys.exit(1)

        elif args.action == "verify":
            print(f"--- Verifying Checksums ({algo}) ---")
            print(f"Checksum File: {args.checksum_file}")
            # Optional root dir
            root = getattr(args, "root", None)
            res = manager.verify_checksums(args.checksum_file, algo, root)

            if res["passed"]:
                print(f"\n✅ Passed ({len(res['passed'])}):")
                for f in res["passed"]:
                    print(f"  {f}")

            if res["failed"]:
                print(f"\n❌ Failed ({len(res['failed'])}):")
                for f in res["failed"]:
                    print(f"  {f['file']} (Expected: {f['expected']}, Got: {f['actual']})")

            if res["missing"]:
                print(f"\n⚠️  Missing ({len(res['missing'])}):")
                for f in res["missing"]:
                    print(f"  {f}")

            if res["errors"]:
                print(f"\n⚠️  Errors ({len(res['errors'])}):")
                for e in res["errors"]:
                    print(f"  {e}")

            if res["failed"] or res["missing"] or res["errors"]:
                sys.exit(1)

        return True

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return False
