## 2026-01-06 - [Telemetry Bottleneck Fix]
**Learning:** The `Telemetry` class was pushing metrics to the Prometheus Pushgateway synchronously on *every single metric update*. This introduced significant latency (network RTT) for every file read, write, or tool execution.
**Action:** Implemented throttling in `_push_metrics` to only push once every 2 seconds, and added an `atexit` handler to ensure final metrics are flushed on shutdown. This drastically reduced the overhead of metric collection.

## 2026-01-06 - [Impact Analysis Optimization]
**Learning:** `ImpactAnalyzer` parses the AST of every Python file in the project to build a dependency graph. Using `ThreadPoolExecutor` for this task provided no speedup (likely due to GIL on `ast.parse` or overhead), but `ProcessPoolExecutor` reduced the graph build time by ~60% (from 1.2s to 0.5s for ~270 files).
**Action:** Implemented parallel AST parsing using `ProcessPoolExecutor` with a file count threshold to fallback to serial execution for small projects.

## 2026-01-08 - [File System Polling Optimization]
**Learning:** `has_recent_activity` used `os.walk` and iterated `fnmatch.fnmatch` for every file against every ignore pattern. For large directory trees (5000+ files), this took ~0.05s per call, repeated every 5 seconds. Switching to `os.scandir` (recursive) and pre-compiling ignore patterns into a single regex reduced execution time by ~35-50% (to ~0.03s), minimizing I/O overhead during idle polling.
**Action:** Replaced `os.walk` with a recursive `os.scandir` implementation and utilized `re.compile` with `fnmatch.translate` for efficient pattern matching.

## 2026-01-09 - [Git Command Batching]
**Learning:** `TemporalCoupling.analyze` was spawning a subprocess for `git show` for every commit (up to 50 times). This high overhead (fork/exec) is avoidable.
**Action:** Batched all commit hashes into a single `git show` command. This reduces N subprocess calls to 1, significantly improving performance for history analysis.
