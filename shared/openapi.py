import logging
import fnmatch
from pathlib import Path
from typing import List, Optional, Dict, Any, Type

from shared.config import Config
from shared.dependencies import DependencyAnalyzer
from agents.shared.base_agent import BaseAgent
from agents.gemini import GeminiAgent
from agents.cursor import CursorAgent
from agents.local import LocalAgent
from agents.openrouter import OpenRouterAgent

logger = logging.getLogger(__name__)

class OpenAPIGenerator:
    """
    Generates an OpenAPI specification for a project using AI.
    """

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.analyzer = DependencyAnalyzer(project_dir)

    def detect_framework(self) -> str:
        """
        Detects the web framework used in the project.
        """
        scan_data = self.analyzer.scan()

        # Flatten dependencies
        python_deps = set()
        for f in scan_data.get("python", []):
            for d in f.get("dependencies", []):
                python_deps.add(d["name"].lower())

        node_deps = set()
        for f in scan_data.get("node", []):
            for d in f.get("dependencies", []):
                node_deps.add(d["name"].lower())

        # Check Python
        if "fastapi" in python_deps: return "fastapi"
        if "flask" in python_deps: return "flask"
        if "django" in python_deps: return "django"
        if "bottle" in python_deps: return "bottle"
        if "pyramid" in python_deps: return "pyramid"

        # Check Node
        if "express" in node_deps: return "express"
        if "nestjs" in node_deps or "@nestjs/core" in node_deps: return "nestjs"
        if "fastify" in node_deps: return "fastify"
        if "koa" in node_deps: return "koa"

        return "unknown"

    def scan_routes(self, framework: str) -> List[Path]:
        """
        Scans the project for files likely to contain route definitions.
        """
        relevant_files = []

        # Define patterns based on framework
        patterns = []
        content_indicators = [] # Simple string checks in file content

        if framework == "flask":
            patterns = ["app.py", "views.py", "routes.py", "*/views.py", "*/routes.py", "*/controllers/*.py"]
            content_indicators = ["@app.route", "Blueprint", "add_url_rule"]

        elif framework == "fastapi":
            patterns = ["main.py", "app.py", "routers/*.py", "*/routers/*.py", "api.py"]
            content_indicators = ["APIRouter", "FastAPI", "@app.get", "@app.post", "@router.get"]

        elif framework == "django":
            patterns = ["urls.py", "views.py", "*/urls.py", "*/views.py", "*/api.py"]
            content_indicators = ["urlpatterns", "path(", "re_path(", "def ", "class "]

        elif framework == "express":
            patterns = ["app.js", "server.js", "index.js", "routes/*.js", "controllers/*.js", "app.ts", "server.ts", "routes/*.ts"]
            content_indicators = ["express.Router", "app.get", "app.post", "router.get", "router.post"]

        else:
            # Generic fallback
            patterns = ["**/*.py", "**/*.js", "**/*.ts"]
            content_indicators = ["route", "api", "get", "post"]

        for path in self.project_dir.rglob("*"):
            if not path.is_file():
                continue

            # Skip ignored dirs
            if any(part.startswith(".") or part in ["__pycache__", "node_modules", "venv", "env"] for part in path.parts):
                continue

            # Check filename patterns
            # We match relative path to project dir
            rel_path = path.relative_to(self.project_dir)
            match = False
            for pattern in patterns:
                if fnmatch.fnmatch(str(rel_path), pattern):
                    match = True
                    break

            if match:
                # Optional: Check content to reduce noise
                try:
                    content = path.read_text(encoding="utf-8", errors="ignore")
                    if any(ind in content for ind in content_indicators):
                        relevant_files.append(path)
                except Exception:
                    pass

        return relevant_files

    async def generate(self, output_path: Path, agent_type: str = "gemini", model: Optional[str] = None) -> bool:
        """
        Generates the OpenAPI spec and saves it to output_path.
        """
        framework = self.detect_framework()
        print(f"Detected framework: {framework}")

        route_files = self.scan_routes(framework)
        print(f"Found {len(route_files)} relevant files for analysis.")

        if not route_files:
            print("No route files found. Cannot generate spec.")
            return False

        # Prepare context
        context_str = f"Framework: {framework}\n\n"
        for file_path in route_files[:10]: # Limit to top 10 files to avoid context overflow (MVP)
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                rel_path = file_path.relative_to(self.project_dir)
                context_str += f"--- File: {rel_path} ---\n{content}\n\n"
            except Exception as e:
                logger.warning(f"Could not read {file_path}: {e}")

        prompt = f"""
You are an expert API documentation generator.
Your task is to analyze the provided code files and generate a comprehensive OpenAPI 3.0 specification in YAML format.

Framework Detected: {framework}

Instructions:
1. Identify all API endpoints/routes defined in the code.
2. Infer the HTTP methods (GET, POST, PUT, DELETE, etc.).
3. Infer request parameters (path, query, body) and response schemas based on the code logic and any type hints or validation schemas (like Pydantic or Marshmallow).
4. Provide meaningful summaries and descriptions for operations.
5. If authentication is detected (e.g., JWT, Basic), include security schemes.
6. Output ONLY the valid OpenAPI YAML content. Do not include markdown blocks or explanations.

Source Code:
{context_str}
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

        agent_class_map: Dict[str, Type[BaseAgent]] = {
            "gemini": GeminiAgent,
            "cursor": CursorAgent,
            "local": LocalAgent,
            "openrouter": OpenRouterAgent,
        }

        agent_class = agent_class_map.get(agent_type)
        if not agent_class:
            raise ValueError(f"Unknown agent type: {agent_type}")

        agent = agent_class(config)

        print("Generating OpenAPI spec (this may take a minute)...")
        try:
            _, response, _ = await agent.run_agent_session(prompt)

            # Clean response
            spec_content = response.strip()
            if spec_content.startswith("```yaml"):
                spec_content = spec_content[7:]
            if spec_content.endswith("```"):
                spec_content = spec_content[:-3]

            # Ensure the output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(spec_content.strip(), encoding="utf-8")
            print(f"✅ OpenAPI spec saved to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error generating spec: {e}")
            return False
