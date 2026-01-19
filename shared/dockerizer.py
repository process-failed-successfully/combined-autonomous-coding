from pathlib import Path


class Dockerizer:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir.resolve()

    def detect_project_type(self) -> str:
        if (self.project_dir / "package.json").exists():
            return "node"
        if (self.project_dir / "requirements.txt").exists() or (self.project_dir / "pyproject.toml").exists():
            return "python"
        if (self.project_dir / "go.mod").exists():
            return "go"
        return "unknown"

    def generate_dockerfile(self, project_type: str) -> str:
        if project_type == "python":
            return self._python_dockerfile()
        elif project_type == "node":
            return self._node_dockerfile()
        elif project_type == "go":
            return self._go_dockerfile()
        else:
            return "# Could not detect project type for Dockerfile generation."

    def _python_dockerfile(self) -> str:
        version = "3.10-slim"

        content = [
            f"FROM python:{version}",
            "WORKDIR /app",
            "",
            "ENV PYTHONDONTWRITEBYTECODE=1",
            "ENV PYTHONUNBUFFERED=1",
            "",
            "# Install dependencies",
        ]

        if (self.project_dir / "requirements.txt").exists():
            content.extend([
                "COPY requirements.txt .",
                "RUN pip install --no-cache-dir -r requirements.txt"
            ])
        elif (self.project_dir / "pyproject.toml").exists():
            # Minimal support for poetry/others if needed, but keeping it simple for now
            # Assuming if pyproject.toml exists, user might want to install via pip .
            content.extend([
                "COPY pyproject.toml .",
                "RUN pip install ."
            ])

        content.extend([
            "",
            "# Copy application code",
            "COPY . .",
            "",
            "# Command to run the application"
        ])

        # Try to infer a better CMD
        if (self.project_dir / "app.py").exists():
            content.append('CMD ["python", "app.py"]')
        elif (self.project_dir / "main.py").exists():
            content.append('CMD ["python", "main.py"]')
        elif (self.project_dir / "wsgi.py").exists():
            content.append('CMD ["gunicorn", "wsgi:app"]')
        else:
            content.append('CMD ["python", "app.py"]')  # Fallback

        return "\n".join(content)

    def _node_dockerfile(self) -> str:
        content = [
            "FROM node:18-alpine",
            "WORKDIR /app",
            "",
            "COPY package*.json ./",
            "RUN npm install",
            "",
            "COPY . .",
            "",
            'CMD ["npm", "start"]'
        ]
        return "\n".join(content)

    def _go_dockerfile(self) -> str:
        content = [
            "FROM golang:1.21-alpine AS builder",
            "WORKDIR /app",
            "",
            "COPY go.mod go.sum ./",
            "RUN go mod download",
            "",
            "COPY . .",
            "RUN go build -o main .",
            "",
            "FROM alpine:latest",
            "WORKDIR /root/",
            "COPY --from=builder /app/main .",
            'CMD ["./main"]'
        ]
        return "\n".join(content)

    def generate_docker_compose(self, project_type: str) -> str:
        # Heuristic for port
        port = "8000"
        if project_type == "node":
            port = "3000"

        return f"""version: '3.8'
services:
  app:
    build: .
    ports:
      - "{port}:{port}"
    volumes:
      - .:/app
    environment:
      - ENV=development
"""

    def generate_dockerignore(self, project_type: str) -> str:
        common = [
            ".git",
            ".gitignore",
            "Dockerfile",
            "docker-compose.yml",
            ".dockerignore",
            ".env",
            ".agent_history",
            ".agent_db.sqlite",
            "worktrees/",
            ".agent_trash/",
            ".agent_archives/"
        ]
        if project_type == "python":
            common.extend(["__pycache__", "*.pyc", "*.pyo", ".venv", "venv", "env"])
        elif project_type == "node":
            common.extend(["node_modules", "npm-debug.log", "dist", "build"])

        return "\n".join(common)
