import pytest
from pathlib import Path
from agents.config_manager import ConfigManager, KNOWN_MODELS

@pytest.fixture
def config_manager(tmp_path):
    # Patch ConfigManager to use tmp_path
    with pytest.MonkeyPatch.context() as m:
        m.setattr("agents.config_manager.get_config_path", lambda: tmp_path / "agent_config.yaml")
        m.setattr("platformdirs.user_config_dir", lambda x: str(tmp_path))
        yield ConfigManager()

def test_set_value_valid(config_manager, capsys):
    config_manager.set_value("max_iterations", "100")
    assert "Set 'max_iterations' to '100'" in capsys.readouterr().out
    
    loaded = config_manager._load_config()
    assert loaded["max_iterations"] == 100

def test_set_value_invalid_key(config_manager, capsys):
    config_manager.set_value("max_iters", "100")
    out = capsys.readouterr().out
    assert "Error: Unknown key 'max_iters'" in out
    assert "Did you mean 'max_iterations'?" in out

def test_set_value_invalid_type(config_manager, capsys):
    config_manager.set_value("max_iterations", "foo")
    assert "Error: Invalid value for max_iterations" in capsys.readouterr().out

def test_set_value_agent_type(config_manager, capsys):
    config_manager.set_value("agent_type", "gemini")
    assert "Set 'agent_type' to 'gemini'" in capsys.readouterr().out
    
    config_manager.set_value("agent_type", "invalid")
    assert "Error: Invalid agent_type 'invalid'" in capsys.readouterr().out

def test_set_value_model_validation(config_manager, capsys):
    # Valid model
    config_manager.set_value("model", "gemini-2.0-flash-exp")
    assert "Set 'model' to 'gemini-2.0-flash-exp'" in capsys.readouterr().out
    
    # Unknown model (Warning)
    config_manager.set_value("model", "unknown-model")
    out = capsys.readouterr().out
    assert "Warning: Model 'unknown-model' is not in the known list" in out
    
    # Fuzzy match hint
    config_manager.set_value("model", "gemini-2.0-flash")
    out = capsys.readouterr().out
    assert "Did you mean 'gemini-2.0-flash-exp'?" in out

def test_list_models(config_manager, capsys):
    config_manager.list_models()
    out = capsys.readouterr().out
    assert "gemini-2.0-flash-exp" in out
    assert "gpt-4o" in out
    
    config_manager.list_models("gemini")
    out = capsys.readouterr().out
    assert "gemini-2.0-flash-exp" in out
    assert "gpt-4o" not in out
