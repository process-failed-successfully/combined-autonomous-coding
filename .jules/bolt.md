## 2026-01-06 - [Telemetry Bottleneck Fix]
**Learning:** The `Telemetry` class was pushing metrics to the Prometheus Pushgateway synchronously on *every single metric update*. This introduced significant latency (network RTT) for every file read, write, or tool execution.
**Action:** Implemented throttling in `_push_metrics` to only push once every 2 seconds, and added an `atexit` handler to ensure final metrics are flushed on shutdown. This drastically reduced the overhead of metric collection.

## 2026-01-06 - [Impact Analysis Optimization]
**Learning:** `ImpactAnalyzer` parses the AST of every Python file in the project to build a dependency graph. Using `ThreadPoolExecutor` for this task provided no speedup (likely due to GIL on `ast.parse` or overhead), but `ProcessPoolExecutor` reduced the graph build time by ~60% (from 1.2s to 0.5s for ~270 files).
**Action:** Implemented parallel AST parsing using `ProcessPoolExecutor` with a file count threshold to fallback to serial execution for small projects.
