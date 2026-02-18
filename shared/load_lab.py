import asyncio
import time
import sys
import statistics
from typing import Dict, Any, List, Optional

try:
    import aiohttp
except ImportError:
    aiohttp = None

class LoadLabManager:
    """
    Manages HTTP load testing with high concurrency using asyncio and aiohttp.
    """

    def __init__(self):
        if aiohttp is None:
            print("Error: aiohttp is required for load-lab. Please install it with 'pip install aiohttp'.", file=sys.stderr)
            sys.exit(1)

    async def _worker(self, session: "aiohttp.ClientSession", url: str, method: str,
                      headers: Optional[Dict[str, str]], body: Optional[str],
                      duration: int, results: List[Dict[str, Any]]):
        """
        Worker function to send requests for a specified duration.
        """
        end_time = time.time() + duration

        while time.time() < end_time:
            req_start = time.time()
            status = 0
            error = None
            try:
                async with session.request(method, url, headers=headers, data=body) as response:
                    status = response.status
                    await response.read() # Read body to complete request
            except Exception as e:
                error = str(e)

            req_end = time.time()
            latency = req_end - req_start

            results.append({
                "latency": latency,
                "status": status,
                "error": error,
                "timestamp": req_end
            })

    async def run_load_test(self, url: str, users: int = 1, duration: int = 10,
                           method: str = "GET", headers: Optional[Dict[str, str]] = None,
                           body: Optional[str] = None) -> Dict[str, Any]:
        """
        Runs the load test with specified parameters.
        """
        print(f"Starting load test on {url}")
        print(f"Users: {users}, Duration: {duration}s, Method: {method}")

        results: List[Dict[str, Any]] = []

        async with aiohttp.ClientSession() as session:
            tasks = []
            for _ in range(users):
                tasks.append(self._worker(session, url, method, headers, body, duration, results))

            start_time = time.time()
            await asyncio.gather(*tasks)
            total_duration = time.time() - start_time

        return self._calculate_stats(results, total_duration)

    def _calculate_stats(self, results: List[Dict[str, Any]], total_duration: float) -> Dict[str, Any]:
        """
        Calculates statistics from raw results.
        """
        if not results:
            return {
                "total_requests": 0,
                "rps": 0,
                "duration": total_duration,
                "success_count": 0,
                "error_count": 0,
                "latency": {}
            }

        latencies = [r["latency"] for r in results]
        status_codes: Dict[int, int] = {}
        error_count = 0
        success_count = 0

        for r in results:
            if r["error"]:
                error_count += 1
            else:
                success_count += 1
                code = r["status"]
                status_codes[code] = status_codes.get(code, 0) + 1

        stats = {
            "total_requests": len(results),
            "rps": len(results) / total_duration if total_duration > 0 else 0,
            "duration": total_duration,
            "success_count": success_count,
            "error_count": error_count,
            "status_codes": status_codes,
            "latency": {
                "min": min(latencies),
                "max": max(latencies),
                "avg": statistics.mean(latencies),
                "median": statistics.median(latencies),
                "p95": statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies),
                "p99": statistics.quantiles(latencies, n=100)[98] if len(latencies) >= 100 else max(latencies)
            }
        }
        return stats

async def run_load_lab_logic(args):
    """
    CLI Logic for Load Lab.
    """
    manager = LoadLabManager()

    # Parse headers if provided (format: "Key:Value,Key2:Value2")
    headers = {}
    if args.headers:
        for pair in args.headers.split(","):
            if ":" in pair:
                k, v = pair.split(":", 1)
                headers[k.strip()] = v.strip()

    result = await manager.run_load_test(
        url=args.url,
        users=args.users,
        duration=args.duration,
        method=args.method,
        headers=headers if headers else None,
        body=args.body
    )

    print("\n--- Load Test Results ---")
    print(f"Target:       {args.url}")
    print(f"Duration:     {result['duration']:.2f}s")
    print(f"Requests:     {result['total_requests']}")
    print(f"RPS:          {result['rps']:.2f}")
    print(f"Success:      {result['success_count']}")
    print(f"Errors:       {result['error_count']}")

    print("\n--- Latency (seconds) ---")
    l = result["latency"]
    if l:
        print(f"Min:    {l['min']:.4f}")
        print(f"Avg:    {l['avg']:.4f}")
        print(f"Median: {l['median']:.4f}")
        print(f"P95:    {l['p95']:.4f}")
        print(f"P99:    {l['p99']:.4f}")
        print(f"Max:    {l['max']:.4f}")

    if result["status_codes"]:
        print("\n--- Status Codes ---")
        for code, count in result["status_codes"].items():
            print(f"[{code}]: {count}")

    sys.exit(0 if result["error_count"] == 0 else 1)
