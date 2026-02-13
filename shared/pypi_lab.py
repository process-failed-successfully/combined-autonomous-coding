import requests
import sys
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

class PyPiLabManager:
    """Manages PyPI Lab operations: info, releases, deps, files, download."""

    BASE_URL = "https://pypi.org/pypi"

    def _get_json(self, package: str, version: Optional[str] = None) -> Dict[str, Any]:
        url = f"{self.BASE_URL}/{package}/json"
        if version:
            url = f"{self.BASE_URL}/{package}/{version}/json"

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise ValueError(f"Package '{package}' not found (or version '{version}' invalid).")
            raise
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Network error: {e}")

    def get_info(self, package: str) -> Dict[str, Any]:
        data = self._get_json(package)
        return data.get("info", {})

    def get_releases(self, package: str) -> Dict[str, List[Dict[str, Any]]]:
        data = self._get_json(package)
        return data.get("releases", {})

    def get_dependencies(self, package: str, version: Optional[str] = None) -> List[str]:
        data = self._get_json(package, version)
        info = data.get("info", {})
        return info.get("requires_dist") or []

    def get_files(self, package: str, version: Optional[str] = None) -> List[Dict[str, Any]]:
        data = self._get_json(package, version)
        if version:
            return data.get("urls", [])
        else:
            return data.get("urls", [])

    def download(self, package: str, version: Optional[str] = None, dest: str = ".") -> List[str]:
        files = self.get_files(package, version)
        if not files:
            raise ValueError(f"No files found for package '{package}' (version: {version or 'latest'}).")

        dest_path = Path(dest)
        dest_path.mkdir(parents=True, exist_ok=True)
        downloaded = []

        print(f"Found {len(files)} file(s). Downloading to {dest_path}...")

        for file_info in files:
            url = file_info.get("url")
            filename = file_info.get("filename")
            if not url or not filename:
                continue

            target = dest_path / filename
            if target.exists():
                print(f"  Skipping {filename} (already exists).")
                continue

            print(f"  Downloading {filename}...")
            try:
                with requests.get(url, stream=True, timeout=30) as r:
                    r.raise_for_status()
                    with open(target, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                downloaded.append(str(target))
            except Exception as e:
                print(f"  Failed to download {filename}: {e}", file=sys.stderr)

        return downloaded

def run_pypi_lab_logic(args) -> bool:
    """CLI handler for PyPI Lab."""
    manager = PyPiLabManager()

    try:
        if args.action == "info":
            info = manager.get_info(args.package)
            print(f"--- {info.get('name')} {info.get('version')} ---")
            print(f"Summary: {info.get('summary')}")
            print(f"Author:  {info.get('author')}")
            print(f"License: {info.get('license')}")
            print(f"Home:    {info.get('home_page')}")
            print(f"PyPI:    {info.get('package_url')}")
            if info.get('project_urls'):
                print("Links:")
                for k, v in info['project_urls'].items():
                    print(f"  {k}: {v}")

        elif args.action == "releases":
            releases = manager.get_releases(args.package)
            print(f"--- Releases for {args.package} ---")
            sorted_versions = []
            for ver, files in releases.items():
                date = "Unknown"
                if files:
                    date = files[0].get("upload_time", "Unknown")[:10]
                sorted_versions.append((ver, date))

            sorted_versions.sort(key=lambda x: x[1], reverse=True)

            for ver, date in sorted_versions:
                print(f"{date} : {ver}")

        elif args.action == "deps":
            deps = manager.get_dependencies(args.package, args.version)
            print(f"--- Dependencies for {args.package} ({args.version or 'latest'}) ---")
            if not deps:
                print("No dependencies listed (or check requires_dist is empty).")
            else:
                for d in deps:
                    print(f"- {d}")

        elif args.action == "files":
            files = manager.get_files(args.package, args.version)
            print(f"--- Files for {args.package} ({args.version or 'latest'}) ---")
            if not files:
                print("No files found.")
            else:
                for f in files:
                    size_mb = f.get('size', 0) / 1024 / 1024
                    print(f"- {f.get('filename')} ({f.get('packagetype')}) - {size_mb:.2f} MB")
                    print(f"  URL: {f.get('url')}")
                    print(f"  SHA256: {f.get('digests', {}).get('sha256')}")

        elif args.action == "download":
            dest = args.dest or "."
            manager.download(args.package, args.version, dest)
            print("Download complete.")

        return True

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return False
