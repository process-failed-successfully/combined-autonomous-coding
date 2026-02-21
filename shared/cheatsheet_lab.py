from pathlib import Path
from typing import Dict, List, Optional

class CheatsheetManager:
    """Manages built-in and user-defined cheatsheets."""

    BUILTIN_SHEETS = {
        "git": """# Git Cheatsheet

## Setup
- `git config --global user.name "Name"`: Set user name
- `git config --global user.email "email"`: Set user email

## Basics
- `git init`: Initialize repo
- `git clone <url>`: Clone repo
- `git status`: Check status
- `git add <file>`: Stage file
- `git commit -m "msg"`: Commit changes
- `git pull`: Pull changes
- `git push`: Push changes

## Branches
- `git branch`: List branches
- `git checkout -b <branch>`: Create and switch to branch
- `git merge <branch>`: Merge branch
- `git branch -d <branch>`: Delete branch

## History
- `git log`: View commit history
- `git diff`: View changes
- `git blame <file>`: See who changed what
""",
        "docker": """# Docker Cheatsheet

## Images
- `docker build -t <tag> .`: Build image
- `docker images`: List images
- `docker rmi <image>`: Remove image
- `docker pull <image>`: Pull image

## Containers
- `docker run -d <image>`: Run in background
- `docker ps`: List running containers
- `docker ps -a`: List all containers
- `docker stop <id>`: Stop container
- `docker rm <id>`: Remove container
- `docker logs <id>`: View logs
- `docker exec -it <id> sh`: Shell into container

## Compose
- `docker compose up -d`: Start services
- `docker compose down`: Stop services
- `docker compose logs -f`: Follow logs
""",
        "linux": """# Linux Cheatsheet

## Files
- `ls -lah`: List all files with details
- `cd <dir>`: Change directory
- `pwd`: Print working directory
- `cp <src> <dest>`: Copy file
- `mv <src> <dest>`: Move/Rename file
- `rm <file>`: Remove file
- `mkdir <dir>`: Create directory
- `chmod +x <file>`: Make executable
- `chown <user>:<group> <file>`: Change ownership

## System
- `top` / `htop`: Monitor processes
- `df -h`: Disk usage
- `free -h`: Memory usage
- `uname -a`: Kernel info
- `whoami`: Current user

## Networking
- `ip addr`: IP addresses
- `ping <host>`: Check connectivity
- `curl <url>`: Make HTTP request
- `netstat -tulpn`: Listening ports
""",
        "python": """# Python Cheatsheet

## Basics
- `print("Hello")`: Output text
- `len(obj)`: Length of object
- `type(obj)`: Type of object
- `range(n)`: Sequence 0 to n-1

## Lists
- `l = [1, 2, 3]`: Create list
- `l.append(4)`: Add item
- `l[0]`: Access item
- `l[1:3]`: Slice
- `[x**2 for x in range(10)]`: List comprehension

## Dictionaries
- `d = {"k": "v"}`: Create dict
- `d["k"]`: Get value
- `d.get("k", default)`: Get safely
- `d.keys()`, `d.values()`, `d.items()`: Iterators

## Strings
- `f"Value: {x}"`: F-string
- `s.split(",")`: Split string
- `",".join(l)`: Join list
- `s.strip()`: Remove whitespace

## Files
```python
with open("file.txt", "r") as f:
    content = f.read()
```
""",
        "regex": """# Regex Cheatsheet

## Anchors
- `^`: Start of line
- `$`: End of line
- `\\b`: Word boundary

## Quantifiers
- `*`: 0 or more
- `+`: 1 or more
- `?`: 0 or 1
- `{n}`: Exactly n
- `{n,m}`: Between n and m

## Classes
- `.`: Any character (except newline)
- `\\d`: Digit
- `\\w`: Word character (alphanumeric + _)
- `\\s`: Whitespace
- `[abc]`: Any of a, b, or c
- `[^abc]`: Not a, b, or c

## Groups
- `(...)`: Capturing group
- `(?:...)`: Non-capturing group
- `(?P<name>...)`: Named group
""",
        "vim": """# Vim Cheatsheet

## Modes
- `i`: Insert mode
- `Esc`: Normal mode
- `v`: Visual mode
- `:`: Command mode

## Editing
- `x`: Delete character
- `dd`: Delete line
- `yy`: Yank (copy) line
- `p`: Paste
- `u`: Undo
- `Ctrl+r`: Redo

## Navigation
- `h`, `j`, `k`, `l`: Left, Down, Up, Right
- `w`: Next word
- `b`: Previous word
- `gg`: Top of file
- `G`: Bottom of file
- `/pattern`: Search

## Saving/Exiting
- `:w`: Save
- `:q`: Quit
- `:wq`: Save and quit
- `:q!`: Quit without saving
""",
        "sql": """# SQL Cheatsheet

## Querying
- `SELECT * FROM table`: Select all columns
- `SELECT col1, col2 FROM table`: Select specific columns
- `WHERE condition`: Filter rows
- `ORDER BY col ASC/DESC`: Sort results
- `LIMIT n`: Limit results

## Joins
- `INNER JOIN table2 ON t1.id = t2.id`: Matching rows
- `LEFT JOIN`: All from left, matching from right
- `RIGHT JOIN`: All from right, matching from left

## Aggregation
- `COUNT(*)`: Count rows
- `SUM(col)`: Sum values
- `AVG(col)`: Average value
- `GROUP BY col`: Group results
- `HAVING condition`: Filter groups

## Manipulation
- `INSERT INTO table (col1) VALUES (val)`: Insert row
- `UPDATE table SET col1 = val WHERE cond`: Update row
- `DELETE FROM table WHERE cond`: Delete row
""",
        "markdown": """# Markdown Cheatsheet

## Headers
- `# H1`
- `## H2`
- `### H3`

## Formatting
- `**bold**`
- `*italic*`
- `` `code` ``
- `[link](url)`
- `![alt](image_url)`

## Lists
- `- Item 1`
- `1. Item 1`

## Code Blocks
```python
print("Hello")
```

## Blockquotes
> This is a quote.
""",
    }

    def __init__(self, project_dir: Optional[Path] = None):
        self.project_dir = project_dir
        self.user_sheets_dir = None
        if self.project_dir:
            self.user_sheets_dir = self.project_dir / ".cheatsheets"

    def list_topics(self) -> List[str]:
        """Returns a sorted list of available cheat sheet topics."""
        topics = set(self.BUILTIN_SHEETS.keys())

        if self.user_sheets_dir and self.user_sheets_dir.exists():
            for f in self.user_sheets_dir.glob("*.md"):
                topics.add(f.stem)

        return sorted(list(topics))

    def get_content(self, topic: str) -> Optional[str]:
        """Returns the content of a cheat sheet."""
        # Check built-in first
        if topic in self.BUILTIN_SHEETS:
            return self.BUILTIN_SHEETS[topic]

        # Check user defined
        if self.user_sheets_dir:
            user_path = self.user_sheets_dir / f"{topic}.md"
            if user_path.exists():
                return user_path.read_text(encoding="utf-8", errors="replace")

        return None

    def search(self, query: str) -> List[str]:
        """Returns topics matching the query (case-insensitive substring)."""
        query = query.lower()
        all_topics = self.list_topics()
        return [t for t in all_topics if query in t.lower()]
