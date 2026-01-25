import os
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any
import logging

from shared.config import Config
from agents.gemini import GeminiAgent
from agents.cursor import CursorAgent
from agents.local import LocalAgent
from agents.openrouter import OpenRouterAgent

logger = logging.getLogger(__name__)

class ADRManager:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir.resolve()
        self.adr_dir = self.project_dir / "docs" / "adr"

    def init_adr_repo(self) -> str:
        """Initialize the ADR directory and the first ADR."""
        if not self.adr_dir.exists():
            self.adr_dir.mkdir(parents=True, exist_ok=True)

        first_adr = self.adr_dir / "0000-record-architecture-decisions.md"
        if first_adr.exists():
            return "ADR repository already initialized."

        content = """# 0. Record architecture decisions

Date: {date}

## Status

Accepted

## Context

We need to record architectural decisions made on this project.

## Decision

We will use Architecture Decision Records, as described by Michael Nygard in this article: http://thinkrelevance.com/blog/2011/11/15/documenting-architecture-decisions

## Consequences

See Michael Nygard's article, linked above.
""".format(date=datetime.now().strftime("%Y-%m-%d"))

        first_adr.write_text(content, encoding="utf-8")
        return f"Initialized ADR repository at {self.adr_dir}"

    def list_adrs(self) -> List[Dict[str, str]]:
        """List all ADRs."""
        if not self.adr_dir.exists():
            return []

        adrs = []
        # Sort by filename which starts with number
        for file_path in sorted(self.adr_dir.glob("*.md")):
            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
                # Extract title from first line
                lines = content.splitlines()
                title = lines[0].lstrip("# ").strip() if lines else "Untitled"

                # Extract status
                status = "Unknown"
                for i, line in enumerate(lines):
                    if line.strip() == "## Status":
                        # Look at next non-empty line
                        for j in range(i+1, len(lines)):
                            if lines[j].strip():
                                status = lines[j].strip()
                                break
                        break

                adrs.append({
                    "filename": file_path.name,
                    "title": title,
                    "status": status
                })
            except Exception as e:
                logger.error(f"Error reading {file_path}: {e}")

        return adrs

    def create_adr(self, title: str, status: str = "Proposed", content: Optional[str] = None) -> Path:
        """Create a new ADR file."""
        if not self.adr_dir.exists():
            self.init_adr_repo()

        # Determine next number
        existing_files = list(self.adr_dir.glob("*.md"))
        max_num = 0
        for f in existing_files:
            try:
                num_str = f.name.split("-")[0]
                if num_str.isdigit():
                    max_num = max(max_num, int(num_str))
            except ValueError:
                pass

        next_num = max_num + 1
        slug = title.lower().replace(" ", "-")
        # Remove non-alphanumeric except hyphen
        slug = re.sub(r'[^a-z0-9-]', '', slug)

        filename = f"{next_num:04d}-{slug}.md"
        file_path = self.adr_dir / filename

        if content:
            # If content is provided (e.g. from AI), verify it has the title
            if not content.startswith("#"):
                content = f"# {next_num}. {title}\n\n" + content

            # Ensure date is present
            if "Date:" not in content:
                content = content.replace(f"# {next_num}. {title}", f"# {next_num}. {title}\n\nDate: {datetime.now().strftime('%Y-%m-%d')}")

            file_path.write_text(content, encoding="utf-8")
        else:
            default_content = f"""# {next_num}. {title}

Date: {datetime.now().strftime("%Y-%m-%d")}

## Status

{status}

## Context

The issue motivating this decision...

## Decision

The change that we are proposing or doing...

## Consequences

What becomes easier or more difficult to do and any risks introduced...
"""
            file_path.write_text(default_content, encoding="utf-8")

        return file_path

    def update_status(self, filename_or_id: str, new_status: str) -> bool:
        """Update the status of an ADR."""
        target_file = None

        # Try to find by ID first
        if filename_or_id.isdigit():
            pattern = f"{int(filename_or_id):04d}-*.md"
            files = list(self.adr_dir.glob(pattern))
            if files:
                target_file = files[0]
        else:
            target_file = self.adr_dir / filename_or_id

        if not target_file or not target_file.exists():
            return False

        content = target_file.read_text(encoding="utf-8")

        lines = content.splitlines()
        new_lines = []
        in_status = False
        status_updated = False

        for line in lines:
            if line.strip() == "## Status":
                new_lines.append(line)
                in_status = True
                continue

            if in_status:
                if line.strip() == "":
                    # Keep empty lines if we haven't updated yet?
                    # No, usually status is tight.
                    new_lines.append(line)
                    continue
                elif line.startswith("##"):
                    # Next section
                    if not status_updated:
                         new_lines.insert(-1, new_status) # Insert before header
                         if new_lines[-1] != "":
                             new_lines.insert(-1, "")
                         status_updated = True
                    in_status = False
                    new_lines.append(line)
                else:
                    if not status_updated:
                        new_lines.append(new_status)
                        status_updated = True
                    # Skip the old status line
            else:
                new_lines.append(line)

        if in_status and not status_updated:
             new_lines.append(new_status)

        target_file.write_text("\n".join(new_lines), encoding="utf-8")
        return True

    async def generate_adr_content(self, title: str, context: str, agent_type: str = "gemini", model: Optional[str] = None) -> str:
        """Generate ADR content using AI."""

        # Load prompt
        prompt_path = Path(__file__).parent / "prompts" / "adr_prompt.md"
        if not prompt_path.exists():
             base_prompt = "Generate an ADR for: {context}"
        else:
             base_prompt = prompt_path.read_text(encoding="utf-8")

        full_prompt = base_prompt.replace("{context}", f"Title: {title}\n\n{context}")

        # Config
        config = Config(
            project_dir=self.project_dir,
            agent_type=agent_type,
            model=model,
            verbose=False,
            max_iterations=1,
            stream_output=False
        )

        # Agent
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

        # Lazy import to avoid circular dependency issues if any
        # though we imported at top level, which is fine in shared usually.

        # Using run_agent_session
        # Returns: (success, response, actions)
        _, response, _ = await agent.run_agent_session(full_prompt)

        return response
