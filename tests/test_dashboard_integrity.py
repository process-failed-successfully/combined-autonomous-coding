import json
import os
import time
import requests
import glob
from shared.telemetry import Telemetry

# Configuration from environment or defaults
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://localhost:9080")
GRAFANA_URL = os.getenv("GRAFANA_URL", "http://localhost:3000")
PUSHGATEWAY_URL = os.getenv("PUSHGATEWAY_URL", "localhost:9081")

TEST_AGENT_ID = "dashboard_integrity_tester"
TEST_PROJECT = "integrity_check_project"


def emit_test_metrics():
    """Generates a comprehensive set of metrics to populate dashboards."""
    print(f"--- Emitting Test Metrics (Agent: {TEST_AGENT_ID}) ---")

    t = Telemetry(TEST_AGENT_ID, agent_type="tester", project_name=TEST_PROJECT)

    # 1. Agent Health
    t.record_gauge("agent_heartbeat_timestamp", time.time())
    t.record_gauge("agent_online", 1)
    t.record_gauge("agent_uptime_seconds", 3600)  # Simulating 1 hour uptime
    t.increment_counter("agent_restart_total", 0, labels={"reason": "test"})

    # 2. Progress
    t.record_gauge("feature_completion_pct", 75.5)
    t.record_gauge("features_passing", 15)
    t.record_gauge("features_total", 20)
    t.record_gauge("agent_iteration", 5)
    t.increment_counter("agent_iterations_total", 42)
    t.record_gauge("iteration_duration_seconds", 120.5)

    # 3. LLM Performance
    t.record_histogram("llm_latency_seconds", 5.2, labels={"model": "gpt-4", "operation": "chat", "role": "developer"})
    t.increment_counter("llm_tokens_total", 1500, labels={"model": "gpt-4", "type": "prompt", "role": "developer"})
    t.increment_counter("llm_tokens_total", 2500, labels={"model": "gpt-4", "type": "completion", "role": "developer"})
    t.increment_counter("llm_errors_total", 0, labels={"model": "gpt-4", "error_type": "none"})

    # 4. Tool Execution
    t.increment_counter("tool_execution_total", 10, labels={"tool_type": "bash"})
    t.record_histogram("tool_execution_duration_seconds", 0.5, labels={"tool_type": "bash"})
    t.increment_counter("tool_errors_total", 1, labels={"tool_type": "bash", "error_type": "exit_code_1"})
    t.increment_counter("files_written_total", 5)
    t.increment_counter("files_read_total", 12)
    t.increment_counter("bash_commands_total", 8, labels={"status": "success"})
    t.increment_counter("agent_errors_total", 0, labels={"error_type": "none"})

    # 5. Resource Usage
    t.record_gauge("container_memory_usage_bytes", 256 * 1024 * 1024)
    t.record_gauge("container_cpu_usage_pct", 12.5)
    t.record_gauge("process_count", 4)

    # 6. Sprint Metrics
    t.record_gauge("sprint_tasks_total", 10, labels={"project": TEST_PROJECT})
    t.increment_counter("sprint_tasks_completed_total", 7, labels={"project": TEST_PROJECT})
    t.increment_counter("sprint_tasks_failed_total", 1, labels={"project": TEST_PROJECT})
    t.record_gauge("sprint_active_workers", 2, labels={"project": TEST_PROJECT})
    t.record_histogram("sprint_task_duration_seconds", 600, labels={"project": TEST_PROJECT, "status": "done"})

    print("Metrics pushed to Pushgateway.")


def get_dashboard_queries():
    """Scans dashboard directory and extracts all PromQL queries."""
    dashboards = glob.glob("monitoring/grafana/dashboards/*.json")
    queries = []

    for dash_path in dashboards:
        with open(dash_path, 'r') as f:
            data = json.load(f)
            title = data.get('title', 'Unknown Dashboard')
            panels = data.get('panels', [])

            for panel in panels:
                panel_title = panel.get('title', 'Untitled')
                targets = panel.get('targets', [])
                for target in targets:
                    expr = target.get('expr')
                    if expr and target.get('datasource', {}).get('type') != 'loki':
                        queries.append({
                            'dashboard': title,
                            'panel': panel_title,
                            'expr': expr
                        })
    return queries


def validate_queries(queries):
    """Executes each query and fails if no data is found."""
    print(f"\n--- Validating {len(queries)} Queries across Dashboards ---")

    all_ok = True
    for q in queries:
        expr = q['expr']
        # Replace template variables
        expr = expr.replace('$agent_id', TEST_AGENT_ID)
        expr = expr.replace('$project', TEST_PROJECT)

        # Loki check - skip for now as it's separate
        if '{job="agent_logs"}' in expr:
            print(f"Skipping Loki query: {expr}")
            continue

        print(f"Checking Dashboard: {q['dashboard']} | Panel: {q['panel']}")
        print(f"  Query: {expr}")

        try:
            response = requests.get(f"{PROMETHEUS_URL}/api/v1/query", params={'query': expr})
            data = response.json()

            if data['status'] != 'success':
                print(f"  [FAIL] Query failed: {data.get('error')}")
                all_ok = False
                continue

            results = data['data']['result']
            if not results:
                # Some queries might naturally be empty (e.g. error rate if 0),
                # but for this test we want to see SOMETHING to prove the plumbing works.
                # However, sum(sprint_tasks_failed) might be 0.
                # We'll check if the value is explicitly present.
                print("  [FAIL] No data returned for query.")
                all_ok = False
            else:
                # Check if value is non-null
                val = results[0]['value'][1]
                print(f"  [SUCCESS] Found value: {val}")

        except Exception as e:
            print(f"  [ERROR] Exception during query: {e}")
            all_ok = False

    return all_ok


if __name__ == "__main__":
    emit_test_metrics()

    print("\nWaiting 10 seconds for Prometheus scrape...")
    time.sleep(10)

    queries = get_dashboard_queries()
    if not queries:
        print("No queries found in dashboards!")
        os._exit(1)

    if validate_queries(queries):
        print("\n\033[0;32mALL DASHBOARD QUERIES VALIDATED SUCCESSFULLY!\033[0m")
        os._exit(0)
    else:
        print("\n\033[0;31mDASHBOARD VALIDATION FAILED!\033[0m")
        os._exit(1)
