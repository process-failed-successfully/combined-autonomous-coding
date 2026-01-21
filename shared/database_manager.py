import sys
import subprocess
import json
from pathlib import Path
from enum import Enum


class DatabaseFramework(Enum):
    DJANGO = "django"
    ALEMBIC = "alembic"  # Flask/FastAPI
    PRISMA = "prisma"
    SEQUELIZE = "sequelize"
    TYPEORM = "typeorm"
    RAILS = "rails"
    UNKNOWN = "unknown"


class DatabaseManager:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir.resolve()

    def detect_framework(self) -> DatabaseFramework:
        # Django
        if (self.project_dir / "manage.py").exists():
            return DatabaseFramework.DJANGO

        # Alembic
        if (self.project_dir / "alembic.ini").exists():
            return DatabaseFramework.ALEMBIC

        # Node.js frameworks
        package_json = self.project_dir / "package.json"
        if package_json.exists():
            try:
                with open(package_json, "r") as f:
                    data = json.load(f)
                    deps = data.get("dependencies", {})
                    dev_deps = data.get("devDependencies", {})
                    all_deps = {**deps, **dev_deps}

                    if "prisma" in all_deps or (self.project_dir / "prisma").exists():
                        return DatabaseFramework.PRISMA
                    if "sequelize" in all_deps:
                        return DatabaseFramework.SEQUELIZE
                    if "typeorm" in all_deps:
                        return DatabaseFramework.TYPEORM
            except json.JSONDecodeError:
                pass

        # Rails
        if (self.project_dir / "bin/rails").exists():
            return DatabaseFramework.RAILS
        if (self.project_dir / "Gemfile").exists():
            # Check content of Gemfile if needed, but for now fallback
            pass

        return DatabaseFramework.UNKNOWN

    def _run_cmd(self, cmd: list[str]) -> bool:
        print(f"Executing: {' '.join(cmd)}")
        try:
            subprocess.run(cmd, cwd=self.project_dir, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Command failed: {e}", file=sys.stderr)
            return False
        except FileNotFoundError:
            print(f"❌ Command not found: {cmd[0]}", file=sys.stderr)
            return False

    def migrate(self) -> bool:
        framework = self.detect_framework()
        print(f"Detected framework: {framework.value}")

        if framework == DatabaseFramework.DJANGO:
            # Try to find python executable
            python = "python"
            if (self.project_dir / "venv").exists():
                # This is a guess, platform dependent
                if sys.platform == "win32":
                    python = str(self.project_dir / "venv/Scripts/python.exe")
                else:
                    python = str(self.project_dir / "venv/bin/python")

            return self._run_cmd([python, "manage.py", "migrate"])

        elif framework == DatabaseFramework.ALEMBIC:
            return self._run_cmd(["alembic", "upgrade", "head"])

        elif framework == DatabaseFramework.PRISMA:
            return self._run_cmd(["npx", "prisma", "migrate", "dev"])

        elif framework == DatabaseFramework.SEQUELIZE:
            return self._run_cmd(["npx", "sequelize-cli", "db:migrate"])

        elif framework == DatabaseFramework.TYPEORM:
            # TypeORM is tricky, usually defined in package.json scripts
            # Trying a common convention
            return self._run_cmd(["npm", "run", "typeorm", "migration:run"])

        elif framework == DatabaseFramework.RAILS:
            return self._run_cmd(["bin/rails", "db:migrate"])

        else:
            print("❌ No supported database framework detected for migration.", file=sys.stderr)
            return False

    def seed(self) -> bool:
        framework = self.detect_framework()
        print(f"Detected framework: {framework.value}")

        if framework == DatabaseFramework.DJANGO:
            print("ℹ️  Django seeding is usually done via 'loaddata' or custom scripts.")
            # We could look for fixtures?
            return True

        elif framework == DatabaseFramework.PRISMA:
            return self._run_cmd(["npx", "prisma", "db", "seed"])

        elif framework == DatabaseFramework.SEQUELIZE:
            return self._run_cmd(["npx", "sequelize-cli", "db:seed:all"])

        elif framework == DatabaseFramework.RAILS:
            return self._run_cmd(["bin/rails", "db:seed"])

        else:
            print("❌ Seeding not auto-configured for this framework.", file=sys.stderr)
            return False

    def init(self) -> bool:
        # Check if docker-compose exists
        dc_path = self.project_dir / "docker-compose.yml"
        if dc_path.exists():
            print("ℹ️  docker-compose.yml already exists.")
            print("   Please manually add your database service if needed.")
            return True

        print("Creating basic docker-compose.yml with Postgres...")
        content = """version: '3.8'
services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: app_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
"""
        try:
            dc_path.write_text(content)
            print(f"✅ Created {dc_path}")
            return True
        except IOError as e:
            print(f"❌ Error writing file: {e}", file=sys.stderr)
            return False

    def inspect(self) -> bool:
        # For now, just print connection info or invoke framework tool
        framework = self.detect_framework()
        if framework == DatabaseFramework.PRISMA:
            return self._run_cmd(["npx", "prisma", "studio"])
        elif framework == DatabaseFramework.DJANGO:
            # Try to find python executable
            python = "python"
            if (self.project_dir / "venv").exists():
                 if sys.platform == "win32":
                    python = str(self.project_dir / "venv/Scripts/python.exe")
                 else:
                    python = str(self.project_dir / "venv/bin/python")
            return self._run_cmd([python, "manage.py", "inspectdb"])
        else:
            print("❌ Inspect not supported for this framework yet.", file=sys.stderr)
            return False
