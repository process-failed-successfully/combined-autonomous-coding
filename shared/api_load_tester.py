import time
import concurrent.futures
import statistics
import requests
import json
from typing import Dict, Any, List


class APILoadTester:
    """
    Performs load testing on API endpoints.
    """
    def __init__(self, manager):
        self.manager = manager

    def run_load_test(self, method: str, url: str, users: int, duration: int, body: str = None) -> Dict[str, Any]:
        """
        Runs a load test against the specified endpoint.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Target URL
            users: Number of concurrent users (threads)
            duration: Duration of the test in seconds
            body: Request body (JSON string)

        Returns:
            Dictionary containing test metrics.
        """
        print(f"Starting load test: {method} {url} with {users} users for {duration}s...")

        start_time = time.time()
        end_time = start_time + duration

        # Parse body once
        json_body = None
        data_body = None
        if body:
            try:
                json_body = json.loads(body)
            except json.JSONDecodeError:
                data_body = body

        results: List[float] = []  # Latencies
        errors = 0
        total_requests = 0
        status_codes: Dict[int, int] = {}

        def worker():
            local_results = []
            local_errors = 0
            local_status_codes = {}

            while time.time() < end_time:
                req_start = time.time()
                try:
                    # Use the manager's session for connection pooling
                    resp = self.manager.session.request(
                        method=method,
                        url=url,
                        json=json_body,
                        data=data_body,
                        timeout=5  # Short timeout for load testing
                    )
                    latency = (time.time() - req_start) * 1000  # ms
                    local_results.append(latency)

                    code = resp.status_code
                    local_status_codes[code] = local_status_codes.get(code, 0) + 1

                    if code >= 500:  # Count server errors as errors for load test
                        local_errors += 1

                except requests.RequestException:
                    local_errors += 1

                # Small sleep to prevent tight loop burning CPU if requests are super fast?
                # Actually for load testing we want to go as fast as possible usually.
                # But let's assume we want to yield to other threads.
                # time.sleep(0.001)

            return local_results, local_errors, local_status_codes

        with concurrent.futures.ThreadPoolExecutor(max_workers=users) as executor:
            futures = [executor.submit(worker) for _ in range(users)]

            for future in concurrent.futures.as_completed(futures):
                r, e, s = future.result()
                results.extend(r)
                errors += e
                total_requests += len(r)
                for code, count in s.items():
                    status_codes[code] = status_codes.get(code, 0) + count

        total_duration = time.time() - start_time

        # Calculate metrics
        avg_latency = statistics.mean(results) if results else 0
        p50 = statistics.median(results) if results else 0
        p95 = statistics.quantiles(results, n=20)[18] if len(results) >= 20 else p50
        p99 = statistics.quantiles(results, n=100)[98] if len(results) >= 100 else p95

        rps = total_requests / total_duration if total_duration > 0 else 0

        return {
            "total_requests": total_requests,
            "duration": total_duration,
            "rps": rps,
            "avg_latency": avg_latency,
            "p50_latency": p50,
            "p95_latency": p95,
            "p99_latency": p99,
            "errors": errors,
            "status_codes": status_codes
        }
