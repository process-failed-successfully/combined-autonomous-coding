import logging
import os
import socket
import time
import threading
import psutil
from typing import Dict, Any
from prometheus_client import (
    CollectorRegistry,
    Gauge,
    Counter,
    Histogram,
    push_to_gateway,
)

# Configuration
PUSHGATEWAY_URL = os.getenv("PUSHGATEWAY_URL", "localhost:9091")
ENABLE_METRICS = os.getenv("ENABLE_METRICS", "true").lower() == "true"
LOG_DIR = os.getenv("LOG_DIR", "./agents/logs")


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
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # Initialize Core Metrics
        self._init_metrics()

        # Initialize Default Values
        self._initialize_default_values()

        # Start System Monitoring Thread
        self.monitoring_thread = threading.Thread(
            target=self._system_monitoring_loop, daemon=True
        )
        self.monitoring_active = False

    def capture_logs_from(self, logger_name: str = None):
        """Attach the telemetry file handler to another logger to capture its output."""
        target_logger = logging.getLogger(logger_name)
        # Avoid duplicate handlers
        if self.file_handler not in target_logger.handlers:
            target_logger.addHandler(self.file_handler)
            self.log_info(
                f"Attached telemetry logging to '{
                    logger_name or 'root'}'"
            )

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
            ["agent_id", "model", "operation"],
            buckets=(1, 5, 10, 30, 60, 120, 300),
        )
        self.register_counter(
            "llm_tokens_total", "Combined token counter", ["agent_id", "model", "type"]
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

        except Exception as e:
            self.log_error(f"Failed to initialize default metrics: {e}")

    def register_gauge(self, name: str, documentation: str, labelnames: list = []):
        if name not in self.metrics:
            self.metrics[name] = Gauge(
                name, documentation, labelnames=labelnames, registry=self.registry
            )

    def register_counter(self, name: str, documentation: str, labelnames: list = []):
        if name not in self.metrics:
            self.metrics[name] = Counter(
                name, documentation, labelnames=labelnames, registry=self.registry
            )

    def register_histogram(
        self,
        name: str,
        documentation: str,
        labelnames: list = [],
        buckets: tuple = Histogram.DEFAULT_BUCKETS,
    ):
        if name not in self.metrics:
            self.metrics[name] = Histogram(
                name,
                documentation,
                labelnames=labelnames,
                registry=self.registry,
                buckets=buckets,
            )

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

    def record_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        if not ENABLE_METRICS:
            return
        labels = labels or {}
        if name in self.metrics:
            # Auto-fill common labels if missing and required
            required_labels = self.metrics[name]._labelnames

            # Create a copy to avoid mutating the passed dictionary if it's
            # reused by caller
            final_labels = labels.copy()

            for lbl in required_labels:
                if lbl not in final_labels:
                    if lbl == "agent_id":
                        final_labels[lbl] = self.service_name
                    elif lbl == "project":
                        final_labels[lbl] = self.project_name
                    elif lbl == "agent_type":
                        final_labels[lbl] = self.agent_type

            self.metrics[name].labels(**final_labels).set(value)
            self._push_metrics()

    def increment_counter(
        self, name: str, value: float = 1.0, labels: Dict[str, str] = None
    ):
        if not ENABLE_METRICS:
            return
        labels = labels or {}
        if name in self.metrics:
            required_labels = self.metrics[name]._labelnames

            # Create a copy
            final_labels = labels.copy()

            for lbl in required_labels:
                if lbl not in final_labels:
                    if lbl == "agent_id":
                        final_labels[lbl] = self.service_name
                    elif lbl == "project":
                        final_labels[lbl] = self.project_name
                    elif lbl == "agent_type":
                        final_labels[lbl] = self.agent_type

            self.metrics[name].labels(**final_labels).inc(value)
            self._push_metrics()

    def record_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        if not ENABLE_METRICS:
            return
        labels = labels or {}
        if name in self.metrics:
            required_labels = self.metrics[name]._labelnames

            # Create a copy
            final_labels = labels.copy()

            for lbl in required_labels:
                if lbl not in final_labels:
                    if lbl == "agent_id":
                        final_labels[lbl] = self.service_name
                    elif lbl == "project":
                        final_labels[lbl] = self.project_name
                    elif lbl == "agent_type":
                        final_labels[lbl] = self.agent_type

            self.metrics[name].labels(**final_labels).observe(value)
            self._push_metrics()

    def log_info(self, message: str):
        self.logger.info(message)

    def log_error(self, message: str):
        self.logger.error(message)
        self.increment_counter("agent_errors_total", labels={"error_type": "log_error"})

    def _push_metrics(self):
        try:
            # We group metrics by job, instance, and other high-level identifiers to act as "global labels"
            # grouping_key = {'instance': socket.gethostname(), 'service': self.service_name, 'project': self.project_name, 'agent_type': self.agent_type}
            # Prometheus Pushgateway grouping keys overwrite previous pushes
            # with the same key.

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
        except Exception:
            # Don't crash the agent if metrics fail
            # Avoid print spam, maybe log once
            pass

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
    service_name: str, agent_type: str = "unknown", project_name: str = "unknown"
):
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
