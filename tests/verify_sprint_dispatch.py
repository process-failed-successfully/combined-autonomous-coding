import asyncio
from pathlib import Path
from shared.config import Config
from agents.shared.sprint import SprintManager
from agents.openrouter.client import OpenRouterClient
from agents.local.client import LocalClient
from agents.gemini.client import GeminiClient

async def test_sprint_manager_dispatch():
    project_dir = Path("./test_sprint_dispatch")
    project_dir.mkdir(exist_ok=True)
    
    # Test OpenRouter
    config_or = Config(project_dir=project_dir, agent_type="openrouter")
    manager_or = SprintManager(config_or)
    client_or, session_or = manager_or._get_agent_runner()
    print(f"Agent Type: openrouter -> Client: {type(client_or).__name__}")
    assert isinstance(client_or, OpenRouterClient)
    
    # Test Local
    config_local = Config(project_dir=project_dir, agent_type="local")
    manager_local = SprintManager(config_local)
    client_local, session_local = manager_local._get_agent_runner()
    print(f"Agent Type: local -> Client: {type(client_local).__name__}")
    assert isinstance(client_local, LocalClient)
    
    # Test Gemini (Default)
    config_gemini = Config(project_dir=project_dir, agent_type="gemini")
    manager_gemini = SprintManager(config_gemini)
    client_gemini, session_gemini = manager_gemini._get_agent_runner()
    print(f"Agent Type: gemini -> Client: {type(client_gemini).__name__}")
    assert isinstance(client_gemini, GeminiClient)
    
    print("SUCCESS: SprintManager dispatch verified.")
    
    # Cleanup
    import shutil
    shutil.rmtree(project_dir)

if __name__ == "__main__":
    asyncio.run(test_sprint_manager_dispatch())
