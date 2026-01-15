import shutil
import subprocess
import sys
import json
import re
from pathlib import Path

def detect_project_type(project_dir: Path):
    """Detects the project type based on dependency files."""
    if (project_dir / "pnpm-lock.yaml").exists() and shutil.which("pnpm"):
        return "pnpm"
    elif (project_dir / "yarn.lock").exists() and shutil.which("yarn"):
        return "yarn"
    elif (project_dir / "package.json").exists() and shutil.which("npm"):
        return "npm"
    elif (project_dir / "requirements.txt").exists():
        return "pip"
    return None

def add_dependency(project_dir: Path, package_name: str):
    """Adds a dependency to the project."""
    project_type = detect_project_type(project_dir)
    if not project_type:
        print("Unsupported project type.", file=sys.stderr)
        return False

    print(f"Adding dependency '{package_name}' using {project_type}...")
    if project_type == "pip":
        req_file = project_dir / "requirements.txt"
        content = req_file.read_text()
        with open(req_file, "a") as f:
            if content.strip() == "":
                f.write(package_name)
            else:
                f.write(f"\n{package_name}")
        cmd = [sys.executable, "-m", "pip", "install", package_name]
    elif project_type == "npm":
        cmd = ["npm", "install", package_name, "--save"]
    elif project_type == "yarn":
        cmd = ["yarn", "add", package_name]
    elif project_type == "pnpm":
        cmd = ["pnpm", "add", package_name]
    else:
        print(f"Unsupported project type: {project_type}", file=sys.stderr)
        return False

    result = subprocess.run(cmd, cwd=project_dir, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error adding dependency:\n{result.stderr}", file=sys.stderr)
        return False
    print(f"Successfully added '{package_name}'.")
    return True

def remove_dependency(project_dir: Path, package_name: str):
    """Removes a dependency from the project."""
    project_type = detect_project_type(project_dir)
    if not project_type:
        print("Unsupported project type.", file=sys.stderr)
        return False

    print(f"Removing dependency '{package_name}' using {project_type}...")
    if project_type == "pip":
        req_file = project_dir / "requirements.txt"
        lines = req_file.read_text().splitlines()
        # This regex handles package names with extras and various version specifiers
        pattern = re.compile(r"^\s*" + re.escape(package_name) + r"(\s*\[.*\])?\s*([<>=!~]=.*)?\s*")
        new_lines = [line for line in lines if not pattern.match(line)]
        req_file.write_text("\n".join(new_lines))
        cmd = [sys.executable, "-m", "pip", "uninstall", "-y", package_name]
    elif project_type == "npm":
        cmd = ["npm", "uninstall", package_name, "--save"]
    elif project_type == "yarn":
        cmd = ["yarn", "remove", package_name]
    elif project_type == "pnpm":
        cmd = ["pnpm", "remove", package_name]
    else:
        print(f"Unsupported project type: {project_type}", file=sys.stderr)
        return False

    result = subprocess.run(cmd, cwd=project_dir, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error removing dependency:\n{result.stderr}", file=sys.stderr)
        return False
    print(f"Successfully removed '{package_name}'.")
    return True

def list_dependencies(project_dir: Path):
    """Lists the project's dependencies."""
    project_type = detect_project_type(project_dir)
    if not project_type:
        print("Unsupported project type.", file=sys.stderr)
        return False

    print(f"Listing dependencies for {project_type} project...")
    if project_type == "pip":
        req_file = project_dir / "requirements.txt"
        if req_file.exists():
            print(req_file.read_text())
        else:
            print("requirements.txt not found.")
            return False
    elif project_type in ["npm", "yarn", "pnpm"]:
        package_file = project_dir / "package.json"
        if package_file.exists():
            data = json.loads(package_file.read_text())
            dependencies = data.get("dependencies", {})
            for dep, version in dependencies.items():
                print(f"{dep}@{version}")
        else:
            print("package.json not found.")
            return False
    return True

def sync_dependencies(project_dir: Path):
    """Installs all dependencies from the project's dependency files."""
    project_type = detect_project_type(project_dir)
    if not project_type:
        print("Unsupported project type.", file=sys.stderr)
        return False

    print(f"Syncing dependencies using {project_type}...")
    if project_type == "pip":
        cmd = [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
    elif project_type == "npm":
        cmd = ["npm", "install"]
    elif project_type == "yarn":
        cmd = ["yarn", "install"]
    elif project_type == "pnpm":
        cmd = ["pnpm", "install"]
    else:
        print(f"Unsupported project type: {project_type}", file=sys.stderr)
        return False

    result = subprocess.run(cmd, cwd=project_dir, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error syncing dependencies:\n{result.stderr}", file=sys.stderr)
        return False
    print("Dependencies synced successfully.")
    return True
