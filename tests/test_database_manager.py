import sys
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from shared.database_manager import DatabaseManager, DatabaseFramework

class TestDatabaseManager:
    @pytest.fixture
    def manager(self, tmp_path: Path) -> DatabaseManager:
        return DatabaseManager(tmp_path)

    def test_detect_django(self, manager: DatabaseManager, tmp_path: Path) -> None:
        (tmp_path / "manage.py").touch()
        assert manager.detect_framework() == DatabaseFramework.DJANGO

    def test_detect_alembic(self, manager: DatabaseManager, tmp_path: Path) -> None:
        (tmp_path / "alembic.ini").touch()
        assert manager.detect_framework() == DatabaseFramework.ALEMBIC

    def test_detect_prisma(self, manager: DatabaseManager, tmp_path: Path) -> None:
        package_json = tmp_path / "package.json"
        package_json.write_text('{"dependencies": {"prisma": "^4.0.0"}}')
        assert manager.detect_framework() == DatabaseFramework.PRISMA

    def test_detect_rails(self, manager: DatabaseManager, tmp_path: Path) -> None:
        (tmp_path / "bin").mkdir()
        (tmp_path / "bin/rails").touch()
        assert manager.detect_framework() == DatabaseFramework.RAILS

    def test_detect_unknown(self, manager: DatabaseManager) -> None:
        assert manager.detect_framework() == DatabaseFramework.UNKNOWN

    @patch("subprocess.run")
    def test_migrate_django(self, mock_run: MagicMock, manager: DatabaseManager, tmp_path: Path) -> None:
        (tmp_path / "manage.py").touch()
        manager.migrate()
        # Check command structure
        args = mock_run.call_args[0][0]
        assert "manage.py" in args
        assert "migrate" in args

    @patch("subprocess.run")
    def test_migrate_prisma(self, mock_run: MagicMock, manager: DatabaseManager, tmp_path: Path) -> None:
        package_json = tmp_path / "package.json"
        package_json.write_text('{"dependencies": {"prisma": "^4.0.0"}}')

        manager.migrate()
        mock_run.assert_called_with(["npx", "prisma", "migrate", "dev"], cwd=tmp_path, check=True)

    @patch("subprocess.run")
    def test_seed_sequelize(self, mock_run: MagicMock, manager: DatabaseManager, tmp_path: Path) -> None:
        package_json = tmp_path / "package.json"
        package_json.write_text('{"dependencies": {"sequelize": "^6.0.0"}}')

        manager.seed()
        mock_run.assert_called_with(["npx", "sequelize-cli", "db:seed:all"], cwd=tmp_path, check=True)

    def test_init_creates_docker_compose(self, manager: DatabaseManager, tmp_path: Path) -> None:
        dc_path = tmp_path / "docker-compose.yml"
        assert not dc_path.exists()

        manager.init()

        assert dc_path.exists()
        content = dc_path.read_text()
        assert "postgres:15-alpine" in content
        assert "POSTGRES_DB" in content

    def test_init_skips_existing(self, manager: DatabaseManager, tmp_path: Path) -> None:
        dc_path = tmp_path / "docker-compose.yml"
        dc_path.write_text("existing: true")

        manager.init()

        assert dc_path.read_text() == "existing: true"
