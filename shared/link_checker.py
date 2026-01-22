import re
import requests
import concurrent.futures
from pathlib import Path
from typing import List, Dict, Set, Any, Tuple
import sys

class LinkChecker:
    """
    Scans files for HTTP/HTTPS links and validates their reachability.
    """

    def __init__(self, timeout: int = 5, ignore_patterns: List[str] = None):
        self.timeout = timeout
        self.ignore_patterns = ignore_patterns or []
        # Simple but effective regex for extracting URLs from text
        self.url_pattern = re.compile(r'https?://[^\s<>")\]\}]+')

    def _is_ignored(self, url: str) -> bool:
        for pattern in self.ignore_patterns:
            if pattern in url:
                return True
        return False

    def extract_links_from_file(self, file_path: Path) -> List[Tuple[int, str]]:
        """
        Reads a file and returns a list of (line_number, url).
        """
        links = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for i, line in enumerate(f, 1):
                    found = self.url_pattern.findall(line)
                    for url in found:
                        # cleanup trailing punctuation sometimes captured
                        url = url.rstrip('.,;:')
                        if not self._is_ignored(url):
                            links.append((i, url))
        except Exception as e:
            print(f"Error reading {file_path}: {e}", file=sys.stderr)
        return links

    def check_url(self, url: str, session: requests.Session = None) -> Dict[str, Any]:
        """
        Checks a single URL. Returns dict with status info.
        """
        try:
            # mimic a browser to avoid some 403s
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            requester = session if session else requests
            response = requester.head(url, timeout=self.timeout, headers=headers, allow_redirects=True)

            # Some servers return 405 Method Not Allowed for HEAD, so try GET
            if response.status_code == 405:
                 response = requester.get(url, timeout=self.timeout, headers=headers, stream=True)
                 response.close() # Close connection immediately

            return {
                "url": url,
                "status": response.status_code,
                "ok": response.ok,
                "error": None
            }
        except requests.exceptions.RequestException as e:
            return {
                "url": url,
                "status": 0,
                "ok": False,
                "error": str(e)
            }

    def check_files(self, files: List[Path], concurrency: int = 10) -> Dict[str, Any]:
        """
        Main entry point. Scans files and checks links concurrently.
        """
        # 1. Extract links
        print(f"Scanning {len(files)} files for links...")
        file_links: Dict[Path, List[Tuple[int, str]]] = {}
        unique_urls: Set[str] = set()

        for p in files:
            if not p.is_file():
                continue
            links = self.extract_links_from_file(p)
            if links:
                file_links[p] = links
                for _, url in links:
                    unique_urls.add(url)

        print(f"Found {len(unique_urls)} unique links in {len(file_links)} files.")

        # 2. Check links
        results: Dict[str, Dict[str, Any]] = {}
        with requests.Session() as session:
            # Pre-configure session to ensure connection reuse works best
            # Note: check_url also sends headers, which will be merged/overridden.
            session.mount('https://', requests.adapters.HTTPAdapter(pool_connections=concurrency, pool_maxsize=concurrency))
            session.mount('http://', requests.adapters.HTTPAdapter(pool_connections=concurrency, pool_maxsize=concurrency))

            with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
                future_to_url = {executor.submit(self.check_url, url, session): url for url in unique_urls}

                # Progress bar simulation
                completed = 0
                total = len(unique_urls)

                for future in concurrent.futures.as_completed(future_to_url):
                    url = future_to_url[future]
                    try:
                        res = future.result()
                        results[url] = res
                    except Exception as e:
                        results[url] = {"url": url, "status": 0, "ok": False, "error": str(e)}

                    completed += 1
                    if total > 0 and completed % 5 == 0:
                        print(f"  Checking... {completed}/{total}", end='\r')

        print(f"  Checking... {total}/{total} (Done)")

        # 3. Aggregate
        broken_count = 0
        report: Dict[Path, List[Dict[str, Any]]] = {}

        for p, links in file_links.items():
            file_report = []
            for line_no, url in links:
                res = results.get(url)
                if res and not res["ok"]:
                    file_report.append({
                        "line": line_no,
                        "url": url,
                        "status": res["status"],
                        "error": res["error"]
                    })
            if file_report:
                report[p] = file_report
                broken_count += len(file_report)

        return {
            "total_links": len(unique_urls),
            "broken_links_count": broken_count,
            "files_with_issues": len(report),
            "details": report
        }

def run_check_links(project_dir: Path, files_pattern: str = "**/*.md", ignore: str = None, timeout: int = 5, concurrency: int = 10):
    """
    CLI Handler for link checking.
    """
    ignore_list = [i.strip() for i in ignore.split(",")] if ignore else []
    checker = LinkChecker(timeout=timeout, ignore_patterns=ignore_list)

    # Resolve files
    # Only verify text-based files to avoid binary noise
    files = list(project_dir.glob(files_pattern))

    # Filter out common binary or hidden dirs
    # A simple heuristic: if it looks like a text file extension
    text_extensions = {
        '.md', '.txt', '.py', '.js', '.ts', '.html', '.css',
        '.json', '.yaml', '.yml', '.rst', '.sh', '.xml'
    }

    # If user provided a specific extension in the glob, trust them.
    # Otherwise, if they used **, verify extensions.
    if "**" in files_pattern:
        files = [f for f in files if f.suffix.lower() in text_extensions]

    if not files:
        print(f"No files found matching {files_pattern}")
        return False

    result = checker.check_files(files, concurrency=concurrency)

    if result["broken_links_count"] == 0:
        print("\n✅ All links are valid!")
        return True
    else:
        print(f"\n❌ Found {result['broken_links_count']} broken links in {result['files_with_issues']} files:")
        for p, issues in result["details"].items():
            print(f"\n📄 {p.relative_to(project_dir)}")
            for issue in issues:
                status_str = f"Status: {issue['status']}" if issue['status'] > 0 else f"Error: {issue['error']}"
                print(f"  Line {issue['line']}: {issue['url']} -> \033[91m{status_str}\033[0m")
        return False
