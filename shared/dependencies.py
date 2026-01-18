import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

class DependencyAnalyzer:
    """
    Analyzes project dependencies from manifest files.
    """

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir.resolve()

    def scan(self) -> Dict[str, Any]:
        """Scans the project directory for dependency files and parses them."""
        results = {
            "python": self._scan_python(),
            "node": self._scan_node(),
        }
        return results

    def _scan_python(self) -> List[Dict[str, Any]]:
        deps = []

        # 1. requirements.txt
        req_file = self.project_dir / "requirements.txt"
        if req_file.exists():
            parsed = self._parse_requirements_txt(req_file)
            if parsed:
                deps.append({
                    "source": "requirements.txt",
                    "dependencies": parsed
                })

        # 2. pyproject.toml
        toml_file = self.project_dir / "pyproject.toml"
        if toml_file.exists():
            parsed = self._parse_pyproject_toml(toml_file)
            if parsed:
                deps.append({
                    "source": "pyproject.toml",
                    "dependencies": parsed
                })

        return deps

    def _scan_node(self) -> List[Dict[str, Any]]:
        deps = []

        # package.json
        pkg_file = self.project_dir / "package.json"
        if pkg_file.exists():
            parsed = self._parse_package_json(pkg_file)
            if parsed:
                deps.append({
                    "source": "package.json",
                    "dependencies": parsed
                })

        return deps

    def _parse_requirements_txt(self, file_path: Path) -> List[Dict[str, str]]:
        dependencies = []
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            for line in content.splitlines():
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith("#"):
                    continue

                # Simple parsing: extract name
                # Covers: package, package==1.0, package>=1.0, package<2.0
                match = re.match(r"^([a-zA-Z0-9\-_]+)(.*)$", line)
                if match:
                    name = match.group(1)
                    version_spec = match.group(2).strip()
                    dependencies.append({
                        "name": name,
                        "version": version_spec
                    })
        except Exception:
            pass
        return dependencies

    def _parse_package_json(self, file_path: Path) -> List[Dict[str, str]]:
        dependencies = []
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            data = json.loads(content)

            # Prod dependencies
            for name, version in data.get("dependencies", {}).items():
                dependencies.append({
                    "name": name,
                    "version": version,
                    "type": "prod"
                })

            # Dev dependencies
            for name, version in data.get("devDependencies", {}).items():
                dependencies.append({
                    "name": name,
                    "version": version,
                    "type": "dev"
                })

        except Exception:
            pass
        return dependencies

    def _parse_pyproject_toml(self, file_path: Path) -> List[Dict[str, str]]:
        dependencies = []
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")

            # Very basic TOML parsing for dependencies block
            # looking for [project.dependencies] or [tool.poetry.dependencies]

            current_section = None
            in_dependency_list = False

            for line in content.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                # Section detection
                if line.startswith("[") and line.endswith("]"):
                    current_section = line[1:-1]
                    # Reset list parsing on new section, unless it is project.dependencies (unlikely valid toml but possible in loose parsing)
                    in_dependency_list = False
                    continue

                # Start of dependency list in [project]
                if current_section == "project" and line.startswith("dependencies = ["):
                    in_dependency_list = True
                    # If the line ends with ], it's a one-liner or empty
                    if line.endswith("]"):
                        # Parse inline content if needed, but let's stick to multiline for MVP or regex matching inside
                        # Extract content inside [...]
                        pass
                    continue

                # End of list
                if in_dependency_list and line == "]":
                    in_dependency_list = False
                    continue

                # Handle [tool.poetry.dependencies] (key = value)
                if current_section == "tool.poetry.dependencies":
                    if "=" in line:
                        parts = line.split("=", 1)
                        name = parts[0].strip()
                        version = parts[1].strip().strip('"').strip("'")
                        if name != "python": # Poetry often includes python version
                            dependencies.append({
                                "name": name,
                                "version": version
                            })

                # Handle list items
                if in_dependency_list:
                     # Usually strings in a list
                     # Regex fallback for strings like '"flask>=2.0",'
                     # We use non-greedy matching for version part to stop before the closing quote
                     match = re.match(r'^[\'"]([a-zA-Z0-9\-_]+)(.*?)[\'"],?$', line)
                     if match:
                         name = match.group(1)
                         version = match.group(2).strip()
                         dependencies.append({
                            "name": name,
                            "version": version
                        })

        except Exception:
            pass
        return dependencies

    def generate_tree(self, data: Dict[str, Any]) -> str:
        output = []

        for lang, files in data.items():
            if not files:
                continue
            output.append(f"📦 {lang.capitalize()}")
            for file_info in files:
                source = file_info["source"]
                output.append(f"  📄 {source}")
                deps = file_info["dependencies"]
                if not deps:
                    output.append("    (no dependencies)")
                for dep in deps:
                    name = dep["name"]
                    version = dep.get("version", "")
                    dtype = dep.get("type", "")
                    type_str = f" ({dtype})" if dtype else ""
                    output.append(f"    ├─ {name} {version}{type_str}")

        return "\n".join(output)

    def generate_mermaid(self, data: Dict[str, Any]) -> str:
        lines = ["graph TD"]
        root_id = "root"
        lines.append(f"    {root_id}[Project]")

        for lang, files in data.items():
            if not files:
                continue

            lang_id = f"lang_{lang}"
            lines.append(f"    {root_id} --> {lang_id}[{lang.capitalize()}]")

            for i, file_info in enumerate(files):
                source = file_info["source"]
                file_id = f"{lang}_file_{i}"
                lines.append(f"    {lang_id} --> {file_id}({source})")

                for j, dep in enumerate(file_info["dependencies"]):
                    name = dep["name"]
                    version = dep.get("version", "")
                    safe_name = re.sub(r'[^a-zA-Z0-9]', '_', name)
                    dep_id = f"dep_{lang}_{i}_{safe_name}"

                    label = f"{name}\\n{version}"
                    lines.append(f"    {file_id} --> {dep_id}[{label}]")

                    # Style dev deps differently?
                    if dep.get("type") == "dev":
                        lines.append(f"    style {dep_id} stroke-dasharray: 5 5")

        return "\n".join(lines)

def _run_deps_logic(project_dir: Path, output_format: str = "text"):
    analyzer = DependencyAnalyzer(project_dir)
    data = analyzer.scan()

    if output_format == "json":
        return json.dumps(data, indent=2)
    elif output_format == "mermaid":
        return analyzer.generate_mermaid(data)
    else:
        return analyzer.generate_tree(data)
