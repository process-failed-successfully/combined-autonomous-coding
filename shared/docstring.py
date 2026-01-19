import ast
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from shared.utils import IGNORED_DIRS
from shared.config import Config
from agents.shared.prompts import get_docstring_prompt
from agents.gemini import GeminiAgent
from agents.cursor import CursorAgent
from agents.local import LocalAgent
from agents.openrouter import OpenRouterAgent

logger = logging.getLogger(__name__)


class DocstringManager:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir

    def scan(self) -> List[Dict[str, Any]]:
        """
        Scans the project for functions and classes missing docstrings.
        Returns a list of dictionaries with metadata.
        """
        results = []
        for path in self.project_dir.rglob("*.py"):
            # Skip ignored dirs
            if any(part in IGNORED_DIRS for part in path.parts):
                continue

            try:
                code = path.read_text(encoding="utf-8")
                tree = ast.parse(code)
            except Exception as e:
                logger.warning(f"Failed to parse {path}: {e}")
                continue

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    # Skip if docstring exists
                    if ast.get_docstring(node):
                        continue

                    # Skip one-liners (heuristic: body starts on same line as def)
                    # node.lineno is the 'def' line.
                    # node.body[0].lineno is the first statement line.
                    if node.body and node.body[0].lineno == node.lineno:
                        continue

                    results.append({
                        "file": path,
                        "name": node.name,
                        "type": type(node).__name__,
                        "lineno": node.lineno,
                        "node": node
                    })
        return results

    async def generate_and_apply(
        self,
        items: List[Dict[str, Any]],
        agent_type: str = "gemini",
        model: Optional[str] = None
    ) -> int:
        """
        Generates and applies docstrings. Returns count of applied docstrings.
        """
        # Setup Agent
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

        agent = agent_class(config)  # type: ignore
        prompt_template = get_docstring_prompt()

        # Group by file
        items_by_file: Dict[Path, List[Dict[str, Any]]] = {}
        for item in items:
            path = item["file"]
            if path not in items_by_file:
                items_by_file[path] = []
            items_by_file[path].append(item)

        applied_count = 0

        for path, file_items in items_by_file.items():
            try:
                # Read file fresh
                code_text = path.read_text(encoding="utf-8")
                code_lines = code_text.splitlines()

                # We need to process from bottom to top to preserve line numbers
                file_items.sort(key=lambda x: x["lineno"], reverse=True)

                file_modified = False

                for item in file_items:
                    node = item["node"]

                    # Get source segment
                    full_source = code_text  # Use original text for extraction
                    source_segment = ast.get_source_segment(full_source, node)

                    if not source_segment:
                        logger.warning(f"Could not extract source for {item['name']} in {path}")
                        continue

                    # Prompt
                    prompt = prompt_template.replace("{code}", source_segment)

                    # Call Agent
                    print(f"Generating docstring for {item['name']} in {path.name}...")
                    try:
                        _, response, _ = await agent.run_agent_session(prompt)
                        docstring = response.strip()

                        # Cleanup: remove surrounding quotes if agent added them duplicatively?
                        # The prompt asks for quotes.
                        # Sometimes agents return `"""doc"""` or just `doc`.
                        # We should robustly handle this.
                        if docstring.startswith('"""') and docstring.endswith('"""'):
                            # Good.
                            pass
                        elif docstring.startswith("'''") and docstring.endswith("'''"):
                            docstring = '"""' + docstring[3:-3] + '"""'
                        else:
                            # Wrap it
                            docstring = '"""' + docstring + '"""'

                        # Determine insertion point
                        # logic from experiment:
                        # Find the body start.
                        # node.body[0] is first statement.
                        # We want to insert before it.

                        first_stmt = node.body[0]
                        start_line_idx = first_stmt.lineno - 1  # 0-indexed

                        # Determine indentation of first stmt
                        line_content = code_lines[start_line_idx]
                        indentation = len(line_content) - len(line_content.lstrip())
                        indent_str = " " * indentation

                        # Format docstring with indentation
                        # If multi-line, indent all lines
                        doc_lines = docstring.splitlines()
                        formatted_doc = []
                        for i, dline in enumerate(doc_lines):
                            if i == 0:
                                formatted_doc.append(indent_str + dline)
                            else:
                                formatted_doc.append(indent_str + dline)

                        formatted_doc_str = "\n".join(formatted_doc)

                        code_lines.insert(start_line_idx, formatted_doc_str)
                        file_modified = True
                        applied_count += 1

                    except Exception as e:
                        logger.error(f"Error generating docstring for {item['name']}: {e}")

                if file_modified:
                    path.write_text("\n".join(code_lines), encoding="utf-8")
                    print(f"Updated {path.name}")

            except Exception as e:
                logger.error(f"Error processing file {path}: {e}")

        return applied_count
