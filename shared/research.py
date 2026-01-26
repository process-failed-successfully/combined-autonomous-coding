import logging
import subprocess
import shutil
from typing import List, Dict, Set
from urllib.parse import urlparse

from shared.knowledge import KnowledgeManager

logger = logging.getLogger(__name__)

class ResearchManager:
    def __init__(self):
        self.knowledge_manager = KnowledgeManager()
        self.lynx_path = shutil.which("lynx")

    def fetch_page_text(self, url: str) -> str:
        """Fetches the text content of a URL using lynx."""
        if not self.lynx_path:
            raise RuntimeError("lynx is not installed. Please install it to use the research feature.")

        try:
            # -dump: formats as text
            # -width=1000: avoid excessive wrapping
            # -nolist: don't append list of links at the end (we parse links separately if needed)
            cmd = [self.lynx_path, "-dump", "-width=1000", "-nolist", url]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"Error fetching {url}: {e.stderr}")
            return ""

    def extract_links(self, url: str) -> List[str]:
        """Extracts links from a URL using lynx."""
        if not self.lynx_path:
            return []

        try:
            # -dump -listonly: lists all links
            cmd = [self.lynx_path, "-dump", "-listonly", url]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            output = result.stdout

            links = []
            for line in output.splitlines():
                # Lynx list format: "   1. http://..."
                # Use regex or simple splitting
                line = line.strip()
                if not line: continue

                parts = line.split(". ", 1)
                if len(parts) == 2 and parts[1].startswith("http"):
                    link = parts[1].strip()
                    # Filter out purely internal anchors or irrelevant stuff?
                    # Lynx usually resolves relative links.
                    links.append(link)
            return links
        except subprocess.CalledProcessError as e:
            logger.error(f"Error extracting links from {url}: {e.stderr}")
            return []

    def crawl(self, start_url: str, depth: int = 0, limit: int = 5, progress_callback=None) -> List[Dict[str, str]]:
        """
        Crawls URLs starting from start_url up to depth.
        Returns a list of dicts {url, content}.
        """
        visited: Set[str] = set()
        results: List[Dict[str, str]] = []
        queue = [(start_url, 0)] # (url, current_depth)

        while queue and len(results) < limit:
            url, current_depth = queue.pop(0)

            if url in visited:
                continue
            visited.add(url)

            logger.info(f"Researching: {url} (depth {current_depth})")
            if progress_callback:
                progress_callback(url, "fetching")

            content = self.fetch_page_text(url)

            if content:
                if progress_callback:
                    progress_callback(url, "success")
                results.append({"url": url, "content": content})
                self.save_to_knowledge(content, url)

            if current_depth < depth:
                links = self.extract_links(url)
                # Filter links to stay on same domain? Usually good practice for docs.
                base_domain = urlparse(start_url).netloc

                for link in links:
                    if urlparse(link).netloc == base_domain:
                        if link not in visited:
                            queue.append((link, current_depth + 1))

        return results

    def save_to_knowledge(self, content: str, url: str) -> None:
        """Saves researched content to the Knowledge Base."""
        # Add a header to identify source
        full_content = f"Source: {url}\n\n{content}"
        self.knowledge_manager.add_knowledge(
            content=full_content,
            category="RESEARCH",
            source="web_crawler"
        )

def run_research_logic(url: str, depth: int = 0, limit: int = 5) -> bool:
    """CLI Entry point logic."""
    manager = ResearchManager()
    if not manager.lynx_path:
        print("❌ Error: 'lynx' command not found. Please install it (e.g., sudo apt install lynx).")
        return False

    print(f"--- Researching: {url} (Depth: {depth}, Limit: {limit}) ---")
    results = manager.crawl(url, depth=depth, limit=limit)

    if not results:
        print("❌ No content retrieved.")
        return False

    print(f"\n✅ Successfully researched {len(results)} page(s).")
    print("Content saved to Knowledge Base (Category: RESEARCH).")

    # Print summary of fetched pages
    for res in results:
        title = res['content'].split('\n')[0][:50] + "..." if res['content'] else "No Content"
        print(f"  - {res['url']}: {len(res['content'])} chars")

    return True
