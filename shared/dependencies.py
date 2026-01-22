import json
import re
import requests
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional


class DependencyAnalyzer:
    """
    Analyzes project dependencies from manifest files.
    """

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir.resolve()
        self.license_cache = {}

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
                        if name != "python":  # Poetry often includes python version
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

    def check_updates(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Checks for updates for all found dependencies."""
        print("Checking for updates (this may take a moment)...")

        # Python
        for file_info in data.get("python", []):
            for dep in file_info.get("dependencies", []):
                latest = self._get_latest_pypi_version(dep["name"])
                if latest:
                    dep["latest"] = latest
                    # Basic check: if latest is not in version string (e.g. '==1.0.0')
                    # This is naive but works for '==', '>=', etc if versions don't match.
                    # For a robust solution we'd need a semver parser.
                    # Here we treat any mismatch in string presence or just difference as potentially outdated
                    current_clean = dep.get("version", "").replace("==", "").replace(">=", "").strip()
                    dep["outdated"] = current_clean != latest

        # Node
        for file_info in data.get("node", []):
            for dep in file_info.get("dependencies", []):
                latest = self._get_latest_npm_version(dep["name"])
                if latest:
                    dep["latest"] = latest
                    current_clean = dep.get("version", "").replace("^", "").replace("~", "").strip()
                    dep["outdated"] = current_clean != latest

        return data

    def check_licenses(self, data: Dict[str, Any], allow_list: Optional[List[str]] = None, deny_list: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Checks licenses for all found dependencies.
        Returns a list of violations (or all items if just listing).
        """
        import concurrent.futures
        print("Checking licenses (this may take a moment)...")
        results = []

        def normalize(lic):
            if not lic: return "unknown"
            # Basic normalization: lowercase, remove common suffixes
            return lic.lower().replace(" license", "").replace(" software", "").strip()

        allow_set = {normalize(l) for l in allow_list} if allow_list else set()
        deny_set = {normalize(l) for l in deny_list} if deny_list else set()

        # Helper to process a dependency
        def process_dep(lang, file_info, dep):
            name = dep["name"]
            license_name = "Unknown"

            if lang == "python":
                license_name = self._get_pypi_license(name) or "Unknown"
            elif lang == "node":
                license_name = self._get_npm_license(name) or "Unknown"

            status = "OK"
            msg = ""
            lic_norm = normalize(license_name)

            if deny_set and lic_norm in deny_set:
                status = "VIOLATION"
                msg = f"License '{license_name}' is explicitly denied."
            elif allow_set and lic_norm not in allow_set:
                status = "VIOLATION"
                msg = f"License '{license_name}' is not in the allowed list."

            # If no lists provided, just list everything as OK (audit mode)
            if not allow_set and not deny_set:
                status = "INFO"

            return {
                "package": name,
                "version": dep.get("version", ""),
                "license": license_name,
                "file": file_info["source"],
                "status": status,
                "message": msg
            }

        # Collect all tasks
        tasks = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            # Python
            for file_info in data.get("python", []):
                for dep in file_info.get("dependencies", []):
                    tasks.append(executor.submit(process_dep, "python", file_info, dep))

            # Node
            for file_info in data.get("node", []):
                for dep in file_info.get("dependencies", []):
                    tasks.append(executor.submit(process_dep, "node", file_info, dep))

            for future in concurrent.futures.as_completed(tasks):
                try:
                    results.append(future.result())
                except Exception as e:
                    print(f"Error checking license: {e}")

        return results

    def _get_latest_pypi_version(self, package_name: str) -> Optional[str]:
        try:
            url = f"https://pypi.org/pypi/{package_name}/json"
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                return response.json()["info"]["version"]
        except Exception:
            pass
        return None

    def _get_latest_npm_version(self, package_name: str) -> Optional[str]:
        try:
            url = f"https://registry.npmjs.org/{package_name}/latest"
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                return response.json()["version"]
        except Exception:
            pass
        return None

    def _get_pypi_license(self, package_name: str) -> Optional[str]:
        if package_name in self.license_cache:
            return self.license_cache[package_name]

        try:
            url = f"https://pypi.org/pypi/{package_name}/json"
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                info = response.json()["info"]

                # 1. Try Classifiers first (more standard)
                classifiers = info.get("classifiers", [])
                for c in classifiers:
                    if c.startswith("License :: OSI Approved :: "):
                        lic = c.replace("License :: OSI Approved :: ", "").strip()
                        self.license_cache[package_name] = lic
                        return lic
                    elif c.startswith("License :: "):
                        lic = c.replace("License :: ", "").strip()
                        # Avoid "License :: OSI Approved" parent category
                        if lic != "OSI Approved":
                            self.license_cache[package_name] = lic
                            return lic

                # 2. Try license field
                license_field = info.get("license", "")
                if license_field and len(license_field) < 50: # Avoid long license texts
                     self.license_cache[package_name] = license_field
                     return license_field

        except Exception:
            pass

        self.license_cache[package_name] = None
        return None

    def _get_npm_license(self, package_name: str) -> Optional[str]:
        if package_name in self.license_cache:
            return self.license_cache[package_name]

        try:
            url = f"https://registry.npmjs.org/{package_name}/latest"
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                data = response.json()
                license_field = data.get("license", "")

                # Sometimes it's a dict { type: "MIT", ... }
                if isinstance(license_field, dict):
                    license_field = license_field.get("type", "")

                if license_field:
                    self.license_cache[package_name] = license_field
                    return license_field
        except Exception:
            pass

        self.license_cache[package_name] = None
        return None

    def generate_updates_table(self, data: Dict[str, Any]) -> str:
        output = []

        for lang, files in data.items():
            if not files:
                continue

            output.append(f"\n📦 {lang.capitalize()} Updates")
            header = f"  {'Package':<30} | {'Current':<15} | {'Latest':<15}"
            output.append(header)
            output.append("  " + "-" * len(header))

            updates_found = False
            for file_info in files:
                for dep in file_info.get("dependencies", []):
                    if dep.get("outdated"):
                        updates_found = True
                        name = dep["name"]
                        current = dep.get("version", "") or "(none)"
                        latest = dep.get("latest", "")
                        output.append(f"  {name:<30} | {current:<15} | {latest:<15}")

            if not updates_found:
                output.append("  ✅ All dependencies appear up to date.")

        return "\n".join(output)


class DependencyUpdater:
    """
    Handles updating dependencies in project files.
    """

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir.resolve()

    def update_dependency(self, file_path: Path, package_name: str, new_version: str, dep_type: str = "prod") -> bool:
        """
        Updates a dependency in the specified file.
        Returns True if successful, False otherwise.
        """
        if file_path.name == "requirements.txt":
            return self._update_python_requirement(file_path, package_name, new_version)
        elif file_path.name == "package.json":
            return self._update_node_package(file_path, package_name, new_version, dep_type)
        else:
            print(f"Skipping update for unsupported file: {file_path.name}")
            return False

    def _update_python_requirement(self, file_path: Path, package_name: str, new_version: str) -> bool:
        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.splitlines()
            new_lines = []
            updated = False

            # Pattern to match the package name at the start of the line, ignoring case.
            # It also captures any existing version specifiers and comments.
            # Group 1: Package Name
            # Group 2: Version Spec (optional)
            # Group 3: Comment (optional)
            pattern = re.compile(r"^(" + re.escape(package_name) + r")([<=>!~].*)?(\s*#.*)?$", re.IGNORECASE)

            for line in lines:
                if not line.strip() or line.strip().startswith('#'):
                    new_lines.append(line)
                    continue

                match = pattern.match(line.strip())
                if match:
                    # Found the package. Preserve name case from file (Group 1).
                    name_in_file = match.group(1)
                    comment = match.group(3) or ""

                    # Update to exact version
                    new_line = f"{name_in_file}=={new_version}{comment}"
                    new_lines.append(new_line)
                    updated = True
                else:
                    new_lines.append(line)

            if updated:
                file_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
                return True
            else:
                print(f"Could not find package '{package_name}' in {file_path.name}")
        except Exception as e:
            print(f"Error updating requirements.txt: {e}")
        return False

    def _detect_package_manager(self) -> str:
        if (self.project_dir / "pnpm-lock.yaml").exists() and shutil.which("pnpm"):
            return "pnpm"
        if (self.project_dir / "yarn.lock").exists() and shutil.which("yarn"):
            return "yarn"
        if shutil.which("npm"):
            return "npm"
        return ""

    def _update_node_package(self, file_path: Path, package_name: str, new_version: str, dep_type: str) -> bool:
        pm = self._detect_package_manager()
        if not pm:
            print("No compatible Node.js package manager found (npm, yarn, pnpm).")
            return False

        # Construct command
        cmd = []
        if pm == "npm":
            cmd = ["npm", "install"]
            if dep_type == "dev":
                cmd.append("--save-dev")
            cmd.append(f"{package_name}@{new_version}")
        elif pm == "yarn":
            cmd = ["yarn", "add"]
            if dep_type == "dev":
                cmd.append("--dev")
            cmd.append(f"{package_name}@{new_version}")
        elif pm == "pnpm":
            cmd = ["pnpm", "add"]
            if dep_type == "dev":
                cmd.append("--save-dev")
            cmd.append(f"{package_name}@{new_version}")

        print(f"Running: {' '.join(cmd)}")
        try:
            # We run the command in the directory containing package.json (usually project root)
            subprocess.run(cmd, cwd=file_path.parent, check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError as e:
            err = e.stderr.decode() if e.stderr else str(e)
            print(f"Error updating node package: {err}")
            return False


def _run_deps_logic(project_dir: Path, output_format: str = "text", check_updates: bool = False):
    analyzer = DependencyAnalyzer(project_dir)
    data = analyzer.scan()

    if check_updates:
        data = analyzer.check_updates(data)
        if output_format == "json":
            return json.dumps(data, indent=2)
        else:
            # For text mode, we show the updates table instead of the tree if check is requested
            return analyzer.generate_updates_table(data)

    if output_format == "json":
        return json.dumps(data, indent=2)
    elif output_format == "mermaid":
        return analyzer.generate_mermaid(data)
    else:
        return analyzer.generate_tree(data)
