import logging
import os
import sys
from shared.telemetry import Telemetry

# Ensure we have a failing gateway URL
os.environ["PUSHGATEWAY_URL"] = "localhost:54321" # Random closed port

def test_telemetry_crash_on_shutdown():
    print("Initializing Telemetry...")
    t = Telemetry("test_crash_service")

    # Simulate logging shutdown which closes streams/handlers
    print("Simulating logging shutdown...")
    logging.shutdown()

    # Manually trigger the sync push which happens at atexit
    print("Triggering push_metrics_sync...")
    try:
        t._push_metrics_sync()
        print("SUCCESS: _push_metrics_sync completed without crashing.")
    except Exception as e:
        print(f"FAILURE: _push_metrics_sync crashed with: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_telemetry_crash_on_shutdown()
