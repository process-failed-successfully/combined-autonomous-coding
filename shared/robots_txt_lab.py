import sys
import urllib.robotparser
import urllib.request
import urllib.error

class RobotsTxtManager:
    """Manager for parsing, checking, and fetching robots.txt files."""

    def __init__(self):
        self.parser = urllib.robotparser.RobotFileParser()

    def fetch(self, url: str) -> str:
        """Fetches the robots.txt file from the specified URL."""
        if not url.endswith("robots.txt"):
            if not url.endswith("/"):
                url += "/"
            url += "robots.txt"

        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            with urllib.request.urlopen(req) as response:
                return response.read().decode('utf-8')
        except urllib.error.URLError as e:
            return f"Error fetching {url}: {e}"
        except Exception as e:
            return f"Unexpected error: {e}"

    def parse(self, content: str) -> bool:
        """Parses the given robots.txt content."""
        self.parser.parse(content.splitlines())
        return True

    def check(self, user_agent: str, path: str) -> bool:
        """Checks if the user-agent is allowed to fetch the path."""
        # By default, robotparser uses '*' if it can't match user_agent
        return self.parser.can_fetch(user_agent, path)

def run_robots_txt_lab_logic(args) -> bool:
    """CLI logic for the robots-txt-lab command."""
    if args.action == "fetch":
        manager = RobotsTxtManager()
        content = manager.fetch(args.url)
        print(content)
        return True

    elif args.action == "parse":
        if not args.file and not args.content:
            print("Error: must provide --file or --content", file=sys.stderr)
            return False

        content = args.content
        if args.file:
            try:
                with open(args.file, 'r') as f:
                    content = f.read()
            except IOError as e:
                print(f"Error reading {args.file}: {e}", file=sys.stderr)
                return False

        manager = RobotsTxtManager()
        manager.parse(content)
        print("Successfully parsed robots.txt content.")
        # For CLI output, just show some basic info (since robotparser API doesn't expose easily, we just say success)
        return True

    elif args.action == "check":
        if not args.file and not args.content:
            print("Error: must provide --file or --content", file=sys.stderr)
            return False

        content = args.content
        if args.file:
            try:
                with open(args.file, 'r') as f:
                    content = f.read()
            except IOError as e:
                print(f"Error reading {args.file}: {e}", file=sys.stderr)
                return False

        manager = RobotsTxtManager()
        manager.parse(content)
        allowed = manager.check(args.user_agent, args.path)

        if allowed:
            print(f"ALLOWED: {args.user_agent} can fetch {args.path}")
        else:
            print(f"DISALLOWED: {args.user_agent} cannot fetch {args.path}")
        return True

    return False
