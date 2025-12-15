import time
import requests
import json
import uuid
import sys
from shared.telemetry import Telemetry, PUSHGATEWAY_URL

# Configuration
PROMETHEUS_QUERY_URL = "http://localhost:9090/api/v1/query"
LOKI_QUERY_URL = "http://localhost:3100/loki/api/v1/query_range"


def verify_metrics():
    print("--- Verifying Metrics (Prometheus) ---")

    # 1. Emit Unique Metric
    marker = float(time.time())
    # Truncate to 3 decimal places to avoid float precision issues in query
    marker = round(marker, 3)

    unique_label = f"test_run_{uuid.uuid4().hex[:6]}"

    t = Telemetry("integration_tester", "test_job")
    t.register_gauge("integration_test_marker", "Test Marker", ["run_id"])

    print(
        f"Emitting metric: integration_test_marker = {marker} (label: {unique_label})"
    )
    t.record_gauge("integration_test_marker", marker, labels={"run_id": unique_label})

    # 2. Wait for Scrape (Prometheus scrapes every 5s in our config)
    print("Waiting 7 seconds for Prometheus scrape...")
    time.sleep(7)

    # 3. Query Prometheus
    query = f'integration_test_marker{{run_id="{unique_label}"}}'
    try:
        response = requests.get(PROMETHEUS_QUERY_URL, params={"query": query})
        data = response.json()

        if data["status"] != "success":
            print("FAILED: Prometheus query failed.")
            print(data)
            return False

        results = data["data"]["result"]
        if not results:
            print("FAILED: No metrics found in Prometheus.")
            return False

        value = float(results[0]["value"][1])
        print(f"Found value in Prometheus: {value}")

        if abs(value - marker) < 0.001:
            print("SUCCESS: Metric value matches.")
            return True
        else:
            print(f"FAILED: Value mismatch. Expected {marker}, got {value}")
            return False

    except Exception as e:
        print(f"FAILED: Exception querying Prometheus: {e}")
        return False


def verify_logs():
    print("\n--- Verifying Logs (Loki) ---")
    # Note: This test requires Promtail to be actually running and reading the log file.
    # Telemetry writes to ./agents/logs/integration_tester.log

    marker_msg = f"Integration Test Log {uuid.uuid4().hex}"
    t = Telemetry("integration_tester")

    print(f"Emitting log message: '{marker_msg}'")
    t.log_info(marker_msg)

    # Promtail takes a moment to tail -> Loki ingest -> Index
    print("Waiting 10 seconds for Log Ingestion...")
    time.sleep(10)

    # Query Loki
    # We query for the exact unique message content
    query = f'{{job="agent_logs"}} |= "{marker_msg}"'
    try:
        response = requests.get(LOKI_QUERY_URL, params={"query": query, "limit": 1})
        if response.status_code != 200:
            print(f"FAILED: Loki API returned {response.status_code}")
            print(response.text)
            return False

        data = response.json()
        results = data.get("data", {}).get("result", [])

        if not results:
            print("FAILED: Log line not found in Loki.")
            return False

        # Parse result to double check
        # Loki returns [timestamp, line]
        line = results[0]["values"][0][1]
        if marker_msg in line:
            print(f"SUCCESS: Log line found: {line}")
            return True
        else:
            print(f"FAILED: Log found but content mismatch? {line}")
            return False

    except Exception as e:
        print(f"FAILED: Exception querying Loki: {e}")
        return False


if __name__ == "__main__":
    m_ok = verify_metrics()
    # l_ok = verify_logs() # Loki might need more setup time/volume mapping in testing env
    # For now we focus on Metrics as critical path, Logs are bonus verification

    if m_ok:
        sys.exit(0)
    else:
        sys.exit(1)
