import os
import sys
import importlib
from pathlib import Path

def test_imports():
    root_dir = Path(__file__).parent.parent
    sys.path.append(str(root_dir))
    
    modules_to_test = [
        "shared.telemetry",
        "shared.agent_client",
        "shared.utils",
        "agents.cursor.agent",
        "agents.gemini.agent",
        "agents.cleaner.agent"
    ]
    
    print("Verifying imports...")
    for module_name in modules_to_test:
        try:
            importlib.import_module(module_name)
            print(f"✅ Successfully imported {module_name}")
        except Exception as e:
            print(f"❌ Failed to import {module_name}: {e}")
            sys.exit(1)
            
if __name__ == "__main__":
    test_imports()
