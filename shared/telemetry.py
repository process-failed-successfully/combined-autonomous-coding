import atexit
import logging
import os
import socket
import time
import threading
from concurrent.futures import ThreadPoolExecutor
import psutil
from typing import Dict, Any, Optional, List, Tuple
from prometheus_client import (
    CollectorRegistry,
    Gauge,
    Counter,
    Histogram,
    push_to_gateway,
)

# Configuration
PUSHGATEWAY_URL = os.getenv("PUSHGATEWAY_URL", "localhost:9081")
ENABLE_METRICS = os.getenv("ENABLE_METRICS", "true").lower() == "true"
LOG_DIR = os.getenv("LOG_DIR", "./agents/logs")


class SafeStreamHandler(logging.StreamHandler[Any]):
    """A StreamHandler that suppresses errors when writing to closed streams."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            super().emit(record)
        except (ValueError, OSError):
            # Stream might be closed
            pass


class Telemetry:
    _instance = None

    def __init__(
        self,
        service_name: str,
        job_name: str = "agent_job",
        agent_type: str = "unknown",
        project_name: str = "unknown",
    ):
        self.service_name = service_name
        self.job_name = job_name
        self.agent_type = agent_type
        self.project_name = project_name
        self.registry = CollectorRegistry()
        self.metrics: Dict[str, Any] = {}

        # Optimization: Cache default labels per metric to avoid re-calculation
        self._metric_defaults: Dict[str, Dict[str, str]] = {}
        self._system_labels = {
            "agent_id": service_name,
            "project": project_name,
            "agent_type": agent_type,
            "role": "unknown",
        }

        self._last_push_error_time = 0.0
        self._last_push_time = 0.0
        self._push_interval = 2.0  # Throttle pushes to every 2 seconds

        # Optimization: Use a ThreadPoolExecutor for non-blocking pushes
        # Max workers = 1 to serialize pushes and avoid overwhelming the gateway
        self._push_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="MetricsPusher")
        self.synchronous_mode = False  # Set to True for testing

        # Ensure log directory exists
        os.makedirs(LOG_DIR, exist_ok=True)

        # Setup Logger
        self.logger = logging.getLogger(service_name)
        self.logger.setLevel(logging.INFO)

        # File Handler
        log_file = os.path.join(LOG_DIR, f"{service_name}.log")
        self.file_handler = logging.FileHandler(log_file)
        formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "service": "%(name)s", "message": "%(message)s"}'
        )
        self.file_handler.setFormatter(formatter)
        self.logger.addHandler(self.file_handler)

        # Console Handler
        console_handler = SafeStreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # Prevent propagation to root logger (which might have broken handlers)
        self.logger.propagate = False

        # Initialize Core Metrics
        self._init_metrics()

        # Initialize Default Values
        self._initialize_default_values()

        # Start System Monitoring Thread
        self.monitoring_thread = threading.Thread(
            target=self._system_monitoring_loop, daemon=True
        )
        self.monitoring_active = False
        self._is_shutting_down = False

        # Ensure final metrics are pushed on exit
        atexit.register(self._shutdown)

    def _shutdown(self):
        """Shutdown handler to ensure pending metrics are pushed."""
        self._is_shutting_down = True
        self._push_metrics(force=True, sync=True, is_shutdown=True)
        self._push_executor.shutdown(wait=True)

    def capture_logs_from(self, logger_name: Optional[str] = None):
        """Attach the telemetry file handler to another logger to capture its output."""
        target_logger = logging.getLogger(logger_name)
        # Avoid duplicate handlers
        if self.file_handler not in target_logger.handlers:
            target_logger.addHandler(self.file_handler)
            self.log_info(f"Attached telemetry logging to '{logger_name or 'root'}'")

    def _init_metrics(self):
        # 1. Agent Health
        self.register_gauge(
            "agent_heartbeat_timestamp",
            "Unix timestamp of last heartbeat",
            ["agent_id", "project"],
        )
        self.register_gauge(
            "agent_online", "Binary (1=online, 0=offline)", ["agent_id", "project"]
        )
        self.register_gauge(
            "agent_uptime_seconds", "Time since agent started", ["agent_id", "project"]
        )
        self.register_counter(
            "agent_restart_total",
            "Number of restarts",
            ["agent_id", "project", "reason"],
        )

        # 2. Progress
        self.register_gauge(
            "feature_completion_pct",
            "Percentage of features passing",
            ["agent_id", "project"],
        )
        self.register_gauge(
            "features_passing", "Number of passing features", ["agent_id", "project"]
        )
        self.register_gauge(
            "features_total", "Total number of features", ["agent_id", "project"]
        )
        self.register_gauge(
            "agent_iteration", "Current iteration number", ["agent_id", "project"]
        )
        self.register_counter(
            "agent_iterations_total",
            "Total iterations completed",
            ["agent_id", "project"],
        )
        self.register_gauge(
            "iteration_duration_seconds",
            "Time taken for the last iteration",
            ["agent_id", "project"],
        )

        # 3. LLM Performance
        self.register_histogram(
            "llm_latency_seconds",
            "LLM response time",
            ["agent_id", "model", "operation", "role"],
            buckets=(1, 5, 10, 30, 60, 120, 300),
        )
        self.register_counter(
            "llm_tokens_total", "Combined token counter", ["agent_id", "model", "type", "role"]
        )
        self.register_counter(
            "llm_errors_total", "LLM API errors", ["agent_id", "model", "error_type"]
        )

        # 4. Tool Execution
        self.register_counter(
            "tool_execution_total", "Tool invocations", ["agent_id", "tool_type"]
        )
        self.register_histogram(
            "tool_execution_duration_seconds",
            "Tool execution time",
            ["agent_id", "tool_type"],
            buckets=(0.1, 0.5, 1, 5, 10, 30, 60),
        )
        self.register_counter(
            "tool_errors_total",
            "Tool failures",
            ["agent_id", "tool_type", "error_type"],
        )
        self.register_counter(
            "files_written_total", "Files created/modified", ["agent_id", "project"]
        )
        self.register_counter("files_read_total", "Files read", ["agent_id", "project"])
        self.register_counter(
            "bash_commands_total", "Bash executions", ["agent_id", "project", "status"]
        )

        # 5. Resource Usage
        self.register_gauge(
            "container_memory_usage_bytes",
            "Memory consumption",
            ["agent_id", "project"],
        )
        self.register_gauge(
            "container_cpu_usage_pct", "CPU usage percentage", ["agent_id"]
        )
        self.register_gauge("process_count", "Child processes spawned", ["agent_id"])

        # 6. Errors
        self.register_counter(
            "agent_errors_total", "All agent errors", ["agent_id", "error_type"]
        )
        self.register_counter(
            "agent_crashes_total", "Agent process crashes", ["agent_id"]
        )

        # 7. Sprint Metrics
        self.register_gauge(
            "sprint_tasks_total", "Total tasks in current sprint", ["project"]
        )
        self.register_counter(
            "sprint_tasks_completed_total", "Tasks completed in sprint", ["project"]
        )
        self.register_counter(
            "sprint_tasks_failed_total", "Tasks failed in sprint", ["project"]
        )
        self.register_gauge(
            "sprint_active_workers", "Currently running worker agents", ["project"]
        )
        self.register_histogram(
            "sprint_task_duration_seconds",
            "Time taken for sprint tasks",
            ["project", "status"],
            buckets=(10, 30, 60, 120, 300, 600, 1800),
        )
        self.register_gauge(
            "sprint_planning_duration_seconds",
            "Time taken for sprint planning",
            ["project", "status"],
        )

    @classmethod
    def get_instance(cls, service_name: str = "unknown_agent"):
        if cls._instance is None:
            cls._instance = Telemetry(service_name)
        return cls._instance

    def _initialize_default_values(self):
        """Initialize metrics to 0/default values so they appear in Grafana immediately."""
        try:
            # Gauges
            self.record_gauge("feature_completion_pct", 0)
            self.record_gauge("features_passing", 0)
            self.record_gauge("features_total", 0)
            self.record_gauge("agent_iteration", 0)
            self.record_gauge("agent_uptime_seconds", 0)
            self.record_gauge("agent_online", 1)

            # Counters (Initialize to 0)
            self.increment_counter("agent_iterations_total", 0)
            self.increment_counter("files_written_total", 0)
            self.increment_counter("files_read_total", 0)
            self.increment_counter("sprint_tasks_completed", 0)
            self.increment_counter("sprint_tasks_failed", 0)

            # Initialize Sprint Gauges
            self.record_gauge("sprint_tasks_total", 0)
            self.record_gauge("sprint_active_workers", 0)

        except Exception as e:
            self.log_error(f"Failed to initialize default metrics: {e}")

    def _cache_defaults(self, name: str, labelnames: List[str]):
        """Pre-calculate default labels for a metric to optimize lookups."""
        defaults = {}
        for lbl in labelnames:
            if lbl in self._system_labels:
                defaults[lbl] = self._system_labels[lbl]
        self._metric_defaults[name] = defaults

    def register_gauge(self, name: str, documentation: str, labelnames: List[str] = []):
        if name not in self.metrics:
            self.metrics[name] = Gauge(
                name, documentation, labelnames=labelnames, registry=self.registry
            )
            self._cache_defaults(name, labelnames)

    def register_counter(self, name: str, documentation: str, labelnames: List[str] = []):
        if name not in self.metrics:
            self.metrics[name] = Counter(
                name, documentation, labelnames=labelnames, registry=self.registry
            )
            self._cache_defaults(name, labelnames)

    def register_histogram(
        self,
        name: str,
        documentation: str,
        labelnames: List[str] = [],
        buckets: Tuple[float, ...] = Histogram.DEFAULT_BUCKETS,
    ):
        if name not in self.metrics:
            self.metrics[name] = Histogram(
                name,
                documentation,
                labelnames=labelnames,
                registry=self.registry,
                buckets=buckets,
            )
            self._cache_defaults(name, labelnames)

    def _get_labels(self, labels: Dict[str, str]) -> Dict[str, str]:
        # Merge default labels with provided labels
        final_labels = labels.copy() if labels else {}
        # Always inject agent_id and project if not provided (though we expect callers to provide specifics or we default)
        # However, checking the schema, most metrics use agent_id and project as labels.
        # We'll rely on the caller or default to instance variables.
        if (
            "agent_id" not in final_labels
            and "agent_id"
            in self.metrics[list(final_labels.keys())[0] if labels else ""]._labelnames
        ):
            final_labels["agent_id"] = self.service_name

        return final_labels

    def record_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        if not ENABLE_METRICS:
            return

        if name in self.metrics:
            if not labels:
                # Fast path: Use cached defaults directly
                # Note: This avoids dictionary copying and loops
                self.metrics[name].labels(**self._metric_defaults[name]).set(value)
            else:
                # Slow path: Merge provided labels with defaults
                final_labels = self._metric_defaults[name].copy()
                final_labels.update(labels)
                self.metrics[name].labels(**final_labels).set(value)

            self._push_metrics()

    def increment_counter(
        self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None
    ):
        if not ENABLE_METRICS:
            return

        if name in self.metrics:
            if not labels:
                # Fast path: Use cached defaults directly
                self.metrics[name].labels(**self._metric_defaults[name]).inc(value)
            else:
                # Slow path: Merge provided labels with defaults
                final_labels = self._metric_defaults[name].copy()
                final_labels.update(labels)
                self.metrics[name].labels(**final_labels).inc(value)

            self._push_metrics()

    def record_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        if not ENABLE_METRICS:
            return

        if name in self.metrics:
            if not labels:
                # Fast path: Use cached defaults directly
                self.metrics[name].labels(**self._metric_defaults[name]).observe(value)
            else:
                # Slow path: Merge provided labels with defaults
                final_labels = self._metric_defaults[name].copy()
                final_labels.update(labels)
                self.metrics[name].labels(**final_labels).observe(value)

            self._push_metrics()

    def log_info(self, message: str):
        self.logger.info(message)

    def log_error(self, message: str):
        self.logger.error(message)
        self.increment_counter("agent_errors_total", labels={"error_type": "log_error"})

    def _push_metrics_sync(self, suppress_logging: bool = False):
        """Synchronous version of push metrics for background thread or final flush."""
        try:
            grouping_key = {
                "instance": socket.gethostname(),
                "service": self.service_name,
                "agent_type": self.agent_type,
                "project": self.project_name,
            }

            push_to_gateway(
                PUSHGATEWAY_URL,
                job=self.job_name,
                registry=self.registry,
                grouping_key=grouping_key,
            )
        except Exception as e:
            # Don't crash the agent if metrics fail
            # Use throttled logging to avoid spamming
            now = time.time()
            if now - self._last_push_error_time > 60:  # Log once per minute
                # Check if we are shutting down globally
                if getattr(self, "_is_shutting_down", False):
                    suppress_logging = True

                if not suppress_logging:
                    # Check for closed streams (common in pytest environment)
                    # Check both local logger and root logger (due to propagation)
                    loggers_to_check = [self.logger, logging.getLogger()]
                    for logger in loggers_to_check:
                        for handler in logger.handlers:
                            if isinstance(handler, logging.StreamHandler) and hasattr(handler, "stream"):
                                if getattr(handler.stream, "closed", False):
                                    suppress_logging = True
                                    break
                        if suppress_logging:
                            break

                if not suppress_logging:
                    try:
                        self.logger.warning(f"Failed to push metrics to gateway: {e}")
                    except (ValueError, OSError):
                        # Logging system might be closed during shutdown
                        pass
                self._last_push_error_time = now

    def _push_metrics(self, force: bool = False, sync: bool = False, is_shutdown: bool = False):
        """
        Push metrics to the gateway.
        If sync=True, blocks until completion (used for shutdown).
        Otherwise, offloads to a thread pool to avoid blocking the main thread.
        """
        now = time.time()
        if not force and (now - self._last_push_time < self._push_interval):
            return

        # Update last push time immediately to prevent hammering
        self._last_push_time = now

        if sync or self.synchronous_mode:
            self._push_metrics_sync(suppress_logging=is_shutdown)
        else:
            # Offload to thread pool
            self._push_executor.submit(self._push_metrics_sync, suppress_logging=False)

    def start_system_monitoring(self, interval: int = 15):
        if self.monitoring_active:
            return
        self.monitoring_active = True
        self.monitoring_thread.start()

    def _system_monitoring_loop(self):
        while self.monitoring_active:
            try:
                process = psutil.Process(os.getpid())
                mem_info = process.memory_info()
                cpu_percent = process.cpu_percent(interval=None)  # Non-blocking

                self.record_gauge("container_memory_usage_bytes", mem_info.rss)
                self.record_gauge("container_cpu_usage_pct", cpu_percent)
                self.record_gauge(
                    "process_count", len(process.children(recursive=True)) + 1
                )  # Self + children

                # Heartbeat
                self.record_gauge("agent_heartbeat_timestamp", time.time())
                self.record_gauge("agent_online", 1)

            except Exception as e:
                self.log_error(f"System monitoring error: {e}")

            time.sleep(15)


# Global Helper
_telemetry = None


def init_telemetry(
    service_name: str,
    agent_type: str = "generic",
    project_name: str = "unknown",
    logger_name: Optional[str] = None,
) -> Telemetry:
    global _telemetry
    _telemetry = Telemetry(
        service_name, agent_type=agent_type, project_name=project_name
    )
    return _telemetry


def get_telemetry() -> Telemetry:
    global _telemetry
    if _telemetry is None:
        # Fallback
        _telemetry = Telemetry("default_agent")
    return _telemetry
