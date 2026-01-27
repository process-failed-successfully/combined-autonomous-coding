import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from pathlib import Path
from shared.cron_lab import CronLabManager

@pytest.fixture
def manager():
    return CronLabManager(Path("."))

def test_validate(manager):
    assert manager.validate("* * * * *")
    assert manager.validate("*/5 * * * *")
    assert not manager.validate("invalid")
    # croniter might accept 6 fields (seconds), so check standard 5
    assert manager.validate("0 0 1 1 *")

def test_get_next_runs(manager):
    runs = manager.get_next_runs("* * * * *", count=5)
    assert len(runs) == 5
    # Just check if strings look datetime-ish or exist
    assert all(isinstance(r, str) for r in runs)

    runs = manager.get_next_runs("invalid")
    assert runs == []

@pytest.mark.asyncio
async def test_explain_expression(manager):
    with patch("shared.cron_lab.run_ask_logic", new_callable=AsyncMock) as mock_ask:
        mock_ask.return_value = (True, "At every minute.")
        result = await manager.explain_expression("* * * * *")
        assert result == "At every minute."
        mock_ask.assert_called_once()

@pytest.mark.asyncio
async def test_generate_expression(manager):
    with patch("shared.cron_lab.run_ask_logic", new_callable=AsyncMock) as mock_ask:
        mock_ask.return_value = (True, "```\n*/5 * * * *\n```")
        result = await manager.generate_expression("Every 5 minutes")
        assert result == "```\n*/5 * * * *\n```"
        mock_ask.assert_called_once()
