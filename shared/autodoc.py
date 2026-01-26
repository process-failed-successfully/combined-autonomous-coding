import ast
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from shared.config import Config
from shared.utils import IGNORED_DIRS
from agents.gemini import GeminiAgent
from agents.cursor import CursorAgent
from agents.local import LocalAgent
from agents.openrouter import OpenRouterAgent

logger = logging.getLogger(__name__)

class AutodocManager:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir

    def scan_commands(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Parses a python file (like main.py) to find argparse commands.
        Looks for: subparsers.add_parser("command_name", help="...")
        """
        commands = []
        try:
            code = file_path.read_text(encoding="utf-8")
            tree = ast.parse(code)
        except Exception as e:
            logger.error(f"Failed to parse {file_path}: {e}")
            return []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check for add_parser call
                if isinstance(node.func, ast.Attribute) and node.func.attr == "add_parser":
                    # Extract name (first arg)
                    cmd_name = "unknown"
                    if node.args and isinstance(node.args[0], ast.Constant):
                        cmd_name = node.args[0].value
                    elif node.args and isinstance(node.args[0], ast.Str): # Python < 3.8
                        cmd_name = node.args[0].s

                    # Extract help (keyword arg)
                    cmd_help = "No description"
                    for kw in node.keywords:
                        if kw.arg == "help":
                            if isinstance(kw.value, ast.Constant):
                                cmd_help = kw.value.value
                            elif isinstance(kw.value, ast.Str):
                                cmd_help = kw.value.s

                    # Extract aliases
                    aliases = []
                    for kw in node.keywords:
                        if kw.arg == "aliases":
                            if isinstance(kw.value, ast.List):
                                for elt in kw.value.elts:
                                    if isinstance(elt, ast.Constant):
                                        aliases.append(elt.value)
                                    elif isinstance(elt, ast.Str):
                                        aliases.append(elt.s)

                    commands.append({
                        "name": cmd_name,
                        "help": cmd_help,
                        "aliases": aliases
                    })

        # Sort by name
        commands.sort(key=lambda x: x["name"])
        return commands

    def scan_structure(self, root_dir: Path, prefix: str = "") -> str:
        """
        Generates a tree-like string structure of the project.
        """
        output = ""
        try:
            entries = sorted(list(root_dir.iterdir()))
        except OSError:
            return ""

        # Filter entries
        filtered_entries = []
        for entry in entries:
            if entry.name.startswith("."):
                # Skip hidden files except strictly required ones?
                # For documentation, we usually skip hidden files/dirs like .git
                continue
            if entry.name in IGNORED_DIRS or entry.name == "__pycache__":
                continue
            filtered_entries.append(entry)

        count = len(filtered_entries)
        for i, entry in enumerate(filtered_entries):
            connector = "├── " if i < count - 1 else "└── "
            output += f"{prefix}{connector}{entry.name}\n"

            if entry.is_dir():
                extension = "│   " if i < count - 1 else "    "
                output += self.scan_structure(entry, prefix + extension)

        return output

    async def update_readme(
        self,
        agent_type: str = "gemini",
        model: Optional[str] = None,
        check_only: bool = False
    ) -> bool:
        """
        Updates README.md using an AI agent.
        """
        readme_path = self.project_dir / "README.md"
        current_readme = ""
        if readme_path.exists():
            current_readme = readme_path.read_text(encoding="utf-8")
        else:
            logger.warning("README.md not found. A new one will be generated.")

        # 1. Gather Context
        main_py = self.project_dir / "main.py"
        commands = self.scan_commands(main_py)

        structure = self.scan_structure(self.project_dir)

        # 2. Construct Prompt
        prompt = f"""
You are an expert technical writer and software engineer.
Your task is to update the project's README.md to accurately reflect its current state.

### Current Project Structure
```
{structure}
```

### Available CLI Commands (Extracted from code)
The following commands are defined in `main.py`:
"""
        for cmd in commands:
            alias_str = f" (aliases: {', '.join(cmd['aliases'])})" if cmd['aliases'] else ""
            prompt += f"- `{cmd['name']}`{alias_str}: {cmd['help']}\n"

        prompt += f"""

### Current README.md
```markdown
{current_readme}
```

### Instructions
1. Analyze the 'Current README.md' and compare it with the 'Current Project Structure' and 'Available CLI Commands'.
2. Identify outdated sections, missing commands, or structural changes.
3. Rewrite the README.md to be comprehensive, accurate, and professional.
4. Ensure all available commands are listed and briefly explained (you can group them logically).
5. If the current README is already good and accurate, you can keep it mostly as is, but ensure the command list is up to date.
6. Return ONLY the content of the new README.md. Do not include markdown code block markers (```markdown) at the start or end unless they are part of the file content itself.
"""

        # 3. Call Agent
        config = Config(
            project_dir=self.project_dir,
            agent_type=agent_type,
            model=model,
            verbose=False,
            max_iterations=1,
            stream_output=False,
        )

        agent_class_map = {
            "gemini": GeminiAgent,
            "cursor": CursorAgent,
            "local": LocalAgent,
            "openrouter": OpenRouterAgent,
        }

        agent_class = agent_class_map.get(agent_type)
        if not agent_class:
            raise ValueError(f"Unknown agent type: {agent_type}")

        agent = agent_class(config)

        print("Analyzing project and generating documentation...")
        _, response, _ = await agent.run_agent_session(prompt)
        new_readme = response.strip()

        # Clean up potential markdown code fences from agent output
        if new_readme.startswith("```markdown"):
            new_readme = new_readme[11:]
        elif new_readme.startswith("```"):
            new_readme = new_readme[3:]

        if new_readme.endswith("```"):
            new_readme = new_readme[:-3]

        new_readme = new_readme.strip()

        # 4. Check or Apply
        if check_only:
            if new_readme != current_readme.strip():
                print("README.md is out of date.")
                # Ideally show diff
                return False
            else:
                print("README.md is up to date.")
                return True
        else:
            readme_path.write_text(new_readme, encoding="utf-8")
            print(f"✅ Updated {readme_path}")
            return True

async def run_autodoc_logic(
    project_dir: Path,
    agent_type: str = "gemini",
    model: Optional[str] = None,
    check: bool = False
):
    manager = AutodocManager(project_dir)
    await manager.update_readme(agent_type, model, check)
