import requests
import sys
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

class NpmLabManager:
    """Manages NPM Lab operations: info, versions, deps, tags, search."""

    REGISTRY_URL = "https://registry.npmjs.org"
    SEARCH_URL = "https://registry.npmjs.org/-/v1/search"

    def _get_json(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise ValueError(f"Resource not found: {url}")
            raise
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Network error: {e}")

    def get_package_data(self, package: str) -> Dict[str, Any]:
        """Fetches full package metadata."""
        url = f"{self.REGISTRY_URL}/{package}"
        return self._get_json(url)

    def get_info(self, package: str) -> Dict[str, Any]:
        """Returns basic package info."""
        data = self.get_package_data(package)
        latest_ver = data.get("dist-tags", {}).get("latest")
        latest_data = data.get("versions", {}).get(latest_ver, {}) if latest_ver else {}

        return {
            "name": data.get("name"),
            "description": data.get("description"),
            "author": data.get("author", {}).get("name") if isinstance(data.get("author"), dict) else data.get("author"),
            "license": data.get("license"),
            "homepage": data.get("homepage"),
            "latest_version": latest_ver,
            "keywords": data.get("keywords", []),
            "repository": data.get("repository", {}).get("url") if isinstance(data.get("repository"), dict) else data.get("repository"),
        }

    def get_versions(self, package: str) -> List[Dict[str, str]]:
        """Returns a list of versions with release dates."""
        data = self.get_package_data(package)
        time_data = data.get("time", {})
        # Filter out 'created' and 'modified' keys
        versions = [
            {"version": v, "date": t[:10]}
            for v, t in time_data.items()
            if v not in ["created", "modified"]
        ]
        # Sort by date descending
        versions.sort(key=lambda x: x["date"], reverse=True)
        return versions

    def get_dependencies(self, package: str, version: Optional[str] = None) -> Dict[str, Dict[str, str]]:
        """Returns dependencies for a specific version (or latest)."""
        data = self.get_package_data(package)
        ver = version or data.get("dist-tags", {}).get("latest")

        if not ver:
            raise ValueError(f"No version found for package '{package}'.")

        ver_data = data.get("versions", {}).get(ver, {})

        return {
            "dependencies": ver_data.get("dependencies", {}),
            "devDependencies": ver_data.get("devDependencies", {}),
            "peerDependencies": ver_data.get("peerDependencies", {}),
        }

    def get_dist_tags(self, package: str) -> Dict[str, str]:
        """Returns distribution tags."""
        data = self.get_package_data(package)
        return data.get("dist-tags", {})

    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Searches for packages."""
        params = {"text": query, "size": limit}
        data = self._get_json(self.SEARCH_URL, params=params)
        objects = data.get("objects", [])

        results = []
        for obj in objects:
            pkg = obj.get("package", {})
            results.append({
                "name": pkg.get("name"),
                "version": pkg.get("version"),
                "description": pkg.get("description"),
                "date": pkg.get("date", "")[:10],
                "publisher": pkg.get("publisher", {}).get("username"),
                "score": obj.get("score", {}).get("final"),
            })
        return results

def run_npm_lab_logic(args) -> bool:
    """CLI handler for NPM Lab."""
    manager = NpmLabManager()

    try:
        if args.action == "info":
            info = manager.get_info(args.package)
            print(f"--- {info.get('name')} {info.get('latest_version')} ---")
            print(f"Description: {info.get('description')}")
            print(f"Author:      {info.get('author')}")
            print(f"License:     {info.get('license')}")
            print(f"Homepage:    {info.get('homepage')}")
            print(f"Repository:  {info.get('repository')}")
            if info.get('keywords'):
                print(f"Keywords:    {', '.join(info.get('keywords')[:10])}")

        elif args.action == "versions":
            versions = manager.get_versions(args.package)
            print(f"--- Versions for {args.package} (Top {args.limit if hasattr(args, 'limit') else 15}) ---")
            limit = getattr(args, 'limit', 15)
            for v in versions[:limit]:
                print(f"{v['date']} : {v['version']}")

        elif args.action == "deps":
            deps = manager.get_dependencies(args.package, args.version)
            ver = args.version or "latest"
            print(f"--- Dependencies for {args.package} ({ver}) ---")

            for dep_type, dependencies in deps.items():
                if dependencies:
                    print(f"\n[{dep_type}]")
                    for name, constraint in dependencies.items():
                        print(f"  {name}: {constraint}")

            if all(not d for d in deps.values()):
                print("No dependencies found.")

        elif args.action == "tags":
            tags = manager.get_dist_tags(args.package)
            print(f"--- Dist Tags for {args.package} ---")
            for tag, version in tags.items():
                print(f"{tag:<10} : {version}")

        elif args.action == "search":
            results = manager.search(args.query, args.limit)
            print(f"--- Search Results for '{args.query}' ---")
            for r in results:
                print(f"\n{r['name']} ({r['version']}) - {r['date']}")
                print(f"  {r['description']}")
                print(f"  Publisher: {r['publisher']}")

        return True

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return False
