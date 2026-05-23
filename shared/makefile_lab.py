import sys
from typing import Dict, Any

class MakefileLabManager:
    """Generates standard Makefiles based on language profiles."""

    PROFILES = {
        "python": {
            "build": "",
            "install": "pip install -r requirements.txt",
            "test": "pytest",
            "lint": "flake8 .",
            "clean": "find . -type d -name __pycache__ -exec rm -r {} +",
            "run": "python main.py"
        },
        "node": {
            "build": "npm run build",
            "install": "npm install",
            "test": "npm test",
            "lint": "npm run lint",
            "clean": "rm -rf node_modules dist",
            "run": "npm start"
        },
        "go": {
            "build": "go build -o bin/app",
            "install": "go mod download",
            "test": "go test ./...",
            "lint": "golangci-lint run",
            "clean": "rm -rf bin/",
            "run": "go run ."
        },
        "rust": {
            "build": "cargo build --release",
            "install": "",
            "test": "cargo test",
            "lint": "cargo clippy",
            "clean": "cargo clean",
            "run": "cargo run"
        },
        "generic": {
            "build": "echo 'Build step'",
            "install": "echo 'Install dependencies step'",
            "test": "echo 'Test step'",
            "lint": "echo 'Lint step'",
            "clean": "echo 'Clean step'",
            "run": "echo 'Run step'"
        }
    }

    def generate(self, lang: str) -> str:
        lang = lang.lower()
        if lang not in self.PROFILES:
            raise ValueError(f"Unknown language profile: {lang}. Available: {', '.join(self.PROFILES.keys())}")

        profile = self.PROFILES[lang]

        lines = []
        lines.append(f"# Makefile for {lang.capitalize()} Project")
        lines.append(".PHONY: all build install test lint clean run")
        lines.append("")
        lines.append("all: clean install lint test build")
        lines.append("")

        # We ensure commands with empty strings aren't completely blank targets, but simple echo or empty
        for target, cmd in profile.items():
            lines.append(f"{target}:")
            if cmd:
                lines.append(f"\t{cmd}")
            else:
                lines.append("\t@echo 'Nothing to do for this target'")
            lines.append("")

        return "\n".join(lines)


def run_makefile_lab_logic(args):
    """CLI logic for Makefile Lab."""
    manager = MakefileLabManager()

    try:
        content = manager.generate(args.lang)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if getattr(args, "output", None):
        try:
            with open(args.output, "w") as f:
                f.write(content)
            print(f"Makefile generated and saved to {args.output}")
        except OSError as e:
            print(f"Error writing to file: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(content)

    sys.exit(0)
