from shared.productivity_lab import ProductivityManager, ProductivitySession
from pathlib import Path
import time
import shutil

def test_productivity_manager():
    test_dir = Path("test_prod_lab")
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir()

    manager = ProductivityManager(test_dir)

    print("1. Start Session")
    manager.start_session("work", "task-123")
    print(f"Active: {manager.current_session is not None}")

    # Check if saved to disk as active (Current implementation: NO)
    manager2 = ProductivityManager(test_dir)
    print(f"New Manager Active: {manager2.current_session is not None}")
    # Expect False currently

    print("2. Stop Session")
    manager.stop_session()
    print(f"Active: {manager.current_session is not None}")

    manager3 = ProductivityManager(test_dir)
    print(f"Saved Sessions: {len(manager3.sessions)}")
    # Expect 1 currently

    if test_dir.exists():
        shutil.rmtree(test_dir)

if __name__ == "__main__":
    test_productivity_manager()
