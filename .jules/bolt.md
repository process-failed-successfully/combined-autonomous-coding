## 2026-01-06 - [Telemetry Bottleneck Fix]
**Learning:** The `Telemetry` class was pushing metrics to the Prometheus Pushgateway synchronously on *every single metric update*. This introduced significant latency (network RTT) for every file read, write, or tool execution.
**Action:** Implemented throttling in `_push_metrics` to only push once every 2 seconds, and added an `atexit` handler to ensure final metrics are flushed on shutdown. This drastically reduced the overhead of metric collection.
