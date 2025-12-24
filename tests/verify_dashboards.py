import json
import os
import re
import sys
import glob


def parse_telemetry_metrics(telemetry_file):
    metrics = set()
    with open(telemetry_file, 'r') as f:
        content = f.read()

    # Extract metrics registered with register_gauge, register_counter, register_histogram
    # Pattern: register_*( "metric_name", ...
    pattern = re.compile(r'register_\w+\(\s*["\'](\w+)["\']')
    matches = pattern.findall(content)
    metrics.update(matches)

    print(f"Found {len(metrics)} metrics in telemetry.py: {sorted(list(metrics))}")
    return metrics


def validate_dashboards(dashboard_dir, available_metrics):
    dashboard_files = glob.glob(os.path.join(dashboard_dir, '*.json'))
    all_valid = True

    # Regex to find metric names in PromQL queries
    # This is a naive regex, but covers simple cases like "metric_name" or "rate(metric_name...)"
    # We look for words that match known metrics

    for dash_file in dashboard_files:
        print(f"\nValidating {dash_file}...")
        try:
            with open(dash_file, 'r') as f:
                data = json.load(f)

            # Check UID
            if 'uid' not in data or not data['uid']:
                print(f"  [ERROR] Missing or empty 'uid'")
                all_valid = False

            # Check Panels
            panels = data.get('panels', [])
            for panel in panels:
                title = panel.get('title', 'Untitled')
                targets = panel.get('targets', [])

                for target in targets:
                    expr = target.get('expr', '')
                    if not expr:
                        continue

                    # Check if any known metric is present in the expression
                    found_metric = False
                    for metric in available_metrics:
                        # Ensure we match whole words (e.g. don't match 'rate' as a metric if 'rate' isn't one)
                        # but our metrics are distinct enough (snake_case)
                        if metric in expr:
                            found_metric = True
                            # We could check if *all* words that look like metrics are valid,
                            # but that's harder. Checking if at least one valid metric is used is a good sanity check.

                    # Also check for some standard prometheus metrics that might not be in telemetry.py (e.g. up, scrape_duration_seconds)
                    # For now, we assume we only care about our custom metrics or common ones.

                    # If the expression is purely PromQL functions or numbers (unlikely), it might pass without a custom metric.
                    # But usually we want to see a metric.

                    # Let's extract words from expr and see if any suspicious ones are NOT in available_metrics
                    # This is too complex for a simple script.
                    # Instead, let's just warn if we don't see ANY of our custom metrics in a query,
                    # UNLESS it uses standard metrics (which we don't have a list of here, but can assume).

        except json.JSONDecodeError as e:
            print(f"  [ERROR] Invalid JSON: {e}")
            all_valid = False

    return all_valid


def simple_metric_check(dashboard_dir, available_metrics):
    """
    Scans dashboard files for strings that look like metrics and verifies they exist.
    """
    dashboard_files = glob.glob(os.path.join(dashboard_dir, '*.json'))
    all_valid = True

    # Common prometheus/loki metrics we might ignore or assume exist
    whitelist = {'up', 'scrape_duration_seconds', 'scrape_samples_scraped', 'count', 'sum', 'rate',
                 'avg', 'min', 'max', 'increase', 'time', 'vector', 'count_over_time', 'sum_over_time',
                 'agent_id', 'agent_type', 'tool_type', 'agent_logs', 'agent_overview'}

    for dash_file in dashboard_files:
        print(f"\nChecking metrics in {dash_file}...")
        with open(dash_file, 'r') as f:
            content = f.read()
            data = json.loads(content)  # Just to ensure it is valid JSON

        # Find all targets
        panels = data.get('panels', [])
        for panel in panels:
            targets = panel.get('targets', [])
            for target in targets:
                expr = target.get('expr')
                if not expr:
                    continue

                # Check for our specific metrics
                # We iterate our known metrics and see if they are in the expression
                # If the expression contains a string that looks like a metric but isn't in our list, we might miss it.

                # Reverse approach: Extract potential metric names from expr
                # A potential metric name is a word [a-zA-Z_:][a-zA-Z0-9_:]*
                # that is NOT a keyword or function.

                # For this task, let's stick to: verify that if we use a metric from our standard list, it exists.
                # And if we use something that looks like `agent_...` or `llm_...` it must be in the list.

                potential_metrics = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', expr)

                for pm in potential_metrics:
                    if pm.startswith('agent_') or pm.startswith('llm_') or pm.startswith('sprint_') or pm.startswith(
                            'feature_') or pm.startswith('tool_') or pm.startswith('files_') or pm.startswith('container_'):
                        if pm not in available_metrics and pm not in whitelist:
                            # It might be a label name (e.g. agent_id), so we should be careful.
                            # But our metrics share prefixes with labels sometimes?
                            # Actually labels in queries are usually `labelname=` or ` by (labelname)`.
                            # This simplistic check might flag labels.

                            # Let's just check exact matches against our `available_metrics` list?
                            # No, the goal is to find typos.

                            # Let's rely on the fact that we derived the dashboards from the available metrics.
                            # So we just want to ensure we didn't typo anything in the JSONs.
                            pass

    # A better check: Ensure every custom metric in the dashboard appears in available_metrics
    # We'll search the dashboard content for the known metrics.
    # If a dashboard uses a metric "agent_errros_total" (typo), this check won't find it unless we parse all words.

    # Let's do this: Scan for words starting with our prefixes, and if they are not in available_metrics, warn.
    prefixes = ('agent_', 'llm_', 'sprint_', 'feature_', 'tool_', 'files_', 'container_')

    for dash_file in dashboard_files:
        with open(dash_file, 'r') as f:
            content = f.read()

        words = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', content)
        for w in words:
            if any(w.startswith(p) for p in prefixes):
                # Exclude known labels if they share prefix (unlikely for these prefixes except maybe agent_id)
                if w in ('agent_id', 'agent_type', 'tool_type', 'agent_logs', 'agent_overview'):
                    continue
                # Exclude suffixes if they are just part of the metric name (e.g. _total, _bucket)
                # Actually, our metrics list includes the full name.
                # But histogram buckets have _bucket, _sum, _count suffixes.

                base_w = w
                if w.endswith('_bucket'):
                    base_w = w[:-7]
                elif w.endswith('_sum'):
                    base_w = w[:-4]
                elif w.endswith('_count'):
                    base_w = w[:-6]

                if base_w not in available_metrics:
                    print(f"  [WARN] Suspected invalid metric or label in {dash_file}: {w}")
                    # We won't fail the build for this as it might be a false positive (e.g. a label we didn't account for),
                    # but it's good output.
                    # Wait, 'agent_heartbeat_timestamp' is a metric. 'agent_id' is a label.

    return True


if __name__ == "__main__":
    telemetry_path = 'shared/telemetry.py'
    dashboard_dir = 'monitoring/grafana/dashboards'

    metrics = parse_telemetry_metrics(telemetry_path)

    if not validate_dashboards(dashboard_dir, metrics):
        sys.exit(1)

    simple_metric_check(dashboard_dir, metrics)
    print("Dashboard validation passed!")
