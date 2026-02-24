#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK
"""
Combined Autonomous Coding Agent
================================

Main entry point for running autonomous coding agents (Gemini or Cursor).
"""

import argparse
import asyncio
try:
    import argcomplete
except ImportError:
    argcomplete = None
import sys
import os
import shutil
import subprocess
from pathlib import Path
import time
from collections import deque
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    Observer = None
    FileSystemEventHandler = None


from shared.config import Config
from shared.logger import setup_logger
from shared.git import ensure_git_safe
from shared.config_loader import load_config_from_file, ensure_config_exists
from shared.hooks import install_hooks

# Import agent runners
# We import these lazily or handled via dispatch to avoid circular deps if any,
# though structure should be clean.
try:
    from shared.jira_client import JiraClient
except ImportError:
    JiraClient = None
from shared.issues import _run_issues_logic
from shared.ai_git import generate_commit_message_logic
from agents.gemini import run_autonomous_agent as run_gemini, GeminiAgent
from agents.shared.sprint import run_sprint as run_sprint
from agents.cursor import run_autonomous_agent as run_cursor, CursorAgent
from agents.local import run_autonomous_agent as run_local, LocalAgent
from agents.openrouter import run_autonomous_agent as run_openrouter, OpenRouterAgent
from shared.shell import InteractiveShell
from shared.commands import run_why
from shared.cost import CostCalculator
from shared.onboarding import run_onboard_logic
from shared.ask import run_ask_logic
from shared.cli import run_do_logic
from shared.playground import PlaygroundManager
from shared.debug import run_debug_logic
from shared.mutate import run_mutate
from shared.code_review import run_code_review_logic
from shared.summarize import run_summarize_logic
from shared.explain import run_explain_logic
from shared.worktree import WorktreeManager
from shared.security import SecurityAuditor
from shared.dockerizer import Dockerizer
from shared.verify import run_verify_logic
from shared.polish import run_polish_logic
from shared.troubleshoot import run_troubleshoot_logic
from shared.health import run_health_check
from shared.sentinel import Sentinel
from shared.work_session import WorkSessionManager
from shared.i18n import run_i18n_logic
from shared.api_lab import run_api_lab_cli
from shared.data_lab import run_data_lab_logic
from shared.schema_lab import run_schema_lab_logic
from shared.cidr_lab import run_cidr_lab_logic
from shared.time_lab import run_time_lab_logic
from shared.sys_lab import run_sys_lab_logic
from shared.log_lab import run_log_lab_logic
from shared.sql_lab import run_sql_lab_logic
from shared.json_lab import run_json_lab_logic
from shared.yaml_lab import run_yaml_lab_logic
from shared.toml_lab import run_toml_lab_logic
from shared.csv_lab import run_csv_lab_logic
from shared.excel_lab import run_excel_lab_logic
from shared.template_lab import run_template_lab_logic
from shared.unit_lab import run_unit_lab_logic
from shared.research import run_research_logic
from shared.serve import ServeManager
from shared.network import run_network_logic
from shared.scheduler import Scheduler
from shared.chaos import run_chaos_logic
from shared.cli_gantt import run_gantt_logic
from shared.retro import run_retro_logic
from shared.impact import ImpactAnalyzer
from shared.smart_context import run_smart_context
from shared.badges import run_badges_logic
from shared.plugin_manager import PluginManager
from shared.crypto_lab import run_crypto_lab_logic
from shared.image_lab import run_image_lab_logic
from shared.media_lab import run_media_lab_logic
from shared.markdown_lab import run_markdown_lab_logic
from shared.net_lab import run_net_lab_logic
from shared.pdf_lab import run_pdf_lab_logic
from shared.archive_lab import run_archive_lab_logic
from shared.uni_lab import run_uni_lab_logic
from shared.docs_generator import run_docs_lab_logic
from shared.qr_lab import run_qr_lab_logic
from shared.http_lab import run_http_lab_logic
from shared.proxy_lab import run_proxy_lab_logic
from shared.proc_lab import run_proc_lab_logic
from shared.geo_lab import run_geo_lab_logic
from shared.struct_lab import run_struct_lab_logic
from shared.chart_lab import run_chart_lab_logic
from shared.enc_lab import run_enc_lab_logic
from shared.rss_lab import run_rss_lab_logic
from shared.fs_lab import run_fs_lab_logic
from shared.ws_lab import run_ws_lab_logic
from shared.webhook_lab import run_webhook_lab_logic
from shared.hash_lab import run_hash_lab_logic
from shared.random_lab import run_random_lab_logic
from shared.browser_lab import run_browser_lab_logic
from shared.npm_lab import run_npm_lab_logic
from shared.pypi_lab import run_pypi_lab_logic
from shared.docker_lab import run_docker_lab_logic
from shared.compose_lab import run_compose_lab_logic
from shared.k8s_lab import run_k8s_lab_logic
from shared.diff_lab import run_diff_lab_logic
from shared.redis_lab import run_redis_lab_logic
from shared.kafka_lab import run_kafka_lab_logic
from shared.github_lab import run_github_lab_logic
from shared.email_lab import run_email_lab_logic
from shared.sock_lab import run_sock_lab_logic
from shared.ssh_lab import run_ssh_lab_logic
from shared.tmux_lab import run_tmux_lab_logic
from shared.terraform_lab import run_terraform_lab_logic
from shared.dns_lab import run_dns_lab_logic
from shared.whois_lab import run_whois_lab_logic
from shared.s3_lab import run_s3_lab_logic
from shared.graphql_lab import run_graphql_lab_logic
from shared.helm_lab import run_helm_lab_logic
from shared.notebook_lab import run_notebook_lab_logic
from shared.grpc_lab import run_grpc_lab_logic
from shared.monitor_lab import run_monitor_lab_logic
from shared.trace_lab import run_trace_lab_logic
from shared.fuzz_lab import run_fuzz_lab_logic
from shared.metrics_lab import run_metrics_lab_logic
from shared.static_lab import run_static_lab_logic
from shared.notify_lab import run_notify_lab_logic
from shared.contract_lab import run_contract_lab_logic
from shared.ansible_lab import run_ansible_lab_logic
from shared.hex_lab import run_hex_lab_logic
from shared.speed_lab import run_speed_lab_logic
from shared.load_lab import run_load_lab_logic
from shared.ast_lab import run_ast_lab_logic
from shared.systemd_lab import run_systemd_lab_logic
from shared.http_server_lab import run_http_server_lab_logic
from shared.productivity_lab import run_productivity_lab_logic
from shared.rename_lab import run_rename_lab_logic
from shared.dict_lab import run_dict_lab_logic
from shared.emoji_lab import run_emoji_lab_logic
import json
import yaml
import platformdirs
from dataclasses import asdict, is_dataclass
from datetime import datetime

# Agent Definitions
AVAILABLE_AGENTS = {
    "gemini": "Uses Google's Gemini model via the official API.",
    "cursor": "Interacts with the Cursor IDE's AI features.",
    "local": "Runs a local model (e.g., Ollama).",
    "openrouter": "Uses a model from the OpenRouter API.",
}

# Known CLI commands for recipe execution
KNOWN_COMMANDS = [
    "shell", "tui", "quiz", "kata", "prompt-lab", "knowledge", "chat", "ask", "do",
    "optimize", "perf", "debug", "code-review", "summarize", "explain", "init", "adr",
    "onboard", "session", "secrets", "db", "database", "playground", "completion",
    "plan", "estimate", "config", "configure", "validate", "doctor", "clean", "prune",
    "archive", "empty-trash", "restore", "trash", "revert", "rewind", "discard", "undo",
    "archives", "artifacts", "worktrees", "snapshot", "list-agents", "models", "glance",
    "status", "dashboard", "summary", "suggest", "tour", "history", "last", "last-run-id",
    "diff-summary", "diff", "log", "logs", "workflow", "cost", "benchmark", "sprint",
    "branch", "mutate", "test", "lint", "format", "hooks", "replay", "recipes", "macro",
    "git", "history-graph", "tree", "report", "push", "pull", "patch", "issues", "pr",
    "commit", "feature", "interact", "profile", "watch", "why", "blame", "stash", "next",
    "context", "search", "smart-search", "ssearch", "replace", "todos", "review", "env",
    "setup", "scaffold", "dockerize", "cicd", "verify", "troubleshoot", "sentinel", "health",
    "debt", "check-links", "security", "help", "cherry-pick", "rollback", "timeline",
    "analytics", "deps", "duplication", "unused", "risk", "impact", "a11y", "license",
    "bisect", "map", "architecture", "arch", "release", "openapi", "docstring", "refactor",
    "polish", "resolve", "regex", "cron-lab", "resolve-conflicts", "fix-conflicts",
    "generate-tests", "gentest", "dataset", "snippets", "mock", "frontend", "i18n",
    "api-lab", "data-lab", "research", "serve", "scheduler", "chaos", "guardrails", "devtools",
    "standup", "presentation", "visualize", "network", "sanitize", "ide", "logic-lab",
    "gantt", "resume", "retro", "kanban", "smart-context", "port", "color-lab", "schema-lab",
    "cidr-lab", "cidr", "cq", "code-query", "badges", "jwt-lab", "uuid-lab", "uuid", "password-lab", "pwd-lab",
    "text-lab", "txt", "cert-lab", "cert", "url-lab", "url", "time-lab", "time", "unit-lab", "unit",
    "math-lab", "math", "calc-lab", "calc", "semver-lab", "semver", "sys-lab", "sys", "log-lab", "ll", "sql-lab", "sql", "html-lab", "html",
    "crypto-lab", "crypto", "json-lab", "json", "csv-lab", "csv", "excel-lab", "xls", "xlsx", "excel", "template-lab", "tpl", "image-lab", "img", "media-lab", "media", "xml-lab", "xml",
    "markdown-lab", "md", "md-lab", "yaml-lab", "yaml", "toml-lab", "toml", "net-lab", "net", "archive-lab", "arc",
    "pdf-lab", "pdf", "uni-lab", "uni", "docs-lab", "docs", "qr-lab", "qr", "http-lab", "http", "req",
    "proxy-lab", "proxy",
    "proc-lab", "proc", "geo-lab", "geo", "struct-lab", "struct", "bin", "chart-lab", "chart",
    "enc-lab", "enc", "encode", "rss-lab", "rss", "fs-lab", "fs", "files",
    "ws-lab", "ws", "webhook-lab", "webhook", "hook", "hash-lab", "hash", "random-lab", "rand", "random",
    "browser-lab", "browser", "web",
    "npm-lab", "npm",
    "pypi-lab", "pypi",
    "docker-lab", "docker", "container",
    "compose-lab", "compose",
    "k8s-lab", "k8s", "kube",
    "diff-lab",
    "redis-lab", "redis", "cache",
    "kafka-lab", "kafka",
    "github-lab", "github", "gh",
    "email-lab", "email", "mail", "smtp",
    "sock-lab", "sock", "nc", "netcat",
    "ssh-lab", "ssh",
    "tmux-lab", "tmux",
    "terraform-lab", "tf", "terraform",
    "dns-lab", "dns",
    "whois-lab", "whois",
    "s3-lab", "s3",
    "graphql-lab", "gql",
    "helm-lab", "helm",
    "notebook-lab", "nb",
    "grpc-lab", "grpc",
    "monitor-lab", "monitor", "mon",
    "metrics-lab", "metrics",
    "trace-lab", "trace",
    "fuzz-lab", "fuzz",
    "static-lab", "static", "serve-static",
    "notify-lab", "notify",
    "contract-lab", "contract",
    "ansible-lab", "ansible",
    "hex-lab", "hex",
    "speed-lab", "speed",
    "load-lab", "load",
    "ast-lab", "ast",
    "otp-lab", "otp", "totp", "mfa",
    "calendar-lab", "calendar", "cal",
    "cheatsheet-lab", "cheatsheet", "cheat",
    "finance-lab", "finance", "fin",
    "runner-lab", "runner",
    "gitignore-lab", "gitignore", "gi",
    "permissions-lab", "perm", "chmod",
    "ollama-lab", "ollama", "ol",
    "mqtt-lab", "mqtt", "mq",
    "path-lab", "path",
    "systemd-lab", "systemd", "service",
    "http-server-lab", "httpd", "server",
    "ascii-lab", "ascii",
    "pattern-lab", "pattern", "design",
    "weather-lab", "weather", "w",
    "bandwidth-lab", "bandwidth", "bw",
    "typing-lab", "type",
    "sound-lab", "sound", "audio",
    "maze-lab", "maze",
    "license-lab", "lic", "license",
    "rfc-lab", "rfc",
    "productivity-lab", "prod", "focus",
    "rename-lab", "rename",
    "diagram-lab", "diagram", "draw",
    "pipe-lab", "pipe", "stream",
    "dict-lab", "dict", "define", "synonym", "antonym", "thesaurus",
    "find-lab", "find", "locate",
    "emoji-lab", "emoji", "emoj"
]

if FileSystemEventHandler:
    class CommandEventHandler(FileSystemEventHandler):
        def __init__(self, command, project_dir):
            self.command = command
            self.project_dir = project_dir

        def on_modified(self, event):
            if event.is_directory:
                return
            print(f"File modified: {event.src_path}. Running command: {' '.join(self.command)}")
            subprocess.run(self.command, cwd=self.project_dir)

def run_calc_lab(args):
    """Runs the Calc Lab (Programmer's Calculator)."""
    from shared.calc_lab import run_calc_lab_logic
    run_calc_lab_logic(args)
    sys.exit(0)

def run_rename_lab(args):
    """Runs the Rename Lab."""
    run_rename_lab_logic(args)
    sys.exit(0)

def run_find_lab(args):
    """Runs the Find Lab."""
    from shared.find_lab import run_find_lab_logic
    run_find_lab_logic(args)
    sys.exit(0)

def run_dict_lab(args):
    """Runs the Dictionary Lab."""
    run_dict_lab_logic(args)
    sys.exit(0)

def run_emoji_lab(args):
    """Runs the Emoji Lab."""
    run_emoji_lab_logic(args)
    sys.exit(0)

def run_diagram_lab(args):
    """Runs the Diagram Lab."""
    if args.action == "tui":
        from shared.tui import AgentTUI
        print("Launching Diagram Lab TUI...")
        app = AgentTUI(project_dir=args.project_dir, start_tab="tab-diagram")
        app.run()
        sys.exit(0)

    from shared.diagram_lab import run_diagram_lab_logic
    run_diagram_lab_logic(args)
    sys.exit(0)

def run_pipeline_lab(args):
    """Runs the Pipeline Lab."""
    from shared.pipeline_lab import run_pipeline_lab_logic
    run_pipeline_lab_logic(args)
    sys.exit(0)

def run_bandwidth_lab(args):
    """Runs the Bandwidth Lab."""
    from shared.bandwidth_lab import run_bandwidth_lab_logic
    run_bandwidth_lab_logic(args)
    sys.exit(0)

def run_typing_lab(args):
    """Runs the Typing Lab."""
    from shared.tui import AgentTUI
    print("Launching Typing Lab...")
    app = AgentTUI(project_dir=args.project_dir, start_tab="tab-typing")
    app.run()
    sys.exit(0)

def run_sound_lab(args):
    """Runs the Sound Lab."""
    if args.action == "tui":
        from shared.tui import AgentTUI
        print("Launching Sound Lab TUI...")
        app = AgentTUI(project_dir=args.project_dir, start_tab="tab-sound")
        app.run()
        sys.exit(0)

    from shared.sound_lab import run_sound_lab_logic
    run_sound_lab_logic(args)
    sys.exit(0)

def run_maze_lab(args):
    """Runs the Maze Lab."""
    from shared.maze_lab import run_maze_lab_logic
    run_maze_lab_logic(args)
    sys.exit(0)

def run_license_lab(args):
    """Runs the License Lab."""
    from shared.license_lab import run_license_lab_logic
    success = run_license_lab_logic(args)
    sys.exit(0 if success else 1)

def run_rfc_lab(args):
    """Runs the RFC Lab."""
    from shared.rfc_lab import run_rfc_lab_logic
    run_rfc_lab_logic(args)
    sys.exit(0)

def run_weather_lab(args):
    """Runs the Weather Lab."""
    from shared.weather_lab import run_weather_lab_logic
    run_weather_lab_logic(args)
    sys.exit(0)

def run_pattern_lab(args):
    """Runs the Pattern Lab."""
    from shared.pattern_lab import run_pattern_lab_logic
    run_pattern_lab_logic(args)
    sys.exit(0)

def run_ascii_lab(args):
    """Runs the Ascii Lab."""
    from shared.ascii_lab import run_ascii_lab_logic
    run_ascii_lab_logic(args)
    sys.exit(0)

def run_path_lab(args):
    """Runs the Path Lab."""
    from shared.path_lab import PathLabManager
    manager = PathLabManager()

    if args.action == "analyze":
        info = manager.analyze_path(args.path)
        print(f"--- Analysis of '{args.path}' ---")
        for k, v in info.items():
            if k == "stat" and isinstance(v, dict):
                print("Stat:")
                for sk, sv in v.items():
                    print(f"  {sk}: {sv}")
            else:
                print(f"{k}: {v}")

    elif args.action == "relative":
        res = manager.calculate_relative(args.target, args.start)
        if res["success"]:
            print(res["result"])
        else:
            print(f"Error: {res['error']}")
            sys.exit(1)

    elif args.action == "join":
        print(manager.join_paths(args.base, args.parts))

    elif args.action == "glob":
        matches = manager.glob_path(args.root, args.pattern, args.recursive)
        if not matches:
            print("No matches found.")
        else:
            for m in matches:
                print(m)

    sys.exit(0)

def run_cheatsheet(args):
    """Runs the Cheatsheet Lab."""
    from shared.cheatsheet_lab import CheatsheetManager
    project_dir = args.project_dir.resolve()
    manager = CheatsheetManager(project_dir)

    if args.topic:
        content = manager.get_content(args.topic)
        if content:
            from rich.console import Console
            from rich.markdown import Markdown
            console = Console()
            console.print(Markdown(content))
        else:
            print(f"Cheat sheet '{args.topic}' not found.")
            # Suggest similar
            matches = manager.search(args.topic)
            if matches:
                print(f"Did you mean: {', '.join(matches)}?")
            sys.exit(1)
    elif args.search:
        results = manager.search(args.search)
        if results:
            print(f"--- Search results for '{args.search}' ---")
            for r in results:
                print(f"  - {r}")
        else:
            print(f"No results found for '{args.search}'.")
    else:
        # List all
        print("--- Available Cheat Sheets ---")
        for topic in manager.list_topics():
            print(f"  - {topic}")
        print("\nUsage: cheatsheet <topic> OR cheatsheet --search <query>")
    sys.exit(0)

def run_calendar_lab(args):
    """Runs the Calendar Lab."""
    from shared.calendar_lab import CalendarLabManager
    from datetime import datetime

    project_dir = args.project_dir.resolve()

    # CLI Mode
    manager = CalendarLabManager(project_dir)
    now = datetime.now()
    year = args.year if args.year else now.year
    month = args.month if args.month else now.month

    print(manager.render_ascii_calendar(year, month))
    sys.exit(0)

def run_finance_lab(args):
    """Runs the Finance Lab."""
    from shared.finance_lab import run_finance_lab_logic
    success = run_finance_lab_logic(args)
    sys.exit(0 if success else 1)

def run_runner_lab(args):
    """Runs the Task Runner Lab."""
    from shared.task_runner_lab import TaskRunnerManager
    project_dir = args.project_dir.resolve()
    manager = TaskRunnerManager(project_dir)

    if args.action == "list":
        tasks = manager.list_tasks()
        if not tasks:
            print("No tasks found.")
            sys.exit(0)

        print(f"{'Source':<20} | {'Name':<30} | {'Command'}")
        print("-" * 80)
        for task in tasks:
            print(f"{task.source:<20} | {task.name:<30} | {task.command}")
        sys.exit(0)

    elif args.action == "run":
        if not args.task_name:
            print("Error: --task-name required.", file=sys.stderr)
            sys.exit(1)

        tasks = manager.list_tasks()
        target = next((t for t in tasks if t.name == args.task_name), None)

        if not target:
            print(f"Error: Task '{args.task_name}' not found.", file=sys.stderr)
            sys.exit(1)

        print(f"Running task: {target.name} ({target.command})")
        ret = manager.run_task(target, on_output=lambda x: print(x))
        sys.exit(ret)

def run_gitignore_lab(args):
    """Runs the Gitignore Lab."""
    from shared.gitignore_lab import run_gitignore_lab_logic
    run_gitignore_lab_logic(args)

def run_ollama_lab(args):
    """Runs the Ollama Lab."""
    from shared.ollama_lab import run_ollama_lab_logic
    run_ollama_lab_logic(args)
    sys.exit(0)

def run_mqtt_lab(args):
    """Runs the MQTT Lab."""
    from shared.mqtt_lab import run_mqtt_lab_logic
    run_mqtt_lab_logic(args)
    sys.exit(0)

def run_permissions_lab(args):
    """Runs the Permissions Lab."""
    from shared.permissions_lab import run_permissions_lab_logic
    run_permissions_lab_logic(args)
    sys.exit(0)

def run_systemd_lab(args):
    """Runs the Systemd Lab."""
    from shared.systemd_lab import run_systemd_lab_logic
    run_systemd_lab_logic(args)
    sys.exit(0)

def run_port(args):
    """Manages network ports."""
    from shared.port_manager import PortManager

    if args.action == "check":
        info = PortManager.get_process_on_port(args.port)
        if info:
            print(f"❌ Port {args.port} is in use.")
            print(f"   Process: {info['name']} (PID: {info['pid']})")
            print(f"   User:    {info['username']}")
            print(f"   Command: {info['cmdline']}")
            sys.exit(1)
        else:
            print(f"✅ Port {args.port} is free.")
            sys.exit(0)

    elif args.action == "list":
        ports = PortManager.list_listening_ports()
        if not ports:
            print("No listening ports found.")
            sys.exit(0)

        print(f"{'Port':<8} | {'PID':<8} | {'User':<15} | {'Process'}")
        print("-" * 50)
        for p in ports:
            print(f"{p['port']:<8} | {p['pid'] or '?':<8} | {p['username'] or '?':<15} | {p['name']}")
        sys.exit(0)

    elif args.action == "kill":
        if PortManager.kill_process_on_port(args.port, force=args.force):
            print(f"✅ Process on port {args.port} killed.")
            sys.exit(0)
        else:
            print(f"❌ Failed to kill process on port {args.port}. It might not exist or you lack permission.", file=sys.stderr)
            sys.exit(1)

    elif args.action == "wait":
        print(f"Waiting for port {args.port} to be {args.state} (timeout: {args.timeout}s)...")
        if PortManager.wait_for_port(args.port, state=args.state, timeout=args.timeout):
            print(f"✅ Port {args.port} is {args.state}.")
            sys.exit(0)
        else:
            print(f"❌ Timeout waiting for port {args.port}.", file=sys.stderr)
            sys.exit(1)

def run_archive_lab(args):
    """Runs the Archive Lab."""
    run_archive_lab_logic(args)
    sys.exit(0)

def run_docs_lab(args):
    """Runs the Docs Lab."""
    run_docs_lab_logic(args)
    sys.exit(0)

def run_qr_lab(args):
    """Runs the QR Lab."""
    run_qr_lab_logic(args)
    sys.exit(0)

def run_monitor_lab(args):
    """Runs the Monitor Lab."""
    run_monitor_lab_logic(args)
    sys.exit(0)

def run_metrics_lab(args):
    """Runs the Metrics Lab."""
    run_metrics_lab_logic(args)
    sys.exit(0)

def run_fuzz_lab(args):
    """Runs the Fuzz Lab."""
    run_fuzz_lab_logic(args)
    sys.exit(0)

def run_notify_lab(args):
    """Runs the Notify Lab."""
    run_notify_lab_logic(args)
    sys.exit(0)

def run_contract_lab(args):
    """Runs the Contract Lab."""
    run_contract_lab_logic(args)
    sys.exit(0)

def run_ansible_lab(args):
    """Runs the Ansible Lab."""
    run_ansible_lab_logic(args)
    sys.exit(0)

def run_hex_lab(args):
    """Runs the Hex Lab."""
    run_hex_lab_logic(args)
    sys.exit(0)

def run_speed_lab(args):
    """Runs the Speed Lab."""
    run_speed_lab_logic(args)
    sys.exit(0)

async def run_load_lab(args):
    """Runs the Load Lab."""
    await run_load_lab_logic(args)
    sys.exit(0)

def run_ast_lab(args):
    """Runs the AST Lab."""
    run_ast_lab_logic(args)
    sys.exit(0)

def run_otp_lab(args):
    """Runs the OTP Lab."""
    from shared.otp_lab import run_otp_lab_logic
    run_otp_lab_logic(args)
    sys.exit(0)

async def run_trace_lab(args):
    """Runs the Trace Lab."""
    await run_trace_lab_logic(args)
    sys.exit(0)

def run_http_lab(args):
    """Runs the HTTP Lab."""
    run_http_lab_logic(args)
    sys.exit(0)

def run_geo_lab(args):
    """Runs the Geo Lab."""
    run_geo_lab_logic(args)
    sys.exit(0)

def run_struct_lab(args):
    """Runs the Struct Lab."""
    run_struct_lab_logic(args)
    sys.exit(0)

def run_chart_lab(args):
    """Runs the Chart Lab."""
    run_chart_lab_logic(args)
    sys.exit(0)

def run_enc_lab(args):
    """Runs the Encoding Lab."""
    success = run_enc_lab_logic(args)
    sys.exit(0 if success else 1)

def run_rss_lab(args):
    """Runs the RSS Lab."""
    run_rss_lab_logic(args)
    sys.exit(0)

def run_fs_lab(args):
    """Runs the FS Lab."""
    run_fs_lab_logic(args)
    sys.exit(0)

def run_webhook_lab(args):
    """Runs the Webhook Lab."""
    run_webhook_lab_logic(args)
    sys.exit(0)

def run_hash_lab(args):
    """Runs the Hash Lab."""
    success = run_hash_lab_logic(args)
    sys.exit(0 if success else 1)

def run_random_lab(args):
    """Runs the Random Lab."""
    run_random_lab_logic(args)
    sys.exit(0)

async def run_browser_lab(args):
    """Runs the Browser Lab."""
    await run_browser_lab_logic(args)
    sys.exit(0)

def run_npm_lab(args):
    """Runs the NPM Lab."""
    success = run_npm_lab_logic(args)
    sys.exit(0 if success else 1)

def run_pypi_lab(args):
    """Runs the PyPI Lab."""
    success = run_pypi_lab_logic(args)
    sys.exit(0 if success else 1)

def run_docker_lab(args):
    """Runs the Docker Lab."""
    run_docker_lab_logic(args)
    sys.exit(0)

def run_compose_lab(args):
    """Runs the Compose Lab."""
    run_compose_lab_logic(args)
    sys.exit(0)

def run_k8s_lab(args):
    """Runs the Kubernetes Lab."""
    run_k8s_lab_logic(args)
    sys.exit(0)

def run_uni_lab(args):
    """Runs the Unicode Lab."""
    success = run_uni_lab_logic(args)
    sys.exit(0 if success else 1)

def run_code_query_cli(args):
    """Runs the Code Query tool."""
    from shared.code_query import run_code_query
    run_code_query(args)
    sys.exit(0)

def run_redis_lab(args):
    """Runs the Redis Lab."""
    run_redis_lab_logic(args)
    sys.exit(0)

def run_kafka_lab(args):
    """Runs the Kafka Lab."""
    run_kafka_lab_logic(args)
    sys.exit(0)

async def run_email_lab(args):
    """Runs the Email Lab."""
    await run_email_lab_logic(args)
    sys.exit(0)

def run_ssh_lab(args):
    """Runs the SSH Lab."""
    run_ssh_lab_logic(args)
    sys.exit(0)

def run_tmux_lab(args):
    """Runs the Tmux Lab."""
    run_tmux_lab_logic(args)
    sys.exit(0)

def run_terraform_lab(args):
    """Runs the Terraform Lab."""
    run_terraform_lab_logic(args)
    sys.exit(0)

def run_dns_lab(args):
    """Runs the DNS Lab."""
    run_dns_lab_logic(args)
    sys.exit(0)

def run_whois_lab(args):
    """Runs the Whois Lab."""
    run_whois_lab_logic(args)
    sys.exit(0)

def run_cidr_lab(args):
    """Runs the CIDR Lab utilities."""
    run_cidr_lab_logic(args)
    sys.exit(0)

def run_color_lab(args):
    """Runs the Color Lab utilities."""
    from shared.color_lab import run_color_lab_logic
    # Convert args to dict
    args_dict = vars(args)
    run_color_lab_logic(**args_dict)
    sys.exit(0)

def run_data_lab(args):
    """Runs the Data Lab utilities."""
    run_data_lab_logic(args)
    sys.exit(0)

def run_badges(args):
    """Runs the badges command."""
    success = run_badges_logic(args)
    sys.exit(0 if success else 1)

def run_crypto_lab(args):
    """Runs the Crypto Lab."""
    success = run_crypto_lab_logic(args)
    sys.exit(0 if success else 1)

def run_image_lab(args):
    """Runs the Image Lab."""
    run_image_lab_logic(args)
    sys.exit(0)

def run_media_lab(args):
    """Runs the Media Lab."""
    run_media_lab_logic(args)
    sys.exit(0)

def run_jwt_lab(args):
    """Runs the JWT Lab."""
    from shared.jwt_lab import run_jwt_lab_logic
    success = run_jwt_lab_logic(args)
    sys.exit(0 if success else 1)

def run_uuid_lab(args):
    """Runs the UUID Lab."""
    from shared.uuid_lab import run_uuid_lab_logic
    run_uuid_lab_logic(args)
    sys.exit(0)

def run_password_lab(args):
    """Runs the Password Lab."""
    from shared.password_lab import run_password_lab_logic
    run_password_lab_logic(args)
    sys.exit(0)

def run_text_lab(args):
    """Runs the Text Lab."""
    from shared.text_lab import run_text_lab_logic
    success = run_text_lab_logic(args)
    sys.exit(0 if success else 1)

def run_markdown_lab(args):
    """Runs the Markdown Lab."""
    success = run_markdown_lab_logic(args)
    sys.exit(0 if success else 1)

def run_html_lab(args):
    """Runs the HTML Lab."""
    from shared.html_lab import run_html_lab_logic
    run_html_lab_logic(args)
    sys.exit(0)

def run_xml_lab(args):
    """Runs the XML Lab."""
    from shared.xml_lab import run_xml_lab_logic
    run_xml_lab_logic(args)
    sys.exit(0)

def run_url_lab(args):
    """Runs the URL Lab."""
    from shared.url_lab import run_url_lab_logic
    run_url_lab_logic(args)
    sys.exit(0)

def run_cert_lab(args):
    """Runs the Certificate Lab."""
    from shared.cert_lab import run_cert_lab_logic
    success = run_cert_lab_logic(args)
    sys.exit(0 if success else 1)

def run_time_lab(args):
    """Runs the Time Lab."""
    success = run_time_lab_logic(args)
    sys.exit(0 if success else 1)

def run_math_lab(args):
    """Runs the Math Lab."""
    from shared.math_lab import run_math_lab_logic
    success = run_math_lab_logic(args)
    sys.exit(0 if success else 1)

def run_unit_lab(args):
    """Runs the Unit Lab."""
    success = run_unit_lab_logic(args)
    sys.exit(0 if success else 1)

def run_sys_lab(args):
    """Runs the System Lab."""
    run_sys_lab_logic(args)
    sys.exit(0)

def run_log_lab(args):
    """Runs the Log Lab."""
    run_log_lab_logic(args)
    sys.exit(0)

async def run_sql_lab(args):
    """Runs the SQL Lab."""
    await run_sql_lab_logic(args)
    sys.exit(0)

def run_csv_lab(args):
    """Runs the CSV Lab."""
    run_csv_lab_logic(args)
    sys.exit(0)

def run_excel_lab(args):
    """Runs the Excel Lab."""
    success = run_excel_lab_logic(args)
    sys.exit(0 if success else 1)

def run_template_lab(args):
    """Runs the Template Lab."""
    run_template_lab_logic(args)
    sys.exit(0)

def run_json_lab(args):
    """Runs the JSON Lab."""
    run_json_lab_logic(args)
    sys.exit(0)

def run_yaml_lab(args):
    """Runs the YAML Lab."""
    run_yaml_lab_logic(args)
    sys.exit(0)

def run_toml_lab(args):
    """Runs the TOML Lab."""
    run_toml_lab_logic(args)
    sys.exit(0)

def run_semver_lab(args):
    """Runs the SemVer Lab."""
    from shared.semver_lab import run_semver_lab_logic
    run_semver_lab_logic(args)
    sys.exit(0)

def run_gantt(args):
    """Generates an ASCII Gantt chart for the current sprint plan."""
    project_dir = args.project_dir.resolve()
    success = run_gantt_logic(project_dir)
    sys.exit(0 if success else 1)

def run_kanban(args):
    """Runs the Kanban board CLI."""
    from shared.cli_kanban import run_kanban_logic
    project_dir = args.project_dir.resolve()

    # Determine action and args
    action = args.action
    task_id = args.task_id if hasattr(args, 'task_id') else None
    status = args.status if hasattr(args, 'status') else None

    success = run_kanban_logic(project_dir, action, task_id, status)
    sys.exit(0 if success else 1)

async def run_resume(args):
    """Generates a project resume."""
    from shared.resume import run_resume_logic

    project_dir = args.project_dir.resolve()
    output = Path(args.output).resolve() if args.output else None

    await run_resume_logic(
        project_dir=project_dir,
        output=output,
        agent_type=args.agent,
        model=args.model
    )
    sys.exit(0)

async def run_retro(args):
    """Conducts a retrospective."""
    project_dir = args.project_dir.resolve()
    output = Path(args.output).resolve() if args.output else None

    success = await run_retro_logic(
        project_dir=project_dir,
        run_id=args.run_id,
        output=output,
        agent_type=args.agent,
        model=args.model
    )
    sys.exit(0 if success else 1)

def run_devtools(args):
    """Runs developer tools from CLI."""
    from shared.devtools import DevTools

    if args.action == "epoch":
        if args.value:
            # Try parsing as float first (timestamp to date)
            try:
                ts = float(args.value)
                print(DevTools.epoch_to_date(ts))
            except ValueError:
                # Try parsing as date string (date to timestamp)
                try:
                    print(DevTools.date_to_epoch(args.value))
                except ValueError as e:
                    print(f"Error: {e}")
        else:
            # No value? print current time
            import time
            now = time.time()
            print(f"Current Epoch: {now}")
            print(f"Current Date:  {DevTools.epoch_to_date(now)}")

    elif args.action == "uuid":
        print(DevTools.generate_uuid())

    elif args.action == "base64":
        if args.decode:
            print(DevTools.base64_decode(args.text))
        else:
            print(DevTools.base64_encode(args.text))

    elif args.action == "hash":
        print(DevTools.calculate_hash(args.text, args.algo))

    elif args.action == "json":
        print(DevTools.format_json(args.text))

    sys.exit(0)

def run_quiz(args):
    """Runs the codebase quiz."""
    from shared.quiz import QuizGenerator

    project_dir = args.project_dir.resolve()

    if args.tui:
        # Launch TUI
        from shared.tui import AgentTUI
        print("Launching TUI... Navigate to 'Quiz' tab.")
        app = AgentTUI(project_dir=project_dir)
        app.run()
        return

    # CLI Mode
    generator = QuizGenerator(project_dir)
    questions = generator.generate_questions(10)
    score = 0

    print(f"--- Codebase Quiz: {project_dir.name} ---")
    print(f"Generated {len(questions)} questions.\n")

    for i, q in enumerate(questions):
        print(f"Q{i+1}: {q.text}")
        for idx, opt in enumerate(q.options):
            print(f"  [{idx+1}] {opt}")

        while True:
            try:
                choice = input("Answer (1-4): ").strip()
                if not choice: continue
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(q.options):
                    break
                print("Invalid choice.")
            except ValueError:
                print("Invalid input.")

        if choice_idx == q.correct_index:
            print("✅ Correct!\n")
            score += 1
        else:
            print(f"❌ Incorrect. {q.explanation}\n")

    print(f"--- Game Over ---")
    print(f"Final Score: {score}/{len(questions)}")
    sys.exit(0)

def run_kata(args):
    """Runs the Refactoring Kata game."""
    from shared.kata import KataManager

    project_dir = args.project_dir.resolve()
    manager = KataManager(project_dir)

    if args.action == "list":
        print(f"--- Refactoring Katas in: {project_dir} ---")
        print("Scanning for high-complexity code...")
        challenges = manager.list_challenges(limit=args.limit)

        if not challenges:
            print("✅ No high-complexity challenges found! Great job.")
            sys.exit(0)

        print(f"Found {len(challenges)} challenges:\n")
        header = f"{'#':<3} | {'Complexity':<10} | {'File':<40} | {'Function'}"
        print(header)
        print("-" * len(header))

        for i, c in enumerate(challenges):
            file_display = c["file"]
            if len(file_display) > 38:
                file_display = "..." + file_display[-35:]
            print(f"{i+1:<3} | {c['complexity']:<10} | {file_display:<40} | {c['function']}")

        print("\nTo start a challenge, run: main.py kata start --index <number>")

    elif args.action == "start":
        challenges = manager.list_challenges(limit=args.limit) # Re-fetch to be safe/consistent indexes
        if not challenges:
             print("No challenges found.")
             sys.exit(0)

        idx = args.index - 1
        if not (0 <= idx < len(challenges)):
            print("Invalid index.")
            sys.exit(1)

        target = challenges[idx]
        print(f"--- Kata Challenge: {target['function']} ---")
        print(f"File: {target['file']}")
        print(f"Line: {target['lineno']}")
        print(f"Current Complexity: {target['complexity']}")
        print("\nGoal: Reduce complexity below 10 (or significantly lower than current).")
        print("Instructions:")
        print("1. Open the file in your editor.")
        print("2. Refactor the function to simplify logic (extract methods, reduce nesting).")
        print("3. Run verification command below:")
        # Easier verification command
        print(f"\n  python3 main.py kata verify --file \"{target['file']}\" --function \"{target['function']}\" --target {target['complexity']}")

    elif args.action == "verify":
        if not args.file or not args.function or not args.target:
            print("Error: --file, --function, and --target are required for verify.", file=sys.stderr)
            sys.exit(1)

        result = manager.verify_improvement(args.file, args.function, int(args.target))

        if result["success"]:
            print(f"✅ {result['message']}")
        else:
            print(f"❌ {result['message']}")

    sys.exit(0)

def run_serve(args):
    """Starts a local development server."""
    project_dir = args.project_dir.resolve()
    manager = ServeManager(project_dir)
    success = manager.start(
        port=args.port,
        host=args.host,
        command=args.command_str,
        dry_run=args.dry_run
    )
    sys.exit(0 if success else 1)

def run_ide(args):
    """Generates IDE configuration files."""
    from shared.ide_config import IdeConfigManager

    project_dir = args.project_dir.resolve()
    manager = IdeConfigManager(project_dir)

    if args.action == "vscode" or args.action == "cursor":
        success = manager.generate_vscode_config(dry_run=args.dry_run, force=args.force)
        sys.exit(0 if success else 1)

def run_scheduler(args):
    """Manages the autonomous scheduler."""
    project_dir = args.project_dir.resolve()
    scheduler = Scheduler(project_dir)

    if args.action == "init":
        if scheduler.init_config():
            print(f"✅ Created default schedule at {scheduler.config_path}")
        else:
            print(f"ℹ️  Schedule config already exists at {scheduler.config_path}")

    elif args.action == "list":
        scheduler.load_config()
        scheduler.list_tasks()

    elif args.action == "start":
        scheduler.load_config()
        scheduler.start()

    sys.exit(0)

def run_chaos(args):
    """Runs chaos engineering experiments."""
    run_chaos_logic(
        project_dir=args.project_dir,
        action=args.action,
        dry_run=getattr(args, 'dry_run', False),
        yes=getattr(args, 'yes', False),
        interface=getattr(args, 'interface', 'eth0')
    )
    sys.exit(0)

def run_network(args):
    """Generates an interactive network graph of the codebase."""
    output_path = Path(args.output).resolve()
    run_network_logic(
        project_dir=args.project_dir,
        output_file=output_path,
        include_authors=args.include_authors,
        include_git=args.include_git,
        limit=args.limit
    )
    sys.exit(0)

def run_onboard(args):
    """Runs the onboarding wizard."""
    run_onboard_logic(args.project_dir)
    sys.exit(0)

def run_secrets(args):
    """Manages encrypted secrets."""
    from shared.secrets import SecretsManager
    project_dir = args.project_dir.resolve()
    manager = SecretsManager(project_dir)

    try:
        if args.action == "init":
            if manager.generate_key(force=args.force):
                print(f"✅ Generated new encryption key at {manager.key_path}")
            else:
                print(f"ℹ️  Key already exists at {manager.key_path}. Use --force to overwrite.")

        elif args.action == "set":
            if not args.name or not args.value:
                print("Error: Name and value required.", file=sys.stderr)
                sys.exit(1)
            manager.set_secret(args.name, args.value)
            print(f"✅ Secret '{args.name}' set.")

        elif args.action == "get":
            val = manager.get_secret(args.name)
            if val is not None:
                print(val)
            else:
                print(f"❌ Secret '{args.name}' not found.", file=sys.stderr)
                sys.exit(1)

        elif args.action == "list":
            secrets = manager.list_secrets()
            if secrets:
                print("--- Secrets ---")
                for s in secrets:
                    print(f"  - {s}")
            else:
                print("No secrets found.")

        elif args.action == "delete":
            if manager.delete_secret(args.name):
                print(f"✅ Secret '{args.name}' deleted.")
            else:
                print(f"❌ Secret '{args.name}' not found.", file=sys.stderr)
                sys.exit(1)

        elif args.action == "run":
            cmd_list = args.command_args
            if cmd_list and cmd_list[0] == "--":
                cmd_list = cmd_list[1:]

            if not cmd_list:
                print("Error: Command required.", file=sys.stderr)
                sys.exit(1)

            # Decrypt secrets and inject into env
            env = manager.get_env_with_secrets()

            # Execute command
            # We use os.execvpe to replace the current process
            cmd = cmd_list[0]
            cmd_args = cmd_list
            try:
                os.execvpe(cmd, cmd_args, env)
            except FileNotFoundError:
                print(f"❌ Command not found: {cmd}", file=sys.stderr)
                sys.exit(1)
            except OSError as e:
                print(f"❌ Error executing command: {e}", file=sys.stderr)
                sys.exit(1)

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

    sys.exit(0)

async def run_db(args):
    """Manages database operations."""
    from shared.database_manager import DatabaseManager
    project_dir = args.project_dir.resolve()
    manager = DatabaseManager(project_dir)

    if args.action == "init":
        sys.exit(0 if manager.init() else 1)
    elif args.action == "migrate":
        sys.exit(0 if manager.migrate() else 1)
    elif args.action == "seed":
        sys.exit(0 if manager.seed() else 1)
    elif args.action == "inspect":
        sys.exit(0 if manager.inspect() else 1)
    elif args.action == "query":
        from shared.db_query import run_db_query_logic
        success = await run_db_query_logic(
            query=args.query,
            project_dir=project_dir,
            agent_type=args.agent,
            model=args.model,
            yes=args.yes,
            verbose=args.verbose
        )
        sys.exit(0 if success else 1)
    else:
        print(f"Unknown action: {args.action}", file=sys.stderr)
        sys.exit(1)

async def run_adr(args):
    """Manages Architecture Decision Records."""
    from shared.adr import ADRManager
    project_dir = args.project_dir.resolve()
    manager = ADRManager(project_dir)

    if args.action == "init":
        print(manager.init_adr_repo())
        sys.exit(0)

    elif args.action == "new":
        if not args.title:
            print("Error: Title required for 'new' action.", file=sys.stderr)
            sys.exit(1)
        path = manager.create_adr(args.title, status="Proposed")
        print(f"✅ Created ADR: {path}")
        sys.exit(0)

    elif args.action == "list":
        adrs = manager.list_adrs()
        if not adrs:
            print("No ADRs found.")
        else:
            print("--- Architecture Decision Records ---")
            for adr in adrs:
                print(f"{adr['filename']} - {adr['title']} ({adr['status']})")
        sys.exit(0)

    elif args.action == "status":
        if not args.id or not args.status:
            print("Error: ID and Status required.", file=sys.stderr)
            sys.exit(1)
        if manager.update_status(args.id, args.status):
            print(f"✅ Updated status of ADR {args.id} to {args.status}")
        else:
            print(f"❌ ADR {args.id} not found.", file=sys.stderr)
            sys.exit(1)

    elif args.action == "generate":
        if not args.title or not args.context:
            print("Error: Title and --context required for generation.", file=sys.stderr)
            sys.exit(1)

        content = await manager.generate_adr_content(
            args.title,
            args.context,
            agent_type=args.agent,
            model=args.model
        )

        path = manager.create_adr(args.title, status="Proposed", content=content)
        print(f"✅ Generated and created ADR: {path}")
        sys.exit(0)

    sys.exit(0)


def run_session(args):
    """Manages work sessions."""
    project_dir = args.project_dir.resolve()
    manager = WorkSessionManager(project_dir)

    if args.action == "new":
        if not args.name:
            print("Error: Name required for 'new' action.", file=sys.stderr)
            sys.exit(1)
        try:
            session = manager.create(args.name, args.description or "")
            print(f"✅ Created session: {session.name}")
            print(f"   Files: {len(session.files)}")
            print(f"   Notes: {len(session.notes)}")
        except FileExistsError as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "load":
        if not args.name:
            print("Error: Name required for 'load' action.", file=sys.stderr)
            sys.exit(1)
        try:
            manager.set_active_session(args.name)
            print(f"✅ Loaded session: {args.name}")
        except FileNotFoundError:
            print(f"❌ Session '{args.name}' not found.", file=sys.stderr)
            sys.exit(1)

    elif args.action == "list":
        sessions = manager.list_sessions()
        if not sessions:
            print("No sessions found.")
        else:
            active = manager.get_active_session()
            print("--- Available Sessions ---")
            for s in sessions:
                marker = "*" if active and active.name == s["name"] else " "
                print(f"{marker} {s['name']:<20} {s['updated_at'][:16]}   {s['description']}")

    elif args.action == "info":
        name = args.name
        if not name:
            active = manager.get_active_session()
            if active:
                name = active.name
            else:
                print("Error: No active session. Please specify a name or load a session.", file=sys.stderr)
                sys.exit(1)

        session = manager.load_session(name)
        if not session:
            print(f"❌ Session '{name}' not found.", file=sys.stderr)
            sys.exit(1)

        print(f"--- Session: {session.name} ---")
        print(f"Created: {session.created_at}")
        print(f"Updated: {session.updated_at}")
        print(f"Description: {session.description}")
        print("\nFiles:")
        for f in session.files:
            print(f"  - {f}")
        print("\nNotes:")
        for n in session.notes:
            print(f"  {n}")

    elif args.action == "add":
        if not args.file:
            print("Error: File required.", file=sys.stderr)
            sys.exit(1)

        target_session = args.name
        if not target_session:
            active = manager.get_active_session()
            if active:
                target_session = active.name
            else:
                 print("Error: No active session. Specify name with --name.", file=sys.stderr)
                 sys.exit(1)

        try:
            manager.add_file(target_session, args.file)
            print(f"✅ Added {args.file} to session '{target_session}'")
        except FileNotFoundError:
             print(f"❌ Session '{target_session}' not found.", file=sys.stderr)
             sys.exit(1)

    elif args.action == "remove":
        if not args.file:
            print("Error: File required.", file=sys.stderr)
            sys.exit(1)

        target_session = args.name
        if not target_session:
            active = manager.get_active_session()
            if active:
                target_session = active.name
            else:
                 print("Error: No active session. Specify name with --name.", file=sys.stderr)
                 sys.exit(1)

        try:
            manager.remove_file(target_session, args.file)
            print(f"✅ Removed {args.file} from session '{target_session}'")
        except FileNotFoundError:
             print(f"❌ Session '{target_session}' not found.", file=sys.stderr)
             sys.exit(1)

    elif args.action == "note":
        if not args.note:
             print("Error: Note text required.", file=sys.stderr)
             sys.exit(1)

        target_session = args.name
        if not target_session:
            active = manager.get_active_session()
            if active:
                target_session = active.name
            else:
                 print("Error: No active session. Specify name with --name.", file=sys.stderr)
                 sys.exit(1)

        try:
            manager.add_note(target_session, args.note)
            print(f"✅ Added note to session '{target_session}'")
        except FileNotFoundError:
             print(f"❌ Session '{target_session}' not found.", file=sys.stderr)
             sys.exit(1)

    elif args.action == "stop":
        manager.stop_session()
        print("✅ Session stopped.")

    elif args.action == "delete":
        if not args.name:
            print("Error: Name required.", file=sys.stderr)
            sys.exit(1)

        if manager.delete_session(args.name):
            print(f"✅ Deleted session '{args.name}'")
        else:
            print(f"❌ Session '{args.name}' not found.", file=sys.stderr)
            sys.exit(1)

    sys.exit(0)

def run_playground(args):
    """Manages the agent playground."""
    project_dir = args.project_dir.resolve()
    manager = PlaygroundManager(project_dir)

    if args.action == "create":
        name = args.name or "scratch.py"
        path = manager.create(name)
        print(f"✅ Created playground file: {path}")
        print(f"Run it with: {sys.argv[0]} playground run {path.name}")

    elif args.action == "run":
        if not args.name:
            print("Error: Name required for 'run' action.", file=sys.stderr)
            sys.exit(1)
        success = manager.run(args.name)
        sys.exit(0 if success else 1)

    elif args.action == "list":
        files = manager.list_files()
        if not files:
            print("Playground is empty.")
        else:
            print("--- Playground Files ---")
            for f in files:
                print(f"  - {f.name}")

    elif args.action == "delete":
        if not args.name:
            print("Error: Name required for 'delete' action.", file=sys.stderr)
            sys.exit(1)
        if manager.delete(args.name):
            print(f"✅ Deleted {args.name}")
        else:
            print(f"❌ File {args.name} not found.")
            sys.exit(1)

    sys.exit(0)

def run_init(args):
    """Runs an interactive setup wizard for a new project."""
    import subprocess
    import shutil

    project_dir = args.project_dir.resolve()
    print("--- Interactive Project Initialization ---")
    print(f"This wizard will set up your project in: {project_dir}\n")

    # --- Step 1: Git Repository Check ---
    print("--- [1/4] Git Repository ---")
    git_path = shutil.which("git")
    if not git_path:
        print("❌ Warning: 'git' command not found. It's highly recommended to use version control.")
    elif (project_dir / ".git").is_dir():
        print("✅ Git repository already exists.")
    else:
        print("No Git repository found.")
        if not args.yes:
            confirm_git = input("Do you want to initialize a new Git repository? [Y/n]: ").strip().lower()
        if args.yes or confirm_git in ['y', '']:
            try:
                project_dir.mkdir(parents=True, exist_ok=True)
                subprocess.run([git_path, "init", "-b", "main", str(project_dir)], check=True, capture_output=True)
                print("✅ Successfully initialized a new Git repository.")
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                stderr = getattr(e, 'stderr', str(e))
                if isinstance(stderr, bytes): stderr = stderr.decode()
                print(f"❌ Error initializing Git repository: {stderr}")

    # --- Step 2: .gitignore ---
    print("\n--- [2/4] .gitignore file ---")
    gitignore_path = project_dir / ".gitignore"
    if gitignore_path.exists():
        print("✅ .gitignore file already exists.")
    else:
        print("No .gitignore file found.")
        if not args.yes:
            confirm_gitignore = input("Do you want to create a Python-focused .gitignore file? [Y/n]: ").strip().lower()
        if args.yes or confirm_gitignore in ['y', '']:
            try:
                gitignore_content = """
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
pip-wheel-metadata/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
#  Usually these files are written by a python script from a template
#  before PyInstaller builds the exe, so as to inject date/other infos into it.
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/
.pytest_cache/
cover/

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Agent artifacts
.agent_trash/
.agent_archives/
.agent_db.sqlite
.agent_run_id
.agent_history
.agent_branch
worktrees/
final_metrics.txt
dashboard_state.json

# Secrets & Configuration
.agent_secrets.key
.agent_secrets.enc
agent_config.yaml
"""
                gitignore_path.write_text(gitignore_content.strip())
                print("✅ Created a .gitignore file.")
            except IOError as e:
                print(f"❌ Error creating .gitignore file: {e}")

    # --- Step 3: app_spec.txt ---
    print("\n--- [3/4] Application Specification ---")
    spec_path = project_dir / "app_spec.txt"
    if spec_path.exists():
        print(f"✅ Application spec file already exists: {spec_path.name}")
        if not args.yes:
             overwrite_spec = input("Do you want to overwrite it? [y/N]: ").strip().lower()
             if overwrite_spec != 'y':
                 spec_path = None # Skip writing

    if spec_path:
        print("Please describe the application you want to build.")
        print("Be detailed. The more information you provide, the better the agent will perform.")
        print("Press Enter twice to save and continue.")

        spec_lines = []
        try:
            while True:
                line = input("> ")
                if not line and len(spec_lines) > 0 and spec_lines[-1] == "":
                    # Two consecutive empty lines
                    spec_lines.pop() # Remove the last empty line
                    break
                spec_lines.append(line)
        except (EOFError, KeyboardInterrupt):
            print("\nSkipping spec creation.")
            spec_lines = []

        if spec_lines:
            try:
                spec_path.write_text("\n".join(spec_lines))
                print(f"✅ Saved application specification to {spec_path.name}")
            except IOError as e:
                print(f"❌ Error writing to {spec_path.name}: {e}")

    # --- Step 4: Next Steps ---
    print("\n--- [4/4] Next Steps ---")
    print("✅ Project initialization complete!")
    print("\nYou're ready to start working with the agent. Here are some common next steps:")
    executable_name = os.path.basename(sys.argv[0])
    print(f"  - To start the agent and build your app:")
    print(f"    {executable_name} --spec app_spec.txt")
    print(f"  - To see all available commands:")
    print(f"    {executable_name} --help")
    print(f"  - For a detailed health check of your environment:")
    print(f"    {executable_name} doctor")

    sys.exit(0)


def run_guardrails(args):
    """Manages project guardrails (policy enforcement)."""
    from shared.guardrails import GuardrailsManager

    project_dir = args.project_dir.resolve()
    manager = GuardrailsManager(project_dir)

    print(f"--- Guardrails in: {project_dir} ---")

    if args.action == "init":
        try:
            path = manager.create_default_config()
            print(f"✅ Created default configuration at: {path}")
        except Exception as e:
            print(f"❌ Error creating configuration: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "list":
        if not manager.policies:
            print("No policies configured. Run 'init' to create a default configuration.")
        else:
            print("Active Policies:")
            for p in manager.policies:
                p_type = p.config.get("type", "unknown")
                print(f"  - {p.name} ({p_type})")

    elif args.action == "check":
        print("Running policy checks...")
        violations = manager.run()

        if not violations:
            print("\n✅ All checks passed.")
            sys.exit(0)
        else:
            print(f"\n❌ Found {len(violations)} violations:")
            for v in violations:
                loc = v.file or "Project"
                if v.line:
                    loc += f":{v.line}"
                print(f"  - [{v.policy_name}] {v.message} ({loc})")
            sys.exit(1)

    sys.exit(0)


def run_validate():
    """Validates the agent_config.yaml file."""
    print("--- Validating Agent Configuration ---")
    errors = []

    from shared.config_loader import get_config_path, load_config_from_file
    config_path = get_config_path()

    if not config_path or not config_path.exists():
        print("❌ Configuration file (agent_config.yaml) not found in any of the searched paths.")
        print("   Searched in ./, ~/.config/combined-autonomous-coding/, and ~/.gemini/")
        sys.exit(1)

    print(f"Found configuration file at: {config_path}")

    try:
        config_data = load_config_from_file()
    except Exception as e:
        print(f"❌ Error loading or parsing YAML from {config_path}: {e}")
        sys.exit(1)

    # Jira Validation
    if 'jira' in config_data:
        jira_config = config_data['jira']
        if not isinstance(jira_config, dict):
            errors.append("Jira config ('jira') must be a dictionary.")
        else:
            required_jira_keys = ['url', 'email', 'token']
            for key in required_jira_keys:
                if key not in jira_config or not jira_config.get(key):
                    errors.append(f"Jira config in {config_path} is missing required key or value: '{key}'")

    # Notification Validation (check for non-empty strings)
    if 'slack_webhook_url' in config_data and config_data.get('slack_webhook_url'):
        url = config_data['slack_webhook_url']
        if not isinstance(url, str) or not url.startswith("https://hooks.slack.com/"):
            errors.append(f"Invalid Slack webhook URL format in {config_path}.")

    if 'discord_webhook_url' in config_data and config_data.get('discord_webhook_url'):
        url = config_data['discord_webhook_url']
        if not isinstance(url, str) or not url.startswith("https://discord.com/api/webhooks/"):
            errors.append(f"Invalid Discord webhook URL format in {config_path}.")

    # Telegram Validation
    if 'telegram_bot_token' in config_data and config_data.get('telegram_bot_token'):
        token = config_data['telegram_bot_token']
        if not isinstance(token, str):
            errors.append(f"Telegram bot token must be a string in {config_path}.")

    if 'telegram_chat_id' in config_data and config_data.get('telegram_chat_id'):
        chat_id = config_data['telegram_chat_id']
        if not isinstance(chat_id, str):
            errors.append(f"Telegram chat ID must be a string in {config_path}.")

    # Type checks for other common keys
    type_checks = {
        'model': str, 'max_iterations': int, 'manager_frequency': int,
        'manager_model': str, 'timeout': (int, float), 'max_error_wait': (int, float),
        'max_agents': int, 'dind_enabled': bool, 'run_manager_first': bool,
        'notification_settings': dict,
    }
    for key, expected_type in type_checks.items():
        if key in config_data and config_data.get(key) is not None and not isinstance(config_data[key], expected_type):
            errors.append(f"'{key}' has incorrect type in {config_path}. Expected {expected_type}, got {type(config_data[key]).__name__}.")

    if errors:
        print(f"\n❌ Configuration validation failed with {len(errors)} error(s):")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print("\n✅ Configuration is valid!")
        sys.exit(0)


def run_doctor(args):
    """Runs a comprehensive health check on the environment."""
    import shutil
    import requests

    print("--- Running Environment Health Check (Doctor) ---")
    project_dir = args.project_dir.resolve()
    all_checks_passed = True
    error_messages = []

    # 1. Configuration File Check
    print("\n[1] Checking Configuration File...")
    from shared.config_loader import get_config_path, load_config_from_file
    config_path = get_config_path()
    config_data = {}

    if not config_path or not config_path.exists():
        print("  ❌ Configuration file (agent_config.yaml) not found.")
        all_checks_passed = False
    else:
        print(f"  ✅ Found configuration file at: {config_path}")
        try:
            # Re-using validation logic from run_validate without exiting
            config_data = load_config_from_file() or {}
            validation_errors = []
            if 'jira' in config_data:
                jira_config = config_data.get('jira', {})
                if not all(k in jira_config and jira_config[k] for k in ['url', 'email', 'token']):
                    validation_errors.append("Jira config is missing required values for 'url', 'email', or 'token'.")

            if config_data.get('slack_webhook_url') and not str(config_data['slack_webhook_url']).startswith("https://hooks.slack.com/"):
                validation_errors.append("Invalid Slack webhook URL format.")

            if config_data.get('discord_webhook_url') and not str(config_data['discord_webhook_url']).startswith("https://discord.com/api/webhooks/"):
                validation_errors.append("Invalid Discord webhook URL format.")

            if validation_errors:
                all_checks_passed = False
                for err in validation_errors:
                    print(f"  ❌ {err}")
                    error_messages.append(f"Config validation: {err}")
            else:
                print("  ✅ Configuration file format appears valid.")
        except yaml.YAMLError as e:
            print(f"  ❌ Error parsing YAML configuration: {e}")
            all_checks_passed = False
            error_messages.append(f"Config parsing error: {e}")
        except Exception as e:
            print(f"  ❌ Error loading or parsing configuration: {e}")
            all_checks_passed = False
            error_messages.append(f"Config loading error: {e}")

    # 2. Dependency Checks (Git)
    print("\n[2] Checking Dependencies...")
    if shutil.which("git"):
        print("  ✅ Git executable found.")
    else:
        print("  ❌ Git executable not found. Git is required for version control.")
        all_checks_passed = False
        error_messages.append("Dependency check: Git not found.")

    # 3. Connectivity Checks
    print("\n[3] Checking API Connectivity...")
    # Jira Connectivity
    if 'jira' in config_data and all(k in config_data['jira'] for k in ['url', 'email', 'token']):
        print("  - Checking Jira connection...")
        try:
            from shared.jira_client import JiraClient
            from shared.config import JiraConfig
            jira_config = JiraConfig(**config_data['jira'])
            jira_client = JiraClient(jira_config)
            jira_client.check_connection()
            print("    ✅ Jira connection successful.")
        except Exception as e:
            print(f"    ❌ Jira connection failed: {e}")
            all_checks_passed = False
            error_messages.append(f"Jira connection: {e}")
    else:
        print("  - Jira not configured, skipping check.")

    # Webhook Connectivity (using requests to avoid heavy deps)
    for service, url_key in [("Slack", "slack_webhook_url"), ("Discord", "discord_webhook_url")]:
        webhook_url = config_data.get(url_key)
        if webhook_url:
            print(f"  - Checking {service} webhook...")
            try:
                response = requests.head(webhook_url, timeout=5)
                # Most webhooks will return 405 for HEAD but it confirms reachability. 200 is also fine.
                if response.status_code in [200, 405]:
                    print(f"    ✅ {service} webhook is reachable.")
                else:
                    print(f"    ❌ {service} webhook returned status {response.status_code}.")
                    all_checks_passed = False
                    error_messages.append(f"{service} webhook check failed with status {response.status_code}.")
            except requests.RequestException as e:
                print(f"    ❌ Could not connect to {service} webhook: {e}")
                all_checks_passed = False
                error_messages.append(f"{service} webhook connection error: {e}")
        else:
            print(f"  - {service} not configured, skipping check.")

    # Telegram Connectivity
    telegram_token = config_data.get('telegram_bot_token')
    if telegram_token:
        print("  - Checking Telegram bot...")
        try:
            # We call getMe to verify the token
            tg_url = f"https://api.telegram.org/bot{telegram_token}/getMe"
            response = requests.get(tg_url, timeout=5)
            if response.status_code == 200:
                bot_info = response.json().get('result', {})
                print(f"    ✅ Telegram bot connected: {bot_info.get('username')}")
            else:
                print(f"    ❌ Telegram bot check failed: {response.status_code} {response.reason}")
                all_checks_passed = False
                error_messages.append(f"Telegram check failed: {response.status_code}")
        except requests.RequestException as e:
            print(f"    ❌ Could not connect to Telegram API: {e}")
            all_checks_passed = False
            error_messages.append(f"Telegram connection error: {e}")
    else:
        print("  - Telegram not configured, skipping check.")

    # 4. Permissions Check
    print("\n[4] Checking File System Permissions...")
    try:
        if not project_dir.exists():
            project_dir.mkdir(parents=True, exist_ok=True)
            print(f"  ✅ Project directory created at: {project_dir}")

        if os.access(project_dir, os.W_OK):
            print(f"  ✅ Project directory is writable: {project_dir}")
        else:
            print(f"  ❌ Project directory is not writable: {project_dir}")
            all_checks_passed = False
            error_messages.append(f"Permissions: Project directory '{project_dir}' not writable.")
    except Exception as e:
        print(f"  ❌ Error checking permissions for {project_dir}: {e}")
        all_checks_passed = False
        error_messages.append(f"Permissions check error: {e}")

    # Final Summary
    print("\n--- Health Check Summary ---")
    if all_checks_passed:
        print("✅ All checks passed. Your environment is ready!")
        sys.exit(0)
    else:
        print(f"❌ Found {len(error_messages)} issue(s). Please review the errors above.")
        sys.exit(1)


def run_show_config(config):
    """Prints the final resolved configuration as JSON and exits."""
    from shared.utils import EnhancedJSONEncoder
    print(json.dumps(config, cls=EnhancedJSONEncoder, indent=2, sort_keys=True))
    sys.exit(0)

from shared.cli_utils import _run_history_graph_logic

def run_history_graph(args):
    """Displays a graph of historical metrics."""
    graph_output = _run_history_graph_logic(
        project_dir=args.project_dir,
        metric=args.metric,
        limit=args.limit
    )
    print(graph_output)
    sys.exit(0)


def run_list_agents():
    """Prints a list of available agents and their descriptions."""
    print("--- Available Agents ---")
    # Find the longest agent name for alignment
    max_len = max(len(name) for name in AVAILABLE_AGENTS.keys())

    for name, description in AVAILABLE_AGENTS.items():
        # Format with padding for alignment
        print(f"  {name.ljust(max_len)} : {description}")
    sys.exit(0)


RECOMMENDED_MODELS = {
    "gemini": [
        {"model": "gemini-1.5-pro-latest", "description": "Most capable model, multi-modal, large context.", "recommended": True},
        {"model": "gemini-1.5-flash-latest", "description": "Fast and cost-effective, multi-modal.", "recommended": False},
        {"model": "gemini-1.0-pro", "description": "Previous generation, balanced performance.", "recommended": False},
    ],
    "cursor": [
        {"model": "claude-3.5-sonnet", "description": "Strong performance, good for complex reasoning.", "recommended": True},
        {"model": "gpt-4o", "description": "Fast, multi-modal, high performance.", "recommended": False},
        {"model": "claude-3-opus", "description": "Most powerful Claude model for highly complex tasks.", "recommended": False},
    ],
    "openrouter": [
        {"model": "anthropic/claude-3.5-sonnet", "description": "Top-tier model, good for reasoning.", "recommended": True},
        {"model": "openai/gpt-4o", "description": "Flagship OpenAI model, multi-modal.", "recommended": False},
        {"model": "google/gemini-flash-1.5", "description": "Fast and efficient model from Google.", "recommended": False},
        {"model": "mistralai/mistral-large", "description": "Flagship model from Mistral AI.", "recommended": False},
    ],
    "local": [
        {"model": "ollama/llama3", "description": "High-performing open source model.", "recommended": True},
        {"model": "ollama/codellama", "description": "Specialized for code generation.", "recommended": False},
    ]
}

def run_models(args):
    """Prints a list of recommended models for each agent."""
    agent_filter = args.agent

    if agent_filter and agent_filter not in RECOMMENDED_MODELS:
        print(f"❌ Error: Agent '{agent_filter}' not found. Use 'list-agents' to see available agents.", file=sys.stderr)
        sys.exit(1)

    print("--- Recommended Models ---")

    for agent_name, models in RECOMMENDED_MODELS.items():
        if agent_filter and agent_name != agent_filter:
            continue

        print(f"\n# {agent_name.capitalize()} Agent")
        header = f"  {'Model Name':<30} | {'Description'}"
        print(header)
        print(f"  {'-'*30}-+-{'-'*40}")

        for model_info in models:
            rec_marker = " (recommended)" if model_info["recommended"] else ""
            print(f"  {model_info['model']:<30} | {model_info['description']}{rec_marker}")
    sys.exit(0)


def run_configure():
    """Interactively create or update the agent_config.yaml file."""
    print("--- Agent Configuration ---")

    # Use XDG path as the primary location
    config_dir = Path(platformdirs.user_config_dir("combined-autonomous-coding"))
    config_path = config_dir / "agent_config.yaml"

    config_dir.mkdir(parents=True, exist_ok=True)

    # Load existing config if it exists
    existing_config: dict = {}
    if config_path.exists():
        print(f"Loading existing configuration from: {config_path}")
        with open(config_path, 'r') as f:
            existing_config = yaml.safe_load(f) or {}
    else:
        print(f"Creating new configuration file at: {config_path}")

    # Helper for user input
    def get_input(prompt, default_value=None):
        if default_value:
            prompt_text = f"{prompt} [{default_value}]: "
        else:
            prompt_text = f"{prompt}: "

        user_input = input(prompt_text).strip()
        return user_input or default_value

    # --- JIRA Configuration ---
    print("\n--- Jira Integration (optional) ---")
    jira_config = existing_config.get('jira', {})

    jira_url = get_input("Jira URL (e.g., https://your-domain.atlassian.net)", jira_config.get('url'))
    if jira_url:
        jira_email = get_input("Jira Email", jira_config.get('email'))
        jira_token = get_input("Jira API Token", jira_config.get('token'))

        updated_jira_config = {
            'url': jira_url,
            'email': jira_email,
            'token': jira_token
        }
        if 'status_map' in jira_config:
            updated_jira_config['status_map'] = jira_config['status_map']

        existing_config['jira'] = updated_jira_config
    elif 'jira' in existing_config:
        del existing_config['jira']

    # --- GitHub Configuration ---
    print("\n--- GitHub Integration (optional) ---")
    github_token = get_input("GitHub Personal Access Token", existing_config.get('github_token'))
    github_host = get_input("GitHub Host (e.g., github.my-company.com for Enterprise)", existing_config.get('github_host'))

    if github_token:
        existing_config['github_token'] = github_token
    if github_host:
        existing_config['github_host'] = github_host

    # --- Notifications ---
    print("\n--- Notifications (optional) ---")
    slack_url = get_input("Slack Webhook URL", existing_config.get('slack_webhook_url'))
    discord_url = get_input("Discord Webhook URL", existing_config.get('discord_webhook_url'))
    telegram_token = get_input("Telegram Bot Token", existing_config.get('telegram_bot_token'))
    telegram_chat_id = get_input("Telegram Chat ID", existing_config.get('telegram_chat_id'))

    if slack_url:
        existing_config['slack_webhook_url'] = slack_url
    if discord_url:
        existing_config['discord_webhook_url'] = discord_url
    if telegram_token:
        existing_config['telegram_bot_token'] = telegram_token
    if telegram_chat_id:
        existing_config['telegram_chat_id'] = telegram_chat_id

    # Clean up empty keys
    final_config = {k: v for k, v in existing_config.items() if v}

    # --- Save Configuration ---
    try:
        with open(config_path, 'w') as f:
            yaml.dump(final_config, f, sort_keys=False, indent=2)
        # Set file permissions to 600 (owner read/write only) to protect secrets
        os.chmod(config_path, 0o600)
        print(f"\n✅ Configuration saved successfully to {config_path}")
    except Exception as e:
        print(f"\n❌ Error saving configuration: {e}")


def run_prune(args):
    """
    Identifies and removes unused code and dependencies.
    """
    from shared.prune import PruneManager

    project_dir = args.project_dir.resolve()
    print(f"--- Project Prune (Cleanup) in: {project_dir} ---")

    manager = PruneManager(project_dir)

    types = []
    if args.types:
        types = [t.strip() for t in args.types.split(",")]

    manager.prune_interactive(dry_run=args.dry_run, yes=args.yes, types=types)
    sys.exit(0)


def run_clean(args):
    """Moves or removes agent-generated artifacts from the project directory."""
    import shutil
    from datetime import datetime

    project_dir = args.project_dir.resolve()
    is_force_delete = args.force
    is_archive = args.archive
    is_list = args.list

    # Determine action and destination
    if is_list:
        action_desc = "Listing"
    elif is_force_delete:
        action_desc = "Permanently DELETING"
        log_verb = "Cleaning"
        dest_base_dir_name = None
        dest_dir_prefix = None
        completion_message = "\n✅ Clean complete."
    elif is_archive:
        action_desc = "Archiving"
        log_verb = "Archiving"
        dest_base_dir_name = ".agent_archives"
        dest_dir_prefix = "archive"
        completion_message = "\n✅ Archive complete. Artifacts moved to {dest_dir_display_path}"
    else:  # Default is trash
        action_desc = "Moving to trash"
        log_verb = "Trashing"
        dest_base_dir_name = ".agent_trash"
        dest_dir_prefix = "trash"
        completion_message = "\n✅ Trash complete. Artifacts moved to {dest_dir_display_path}"

    print(f"--- {action_desc} artifacts in project directory: {project_dir} ---")

    # List of agent-generated files and directories to be cleaned
    artifacts_to_clean = [
        ".agent_db.sqlite",
        "COMPLETED",
        "QA_PASSED",
        "PROJECT_SIGNED_OFF",
        "feature_list.json",
        "qa_summary.txt",
        "reviewer_report.txt",
        "cleanup_report.txt",
        "final_metrics.txt",
        "temp_files.txt",
        "dashboard_state.json",
        "worktrees/",  # Directory
    ]

    # Find artifacts in the project directory
    existing_artifacts = []
    for artifact in artifacts_to_clean:
        path = project_dir / artifact
        if path.exists():
            existing_artifacts.append(path)

    # Also include the log file from the last run
    run_id_file = project_dir / ".agent_run_id"
    log_file_path = None
    if run_id_file.exists():
        run_id = run_id_file.read_text().strip()
        repo_root = Path(__file__).parent
        log_file_path = repo_root / f"agents/logs/{run_id}.log"
        if log_file_path.exists():
            # Add the log file to be cleaned
            existing_artifacts.append(log_file_path)

    if not existing_artifacts:
        print("No agent-generated artifacts found to clean.")
        sys.exit(0)

    # If --list is used, just print the files and exit
    if is_list:
        print("The following agent-generated artifacts would be cleaned:")
        for path in existing_artifacts:
            try:
                display_path = path.relative_to(project_dir)
            except ValueError:
                repo_root = Path(__file__).parent
                try:
                    display_path = f"(from repo root) {path.relative_to(repo_root)}"
                except ValueError:
                    display_path = path
            print(f"  - {display_path}")
        sys.exit(0)

    # Prepare destination directory path if needed
    dest_dir = None
    dest_dir_display_path = None
    if not is_force_delete:
        dest_base_dir = project_dir / dest_base_dir_name
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        dest_dir = dest_base_dir / f"{dest_dir_prefix}-{timestamp}"
        dest_dir_display_path = dest_dir.relative_to(project_dir)

    action_verb = "permanently DELETED" if is_force_delete else f"MOVED to {dest_dir_display_path}"
    print(f"The following agent-generated files and directories will be {action_verb}:")
    for path in existing_artifacts:
        try:
            display_path = path.relative_to(project_dir)
        except ValueError:
            # The path is not inside the project directory (e.g., agent log file)
            repo_root = Path(__file__).parent
            try:
                display_path = f"(from repo root) {path.relative_to(repo_root)}"
            except ValueError:
                display_path = path  # Absolute path as a fallback
        print(f"  - {display_path}")

    if not args.yes:
        confirm = input("\nAre you sure you want to proceed? [y/N]: ").strip().lower()
        if confirm != 'y':
            print("Aborted.")
            sys.exit(0)

    print(f"\n{log_verb} artifacts...")

    # Create destination directory now that we have confirmation
    if not is_force_delete and dest_dir:
        dest_dir.mkdir(parents=True, exist_ok=True)

    for path in existing_artifacts:
        try:
            if is_force_delete:
                if path.is_file():
                    path.unlink()
                    print(f"Deleted file: {path.relative_to(project_dir)}")
                elif path.is_dir():
                    shutil.rmtree(path)
                    print(f"Deleted directory: {path.relative_to(project_dir)}")
            else:
                dest = dest_dir / path.name
                shutil.move(str(path), str(dest))
                print(f"Moved to {dest_dir_prefix}: {path.relative_to(project_dir)}")
        except OSError as e:
            print(f"Error processing {path}: {e}", file=sys.stderr)

    if not is_force_delete:
        print(completion_message.format(dest_dir_display_path=dest_dir.relative_to(project_dir)))
    else:
        print(completion_message)
    sys.exit(0)


def run_archive(args):
    """Archives agent-generated artifacts to a timestamped directory."""
    print("Warning: The 'archive' command is deprecated and will be removed in a future version. "
          "Use 'clean --archive' instead.", file=sys.stderr)
    import shutil
    from datetime import datetime

    project_dir = args.project_dir.resolve()
    print(f"--- Archiving artifacts in project directory: {project_dir} ---")

    # List of agent-generated files and directories to be archived
    artifacts_to_archive = [
        ".agent_db.sqlite",
        "COMPLETED",
        "QA_PASSED",
        "PROJECT_SIGNED_OFF",
        "feature_list.json",
        "qa_summary.txt",
        "reviewer_report.txt",
        "cleanup_report.txt",
        "final_metrics.txt",
        "temp_files.txt",
        "dashboard_state.json",
        "worktrees/",  # Directory
    ]

    existing_artifacts = []
    for artifact in artifacts_to_archive:
        path = project_dir / artifact
        if path.exists():
            existing_artifacts.append(path)

    if not existing_artifacts:
        print("No agent-generated artifacts found to archive.")
        sys.exit(0)

    # Create archive directory
    archive_base_dir = project_dir / ".agent_archives"
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    archive_dir = archive_base_dir / f"archive-{timestamp}"
    archive_dir.mkdir(parents=True, exist_ok=True)

    print(f"Archiving to: {archive_dir}")

    for path in existing_artifacts:
        try:
            dest = archive_dir / path.name
            shutil.move(str(path), str(dest))
            print(f"Archived: {path.relative_to(project_dir)}")
        except OSError as e:
            print(f"Error archiving {path}: {e}", file=sys.stderr)

    print(f"\n✅ Archiving complete. Artifacts moved to {archive_dir.relative_to(project_dir)}")
    sys.exit(0)


def _snapshot_create(args):
    """Helper function to create a snapshot."""
    import shutil
    from datetime import datetime

    project_dir = args.project_dir.resolve()
    snapshot_name = args.name
    archive_base_dir = project_dir / ".agent_archives"

    # Define the name of the snapshot directory
    if snapshot_name:
        snapshot_dir_name = snapshot_name
    else:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        snapshot_dir_name = f"snapshot-{timestamp}"

    snapshot_dir = archive_base_dir / snapshot_dir_name

    print(f"--- Creating snapshot of artifacts in: {project_dir} ---")

    # List of key agent-generated files to be snapshotted
    artifacts_to_snapshot = [
        "feature_list.json",
        "qa_summary.txt",
        "reviewer_report.txt",
        "final_metrics.txt",
        "dashboard_state.json",
    ]

    # Find artifacts that actually exist in the project directory
    existing_artifacts = []
    for artifact in artifacts_to_snapshot:
        path = project_dir / artifact
        if path.exists():
            existing_artifacts.append(path)

    # Also include the log file from the last run, if it exists
    run_id_file = project_dir / ".agent_run_id"
    if run_id_file.exists():
        run_id = run_id_file.read_text().strip()
        repo_root = Path(__file__).parent
        log_file_path = repo_root / f"agents/logs/{run_id}.log"
        if log_file_path.exists():
            existing_artifacts.append(log_file_path)

    if not existing_artifacts:
        print("No key agent-generated artifacts found to snapshot.")
        sys.exit(0)

    if snapshot_dir.exists():
        print(f"❌ Error: A snapshot named '{snapshot_dir_name}' already exists in .agent_archives.")
        print("Please choose a different name or remove the existing one.")
        sys.exit(1)

    print(f"Snapshot will be saved to: .agent_archives/{snapshot_dir_name}")
    print("The following artifacts will be copied:")
    for path in existing_artifacts:
        try:
            display_path = path.relative_to(project_dir)
        except ValueError:
            repo_root = Path(__file__).parent
            display_path = f"(from repo root) {path.relative_to(repo_root)}"
        print(f"  - {display_path}")

    if not args.yes:
        confirm = input("\nAre you sure you want to proceed? [y/N]: ").strip().lower()
        if confirm != 'y':
            print("Aborted.")
            sys.exit(0)

    print("\nCreating snapshot...")
    try:
        archive_base_dir.mkdir(exist_ok=True)
        snapshot_dir.mkdir()

        for path in existing_artifacts:
            dest = snapshot_dir / path.name
            if path.is_file():
                shutil.copy2(path, dest)
            elif path.is_dir():
                shutil.copytree(path, dest)
        print(f"Copied {len(existing_artifacts)} artifact(s).")

    except OSError as e:
        print(f"❌ Error creating snapshot: {e}", file=sys.stderr)
        if snapshot_dir.exists():
            shutil.rmtree(snapshot_dir)
        sys.exit(1)

    print(f"\n✅ Snapshot '{snapshot_dir_name}' created successfully.")
    sys.exit(0)


def _snapshot_diff(args):
    """Helper function to diff a snapshot against the current project state."""
    project_dir = args.project_dir.resolve()
    snapshot_name = args.name
    archive_base_dir = project_dir / ".agent_archives"
    snapshot_dir = archive_base_dir / snapshot_name

    if not snapshot_name:
        print("❌ Error: 'snapshot diff' requires a snapshot name.", file=sys.stderr)
        sys.exit(1)

    if not snapshot_dir.is_dir():
        print(f"❌ Error: Snapshot '{snapshot_name}' not found in '{archive_base_dir}'.", file=sys.stderr)
        sys.exit(1)

    git_path = shutil.which("git")
    if not git_path:
        print("❌ Error: 'git' command not found. Diff functionality requires Git.", file=sys.stderr)
        sys.exit(1)

    print(f"--- Diffing current project against snapshot: {snapshot_name} ---")

    try:
        # Using --no-index to compare paths on the filesystem directly
        # --ignore-cr-at-eol helps with cross-platform line ending differences
        # --ignore-space-change ignores changes in the amount of whitespace
        cmd = [
            git_path, "diff", "--no-index", "--color=always",
            "--ignore-cr-at-eol", "--ignore-space-change",
            str(snapshot_dir), str(project_dir)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)

        # git diff exits with 1 if there are differences, 0 if not.
        if result.returncode == 0:
            print("✅ No differences found.")
        else:
            print(result.stdout)
            # You can also print stderr if you want to see potential git warnings/errors
            if result.stderr:
                print("\n--- Git Errors/Warnings ---", file=sys.stderr)
                print(result.stderr, file=sys.stderr)

    except Exception as e:
        print(f"❌ An unexpected error occurred during diff: {e}", file=sys.stderr)
        sys.exit(1)

    sys.exit(0)


def run_snapshot(args):
    """Dispatches snapshot actions."""
    if args.action == "create":
        _snapshot_create(args)
    elif args.action == "diff":
        _snapshot_diff(args)


def _artifacts_list(base_dir, mode):
    """Generic helper function to list archives or trash."""
    title = "Archives" if mode == 'archive' else "Trash"
    print(f"--- {title} in: {base_dir} ---")
    try:
        archives = sorted([d for d in base_dir.iterdir() if d.is_dir()], reverse=True)
    except OSError as e:
        print(f"Error reading {mode} directory: {e}", file=sys.stderr)
        sys.exit(1)

    if not archives:
        print(f"{mode.capitalize()} is empty.")
        sys.exit(0)

    for i, archive_dir in enumerate(archives):
        latest_marker = " (latest)" if i == 0 else ""
        print(f"\n[{i+1}] {archive_dir.name}{latest_marker}")
        try:
            contents = list(archive_dir.iterdir())
            if not contents:
                print("    (empty)")
            else:
                # Always list all contents first
                for item in contents:
                    is_dir = "/ (dir)" if item.is_dir() else ""
                    print(f"    - {item.name}{is_dir}")

                # If a log file exists, show a summary
                log_file = next((item for item in contents if item.suffix == '.log'), None)
                if log_file:
                    print("    --- Log Summary (last 15 lines) ---")
                    try:
                        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                            for line in lines[-15:]:
                                stripped_line = line.strip()
                                if stripped_line:
                                    print(f"      {stripped_line}")
                    except Exception as e:
                        print(f"      [Error reading log summary: {e}]")
        except OSError as e:
            print(f"    Error reading archive contents: {e}", file=sys.stderr)
    sys.exit(0)


def _artifacts_restore(args, base_dir, mode):
    """Generic helper function to restore from trash or an archive."""
    import shutil
    project_dir = args.project_dir.resolve()
    print(f"--- Restoring from {mode} in: {project_dir} ---")
    archive_to_restore = None
    try:
        archives = sorted([d for d in base_dir.iterdir() if d.is_dir()], reverse=True)
        if not archives:
            print(f"{mode.capitalize()} is empty. Nothing to restore.")
            sys.exit(0)

        if args.archive_name:
            target_path = base_dir / args.archive_name
            if not target_path.is_dir():
                print(f"❌ Error: {mode.capitalize()} '{args.archive_name}' not found.")
                sys.exit(1)
            archive_to_restore = target_path
        else:
            print(f"Please select a {mode} archive to restore:")
            for i, archive_dir in enumerate(archives):
                print(f"  [{i+1}] {archive_dir.name}")

            while True:
                try:
                    selection = input(f"Enter number (1-{len(archives)}): ").strip()
                    if not selection:
                        print("Aborted.")
                        sys.exit(0)
                    choice_index = int(selection) - 1
                    if 0 <= choice_index < len(archives):
                        archive_to_restore = archives[choice_index]
                        break
                    else:
                        print("Invalid selection. Please try again.")
                except ValueError:
                    print("Invalid input. Please enter a number.")
                except (EOFError, KeyboardInterrupt):
                    print("\nAborted.")
                    sys.exit(0)

    except (OSError, ValueError) as e:
        print(f"Error accessing {mode} archives: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Found archive to restore: {archive_to_restore.name}")

    artifacts = list(archive_to_restore.iterdir())
    if not artifacts:
        print("Archive is empty. Nothing to restore.")
        if mode == 'trash':
            archive_to_restore.rmdir()
            print(f"Removed empty archive: {archive_to_restore.name}")
        sys.exit(0)

    conflicts = [p.name for p in artifacts if (project_dir / p.name).exists()]
    if conflicts:
        print("\n❌ Error: The following files already exist in the project directory:", file=sys.stderr)
        for f in conflicts:
            print(f"  - {f}", file=sys.stderr)
        print("Please move or delete these conflicting files before running restore.", file=sys.stderr)
        sys.exit(1)

    restore_verb = "restored" if mode == 'trash' else "restored (copied)"
    print(f"\nThe following artifacts will be {restore_verb}:")
    for artifact in artifacts:
        print(f"  - {artifact.name}")

    if args.dry_run:
        print("\n-- DRY RUN --")
        print("The following actions would be taken:")
        action_verb = "MOVE" if mode == 'trash' else "COPY"
        for artifact in artifacts:
            print(f"  - {action_verb}: {artifact.name} from {mode} to project directory")
        if mode == 'trash':
            print(f"  - DELETE: Empty archive '{archive_to_restore.name}'")
        print("\nNo changes were made.")
        sys.exit(0)

    if not args.yes:
        confirm = input("\nAre you sure you want to proceed? [y/N]: ").strip().lower()
        if confirm != 'y':
            print("Aborted.")
            sys.exit(0)

    print("\nRestoring artifacts...")
    try:
        for artifact in artifacts:
            dest = project_dir / artifact.name
            if mode == 'trash':
                shutil.move(str(artifact), str(dest))
            else:  # archive mode
                if artifact.is_dir():
                    shutil.copytree(str(artifact), str(dest))
                else:
                    shutil.copy2(str(artifact), str(dest))
            print(f"Restored: {artifact.name}")
        if mode == 'trash':
            archive_to_restore.rmdir()
            print(f"Removed empty archive: {archive_to_restore.name}")
    except OSError as e:
        print(f"Error during restore: {e}", file=sys.stderr)
        sys.exit(1)

    if mode == 'trash':
        print("\n✅ Restore complete.")
    else:
        print("\n✅ Restore complete. Original archive remains untouched.")
    sys.exit(0)


def _artifacts_clear(args, base_dir, mode):
    """Generic helper function to clear trash or archives."""
    import shutil
    project_dir = args.project_dir.resolve()
    print(f"--- Clearing {mode} in: {project_dir} ---")
    if args.all:
        if args.dry_run:
            print("\n-- DRY RUN --")
            print(f"Would permanently delete the entire '{base_dir.name}' directory and all its contents.")
            print("\nNo changes were made.")
            sys.exit(0)
        if not args.yes:
            print(f"This will permanently delete the entire '{base_dir.name}' directory and all its contents.")
            confirm = input("Are you sure? [y/N]: ").strip().lower()
            if confirm != 'y':
                print("Aborted.")
                sys.exit(0)
        try:
            shutil.rmtree(base_dir)
            print(f"✅ {mode.capitalize()} successfully emptied.")
        except OSError as e:
            print(f"Error emptying {mode}: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.archive_name:
        target_path = base_dir / args.archive_name
        if not target_path.is_dir():
            print(f"❌ Error: Archive '{args.archive_name}' not found.")
            sys.exit(1)

        if args.dry_run:
            print("\n-- DRY RUN --")
            print(f"Would permanently delete the archive: {args.archive_name}")
            print("\nNo changes were made.")
            sys.exit(0)
        if not args.yes:
            print(f"This will permanently delete the archive: {args.archive_name}")
            confirm = input("Are you sure? [y/N]: ").strip().lower()
            if confirm != 'y':
                print("Aborted.")
                sys.exit(0)
        try:
            shutil.rmtree(target_path)
            print(f"✅ Archive '{args.archive_name}' deleted.")
        except OSError as e:
            print(f"Error deleting archive: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("Error: 'clear' action requires either an archive name or the --all flag.")
        sys.exit(1)
    sys.exit(0)


def _artifacts_inspect(args, base_dir, mode):
    """Generic helper function to inspect trash or archives."""
    if not args.archive_name:
        print(f"❌ Error: 'inspect' action requires an archive name.", file=sys.stderr)
        sys.exit(1)

    archive_dir = base_dir / args.archive_name
    if not archive_dir.is_dir():
        print(f"❌ Error: Archive '{args.archive_name}' not found in {mode}.", file=sys.stderr)
        sys.exit(1)

    # Inspecting a specific file
    if args.file_name:
        file_path = archive_dir / args.file_name
        if not file_path.exists():
            print(f"❌ Error: File '{args.file_name}' not found in archive '{args.archive_name}'.", file=sys.stderr)
            sys.exit(1)
        if file_path.is_dir():
            print(f"❌ Error: '{args.file_name}' is a directory. Cannot inspect directories.", file=sys.stderr)
            sys.exit(1)

        print(f"--- Contents of {args.file_name} from {args.archive_name} ---")
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                print(f.read())
        except Exception as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            sys.exit(1)

    # Inspecting the whole archive (summary)
    else:
        print(f"--- Inspecting Archive: {archive_dir.name} ---")
        try:
            contents = sorted(list(archive_dir.iterdir()))
            if not contents:
                print("(empty)")
                sys.exit(0)

            for item in contents:
                print(f"\n--- File: {item.name} ---")
                if item.is_dir():
                    print("    (Directory)")
                    continue
                try:
                    with open(item, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = []
                        try:
                            for _ in range(10):
                                lines.append(next(f))
                        except StopIteration:
                            pass  # File has fewer than 10 lines, which is fine.

                        for line in lines:
                            print(f"    {line.strip()}")

                        # Check if there are more lines by trying to read one more.
                        try:
                            next(f)
                            print("    ...")
                        except StopIteration:
                            pass  # End of file, no more lines.
                except Exception:
                    print("    (Could not display preview - possibly a binary file)")

        except OSError as e:
            print(f"Error reading archive contents: {e}", file=sys.stderr)
            sys.exit(1)
    sys.exit(0)


def _artifacts_diff(args, base_dir, mode):
    """Generic helper function to diff a file in trash/archive with the project version."""
    import difflib

    project_dir = args.project_dir.resolve()
    archive_name = args.archive_name
    file_name = args.file_name

    if not archive_name or not file_name:
        print("❌ Error: 'diff' action requires an archive name and a file name.", file=sys.stderr)
        sys.exit(1)

    archive_dir = base_dir / archive_name
    if not archive_dir.is_dir():
        print(f"❌ Error: Archive '{archive_name}' not found in {mode}.", file=sys.stderr)
        sys.exit(1)

    stored_file_path = archive_dir / file_name
    if not stored_file_path.is_file():
        print(f"❌ Error: File '{file_name}' not found in archive '{archive_name}'.", file=sys.stderr)
        sys.exit(1)

    project_file_path = project_dir / file_name

    try:
        with open(stored_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            stored_lines = f.readlines()
    except Exception as e:
        print(f"Error reading {mode}d file: {e}", file=sys.stderr)
        sys.exit(1)

    if project_file_path.exists():
        try:
            with open(project_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                project_lines = f.readlines()
            from_file = f"a/{file_name}"
            to_file = f"b/{file_name}"
        except Exception as e:
            print(f"Error reading project file: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        project_lines = []
        from_file = f"a/{file_name}"
        to_file = f"b/{file_name} (deleted)"

    diff = list(difflib.unified_diff(
        project_lines,
        stored_lines,
        fromfile=from_file,
        tofile=to_file,
    ))

    if not diff:
        print(f"✅ No differences found between the project version and the {mode}d version of '{file_name}'.")
        sys.exit(0)

    print(f"--- Diff for {file_name} ---")
    print(f"--- a/{file_name} (Project Version)")
    print(f"+++ b/{file_name} ({mode.capitalize()}d Version in {archive_name})")
    for line in diff[2:]:
        print(line, end="")

    sys.exit(0)

def run_tour(args):
    """Manages interactive code tours."""
    from shared.tour import TourManager
    from rich.console import Console
    from rich.syntax import Syntax
    from rich.panel import Panel
    from rich.prompt import Prompt

    project_dir = args.project_dir.resolve()
    manager = TourManager(project_dir)
    console = Console()

    if args.action == "list":
        tours = manager.list_tours()
        if not tours:
            print("No tours found.")
        else:
            print("--- Available Tours ---")
            for t in tours:
                print(f"  - {t}")
        sys.exit(0)

    elif args.action == "create":
        if not args.name:
            print("Error: Name required.", file=sys.stderr)
            sys.exit(1)
        try:
            manager.create_tour(args.name)
            print(f"✅ Created tour '{args.name}'")
            print("Use 'tour add-step' to add steps.")
        except Exception as e:
            print(f"❌ Error creating tour: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "delete":
        if not args.name:
            print("Error: Name required.", file=sys.stderr)
            sys.exit(1)
        if manager.delete_tour(args.name):
            print(f"✅ Deleted tour '{args.name}'")
        else:
            print(f"❌ Tour '{args.name}' not found.", file=sys.stderr)
            sys.exit(1)

    elif args.action == "add-step":
        if not args.name or not args.file or not args.line:
            print("Error: Name, file, and line required.", file=sys.stderr)
            sys.exit(1)

        desc = args.description or input("Description: ")
        try:
            manager.add_step(args.name, args.file, args.line, desc)
            print(f"✅ Added step to tour '{args.name}'")
        except Exception as e:
            print(f"❌ Error adding step: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "play":
        if not args.name:
            print("Error: Name required.", file=sys.stderr)
            sys.exit(1)

        tour = manager.get_tour(args.name)
        if not tour:
            print(f"❌ Tour '{args.name}' not found.", file=sys.stderr)
            sys.exit(1)

        steps = tour.steps
        if not steps:
            print("Tour has no steps.")
            sys.exit(0)

        idx = 0
        while 0 <= idx < len(steps):
            step = steps[idx]
            console.clear()
            console.print(f"[bold magenta]Tour: {tour.title} ({idx+1}/{len(steps)})[/bold magenta]")
            console.print(f"[bold cyan]File:[/bold cyan] {step.file}:{step.line}")
            console.print(Panel(step.description, title="Description", border_style="green"))

            file_path = project_dir / step.file
            if file_path.exists():
                try:
                    content = file_path.read_text(encoding="utf-8")
                    # simple logic to show context around the line
                    lines = content.splitlines()
                    start_line = max(0, step.line - 5)
                    end_line = min(len(lines), step.line + 5)
                    context_code = "\n".join(lines[start_line:end_line])

                    syntax = Syntax(context_code, "python", theme="monokai", line_numbers=True, start_line=start_line+1, highlight_lines={step.line})
                    console.print(syntax)
                except Exception as e:
                    console.print(f"[red]Error reading file: {e}[/red]")
            else:
                console.print(f"[red]File not found: {step.file}[/red]")

            print("\n")
            choice = Prompt.ask("Navigate", choices=["n", "p", "q"], default="n")

            if choice == "n":
                idx += 1
            elif choice == "p":
                idx -= 1
            elif choice == "q":
                break

        console.clear()
        print("Tour finished.")

    sys.exit(0)

def run_artifacts(args, mode):
    """Manages agent artifacts (trash or archives)."""
    project_dir = args.project_dir.resolve()
    base_dir_name = ".agent_trash" if mode == 'trash' else ".agent_archives"
    base_dir = project_dir / base_dir_name

    if not base_dir.exists() or not base_dir.is_dir():
        print(f"{mode.capitalize()} directory ({base_dir_name}) not found. Nothing to do.")
        sys.exit(0)

    # Convert the Namespace object to a dictionary for easier handling
    args_dict = vars(args)

    if args.action == "list":
        _artifacts_list(base_dir, mode)
    elif args.action == "restore":
        _artifacts_restore(args, base_dir, mode)
    elif args.action == "clear":
        _artifacts_clear(args, base_dir, mode)
    elif args.action == "inspect":
        _artifacts_inspect(args, base_dir, mode)
    elif args.action == "diff":
        _artifacts_diff(args, base_dir, mode)

def run_archives(args):
    """Manages the agent archives directory."""
    print("Warning: The 'archives' command is deprecated. Use 'artifacts archive <action>' instead.", file=sys.stderr)
    # Re-package args for the new command structure
    new_args = argparse.Namespace(
        type='archive',
        action=args.action,
        archive_name=args.archive_name,
        file_name=args.file_name,
        project_dir=args.project_dir,
        all=args.all,
        yes=args.yes,
        dry_run=args.dry_run
    )
    run_artifacts(new_args, mode='archive')

def run_revert(args):
    """Discards uncommitted changes for specified files or for the entire repository."""
    import subprocess
    import shutil
    project_dir = args.project_dir.resolve()

    # --- Pre-flight checks ---
    git_path = shutil.which("git")
    if not git_path:
        print("❌ Error: 'git' command not found. Please ensure Git is installed and in your PATH.", file=sys.stderr)
        sys.exit(1)

    git_dir = project_dir / ".git"
    if not git_dir.exists() or not git_dir.is_dir():
        print("❌ Error: Not a git repository. Cannot revert.", file=sys.stderr)
        sys.exit(1)

    # Validate arguments
    if args.files and args.interactive:
        print("❌ Error: Cannot use --interactive mode when specifying individual files.", file=sys.stderr)
        sys.exit(1)

    files_to_revert = args.files

    # --- Mode 1: Interactive Revert ---
    if args.interactive:
        print(f"--- Interactive Revert in: {project_dir} ---")
        try:
            status_result = subprocess.run(
                [git_path, "-C", str(project_dir), "status", "--porcelain"],
                capture_output=True, text=True, check=True
            )
            changes = [line for line in status_result.stdout.splitlines() if line]
            if not changes:
                print("✅ No uncommitted changes to revert.")
                sys.exit(0)

            print("Select files to revert (e.g., 1 3 4), or press Enter to cancel:")
            all_files = []
            for i, change in enumerate(changes):
                status, filename = change[:2], change[3:]
                all_files.append(filename)
                print(f"  [{i+1}] {status.strip()}: {filename}")

            selection = input("> ").strip()
            if not selection:
                print("Aborted.")
                sys.exit(0)

            try:
                indices = [int(i) - 1 for i in selection.split()]
                files_to_revert = [all_files[i] for i in indices if 0 <= i < len(all_files)]
            except ValueError:
                print("❌ Invalid input. Please enter numbers separated by spaces.", file=sys.stderr)
                sys.exit(1)

            if not files_to_revert:
                print("No valid files selected. Aborting.")
                sys.exit(0)

        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"❌ Error checking git status: {e}", file=sys.stderr)
            sys.exit(1)
        except (EOFError, KeyboardInterrupt):
            print("\nAborted.")
            sys.exit(0)

    # --- Mode 2: Revert specific files (also used by interactive mode) ---
    if files_to_revert:
        print(f"--- Reverting specified files in: {project_dir} ---")

        # Get the status of all files in the repo to identify untracked files
        status_result = subprocess.run(
            [git_path, "-C", str(project_dir), "status", "--porcelain"],
            capture_output=True, text=True, check=True
        )
        all_untracked_files = {
            line[3:] for line in status_result.stdout.strip().split('\n') if line.startswith('??')
        }

        # Separate the user's list into files that are tracked vs. untracked
        tracked_to_revert = [f for f in files_to_revert if f not in all_untracked_files]
        untracked_to_revert = [f for f in files_to_revert if f in all_untracked_files]

        # Get the status of only the files the user wants to revert to confirm there are changes
        final_revert_list = []
        if files_to_revert:
            status_of_selection = subprocess.run(
                [git_path, "-C", str(project_dir), "status", "--porcelain", "--"] + files_to_revert,
                capture_output=True, text=True
            )
            final_revert_list = [line[3:] for line in status_of_selection.stdout.strip().split('\n') if line.strip()]

        if not final_revert_list:
            print("✅ No uncommitted changes to revert for the specified files.")
            sys.exit(0)

        print("\nThe following files will be reverted to their last committed state:")
        for f in final_revert_list:
            print(f"  - {f}")

        if not args.yes:
            confirm = input("\nAre you sure you want to proceed? [y/N]: ").strip().lower()
            if confirm != 'y':
                print("Aborted.")
                sys.exit(0)

        print("\nReverting files...")
        try:
            if tracked_to_revert:
                cmd = [git_path, "-C", str(project_dir), "checkout", "HEAD", "--"] + tracked_to_revert
                subprocess.run(cmd, check=True, capture_output=True)

            if untracked_to_revert:
                cmd = [git_path, "-C", str(project_dir), "clean", "-f", "--"] + untracked_to_revert
                subprocess.run(cmd, check=True, capture_output=True)

            print("✅ Specified files have been reverted.")
        except subprocess.CalledProcessError as e:
            stderr = e.stderr.decode().strip() if e.stderr else str(e)
            print(f"❌ Error during revert: {stderr}", file=sys.stderr)
            sys.exit(1)

    # --- Mode 3: Revert all changes (if no files and no interactive) ---
    elif not args.interactive:
        print(f"--- Reverting ALL uncommitted changes in: {project_dir} ---")
        try:
            status_result = subprocess.run(
                [git_path, "-C", str(project_dir), "status", "--porcelain"],
                capture_output=True, text=True, check=True
            )
            if not status_result.stdout.strip():
                print("  ✅ No uncommitted changes to revert.")
                sys.exit(0)

            print("\nUncommitted changes (will be discarded):")
            for line in status_result.stdout.strip().split('\n'):
                print(f"  {line}")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"❌ Error checking git status: {e}", file=sys.stderr)
            sys.exit(1)

        if not args.yes:
            confirm = input("\nAre you sure you want to discard ALL uncommitted changes? [y/N]: ").strip().lower()
            if confirm != 'y':
                print("Aborted.")
                sys.exit(0)

        print("\nReverting changes...")
        try:
            subprocess.run(
                [git_path, "-C", str(project_dir), "reset", "--hard", "HEAD"],
                check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            subprocess.run(
                [git_path, "-C", str(project_dir), "clean", "-fd"],
                check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            print("✅ Revert complete. Working directory is now clean.")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            stderr = getattr(e, 'stderr', str(e))
            if isinstance(stderr, bytes):
                stderr = stderr.decode().strip()
            print(f"❌ Error during revert: {stderr}", file=sys.stderr)
            sys.exit(1)

    sys.exit(0)


def run_trash(args):
    """Manages the agent trash directory."""
    print("Warning: The 'trash' command is deprecated. Use 'artifacts trash <action>' instead.", file=sys.stderr)
    run_artifacts(args, mode='trash')


def _discard_interactive(project_dir, git_path):
    """Handles the interactive discard logic."""
    print(f"--- Interactive Discard in: {project_dir} ---")
    try:
        status_result = subprocess.run(
            [git_path, "-C", str(project_dir), "status", "--porcelain"],
            capture_output=True, text=True, check=True
        )
        changes = [line for line in status_result.stdout.splitlines() if line]
        if not changes:
            print("✅ No uncommitted changes to discard.")
            sys.exit(0)

        print("Select files to discard (e.g., 1 3 4), or press Enter to cancel:")
        all_files = []
        for i, change in enumerate(changes):
            status, filename = change[:2], change[3:]
            all_files.append(filename)
            print(f"  [{i+1}] {status.strip()}: {filename}")

        selection = input("> ").strip()
        if not selection:
            print("Aborted.")
            sys.exit(0)

        try:
            indices = [int(i) - 1 for i in selection.split()]
            files_to_discard = [all_files[i] for i in indices if 0 <= i < len(all_files)]
            if not files_to_discard:
                print("No valid files selected. Aborting.")
                sys.exit(0)
            return files_to_discard
        except ValueError:
            print("❌ Invalid input. Please enter numbers separated by spaces.", file=sys.stderr)
            sys.exit(1)

    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"❌ Error checking git status: {e}", file=sys.stderr)
        sys.exit(1)
    except (EOFError, KeyboardInterrupt):
        print("\nAborted.")
        sys.exit(0)
    return []


def _discard_files(project_dir, git_path, files_to_discard, yes=False):
    """Handles discarding a specific list of files."""
    print(f"--- Discarding specified files in: {project_dir} ---")
    status_result = subprocess.run(
        [git_path, "-C", str(project_dir), "status", "--porcelain"],
        capture_output=True, text=True, check=True
    )
    all_untracked_files = {
        line[3:] for line in status_result.stdout.strip().split('\n') if line.startswith('??')
    }

    tracked_to_discard = [f for f in files_to_discard if f not in all_untracked_files]
    untracked_to_discard = [f for f in files_to_discard if f in all_untracked_files]

    status_of_selection = subprocess.run(
        [git_path, "-C", str(project_dir), "status", "--porcelain", "--"] + files_to_discard,
        capture_output=True, text=True
    )
    final_discard_list = [line[3:] for line in status_of_selection.stdout.strip().split('\n') if line.strip()]

    if not final_discard_list:
        print("✅ No uncommitted changes to discard for the specified files.")
        sys.exit(0)

    print("\nThe following files will be discarded:")
    for f in final_discard_list:
        print(f"  - {f}")

    if not yes:
        confirm = input("\nAre you sure you want to proceed? [y/N]: ").strip().lower()
        if confirm != 'y':
            print("Aborted.")
            sys.exit(0)

    print("\nDiscarding files...")
    try:
        if tracked_to_discard:
            cmd = [git_path, "-C", str(project_dir), "checkout", "HEAD", "--"] + tracked_to_discard
            subprocess.run(cmd, check=True, capture_output=True)
        if untracked_to_discard:
            cmd = [git_path, "-C", str(project_dir), "clean", "-f", "--"] + untracked_to_discard
            subprocess.run(cmd, check=True, capture_output=True)
        print("✅ Specified files have been discarded.")
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.decode().strip() if e.stderr else str(e)
        print(f"❌ Error during discard: {stderr}", file=sys.stderr)
        sys.exit(1)


def _discard_all(project_dir, git_path, yes=False):
    """Handles discarding all uncommitted changes."""
    print(f"--- Discarding ALL uncommitted changes in: {project_dir} ---")
    try:
        status_result = subprocess.run(
            [git_path, "-C", str(project_dir), "status", "--porcelain"],
            capture_output=True, text=True, check=True
        )
        if not status_result.stdout.strip():
            print("  ✅ No uncommitted changes to discard.")
            sys.exit(0)

        print("\nUncommitted changes (will be discarded):")
        for line in status_result.stdout.strip().split('\n'):
            print(f"  {line}")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"❌ Error checking git status: {e}", file=sys.stderr)
        sys.exit(1)

    if not yes:
        confirm = input("\nAre you sure you want to discard ALL uncommitted changes? [y/N]: ").strip().lower()
        if confirm != 'y':
            print("Aborted.")
            sys.exit(0)

    # Stash changes before discarding to allow for recovery
    print("\nStashing changes before discarding...")
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        stash_message = f"agent-discard-stash-{timestamp}"
        # Use -u to include untracked files
        subprocess.run(
            [git_path, "-C", str(project_dir), "stash", "push", "-u", "-m", stash_message],
            check=True, capture_output=True, text=True
        )
        print(f"✅ Changes stashed safely. To recover, use the 'undo' command.")
    except subprocess.CalledProcessError as e:
        # It's possible there are no changes to stash if only ignored files are present
        if "No local changes to save" not in e.stderr:
            print(f"❌ Error while stashing changes: {e.stderr}", file=sys.stderr)
            print("Aborting discard to prevent data loss.", file=sys.stderr)
            sys.exit(1)

    print("\nCleaning working directory...")
    try:
        subprocess.run(
            [git_path, "-C", str(project_dir), "reset", "--hard", "HEAD"],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        subprocess.run(
            [git_path, "-C", str(project_dir), "clean", "-fd"],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        print("✅ Discard complete. Working directory is now clean.")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        stderr = getattr(e, 'stderr', str(e))
        if isinstance(stderr, bytes):
            stderr = stderr.decode().strip()
        print(f"❌ Error during discard: {stderr}", file=sys.stderr)
        sys.exit(1)


def run_undo(args):
    """Restores uncommitted changes that were stashed by the 'discard' command."""
    project_dir = args.project_dir.resolve()
    git_path = shutil.which("git")

    if not git_path or not (project_dir / ".git").is_dir():
        print("❌ Error: Not a git repository. Cannot run undo.", file=sys.stderr)
        sys.exit(1)

    print(f"--- Searching for stashed discards in: {project_dir} ---")

    try:
        result = subprocess.run(
            [git_path, "-C", str(project_dir), "stash", "list"],
            capture_output=True, text=True, check=True
        )
        stashes = result.stdout.strip().split('\n')
        discard_stashes = [s for s in stashes if "agent-discard-stash" in s]

        if not discard_stashes:
            print("No stashed discards found to undo.")
            sys.exit(0)

        print("Please select a discard to undo (press Enter to cancel):")
        for i, stash in enumerate(discard_stashes):
            print(f"  [{i+1}] {stash}")

        selection = input("> ").strip()
        if not selection:
            print("Aborted.")
            sys.exit(0)

        choice_index = int(selection) - 1
        if 0 <= choice_index < len(discard_stashes):
            stash_to_apply = discard_stashes[choice_index].split(':')[0]
            print(f"\nRestoring selected stash: {stash_to_apply}...")
            subprocess.run(
                [git_path, "-C", str(project_dir), "stash", "pop", stash_to_apply],
                check=True
            )
            print("✅ Undo complete. Your changes have been restored.")
            sys.exit(0)
        else:
            print("❌ Invalid selection.", file=sys.stderr)
            sys.exit(1)

    except (ValueError, IndexError):
        print("❌ Invalid input. Please enter a valid number.", file=sys.stderr)
        sys.exit(1)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        stderr = getattr(e, 'stderr', str(e))
        print(f"❌ Error during undo process: {stderr}", file=sys.stderr)
        sys.exit(1)
    except (EOFError, KeyboardInterrupt):
        print("\nAborted.")
        sys.exit(0)


def run_discard(args):
    """Discards uncommitted changes for specified files or for the entire repository."""
    project_dir = args.project_dir.resolve()

    git_path = shutil.which("git")
    if not git_path:
        print("❌ Error: 'git' command not found. Please ensure Git is installed and in your PATH.", file=sys.stderr)
        sys.exit(1)

    git_dir = project_dir / ".git"
    if not git_dir.exists() or not git_dir.is_dir():
        print("❌ Error: Not a git repository. Cannot discard changes.", file=sys.stderr)
        sys.exit(1)

    if args.files and args.interactive:
        print("❌ Error: Cannot use --interactive mode when specifying individual files.", file=sys.stderr)
        sys.exit(1)

    files_to_discard = args.files
    if args.interactive:
        files_to_discard = _discard_interactive(project_dir, git_path)

    if files_to_discard:
        _discard_files(project_dir, git_path, files_to_discard, args.yes)
    else:
        _discard_all(project_dir, git_path, args.yes)

    sys.exit(0)


def _find_commit_by_run_id(project_dir: Path, git_path: str, run_id: str) -> str | None:
    """Searches the git log for a commit associated with a Run ID."""
    try:
        # Search the entire commit history for the Run ID in the message body
        result = subprocess.run(
            [git_path, "-C", str(project_dir), "log", "--all", f"--grep=Run ID: {run_id}", "--format=%H"],
            capture_output=True, text=True, check=True
        )
        if result.stdout.strip():
            # Return the first commit hash found
            return result.stdout.strip().split('\n')[0]
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return None


def run_rollback(args):
    """Reverts all commits associated with a specific agent Run ID."""
    project_dir = args.project_dir.resolve()
    run_id = args.run_id

    # --- Pre-flight checks ---
    git_path = shutil.which("git")
    if not git_path:
        print("❌ Error: 'git' command not found. Please ensure Git is installed and in your PATH.", file=sys.stderr)
        sys.exit(1)

    git_dir = project_dir / ".git"
    if not git_dir.exists() or not git_dir.is_dir():
        print("❌ Error: Not a git repository. Cannot rollback.", file=sys.stderr)
        sys.exit(1)

    # Check for uncommitted changes
    try:
        status_result = subprocess.run(
            [git_path, "-C", str(project_dir), "status", "--porcelain"],
            capture_output=True, text=True, check=True
        )
        if status_result.stdout.strip():
            print("❌ Error: Your repository has uncommitted changes.", file=sys.stderr)
            print("Please commit or stash them before using rollback.", file=sys.stderr)
            sys.exit(1)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"❌ Error checking git status: {e}", file=sys.stderr)
        sys.exit(1)

    # Resolve Run ID
    if not run_id or run_id == "last":
        history_file = project_dir / ".agent_history"
        if not history_file.exists():
            print("❌ Error: No agent history found.", file=sys.stderr)
            sys.exit(1)

        try:
            with open(history_file, "r") as f:
                lines = [l.strip() for l in f if l.strip()]
            if not lines:
                print("❌ Error: Agent history is empty.", file=sys.stderr)
                sys.exit(1)
            run_id = lines[-1]
            print(f"Rolling back last run: {run_id}")
        except IOError as e:
            print(f"❌ Error reading history file: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"Rolling back run: {run_id}")

    # Find commits associated with Run ID
    print("Searching for commits...")
    try:
        # We look for "Run ID: <run_id>" in the commit message body
        # git log --grep="Run ID: <run_id>" --format="%H"
        # This returns commits in reverse chronological order (newest first).
        # We want to revert them in that order.
        result = subprocess.run(
            [git_path, "-C", str(project_dir), "log", "--grep", f"Run ID: {run_id}", "--format=%H"],
            capture_output=True, text=True, check=True
        )
        commits = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    except subprocess.CalledProcessError as e:
        print(f"❌ Error searching git log: {e}", file=sys.stderr)
        sys.exit(1)

    if not commits:
        print(f"✅ No commits found for Run ID '{run_id}'. Nothing to rollback.")
        sys.exit(0)

    print(f"Found {len(commits)} commit(s) to revert:")
    for c in commits:
        print(f"  - {c[:7]}")

    if not args.yes:
        confirm = input("\nAre you sure you want to revert these commits? This will create new revert commits. [y/N]: ").strip().lower()
        if confirm != 'y':
            print("Aborted.")
            sys.exit(0)

    print("\nReverting commits...")
    reverted_count = 0
    try:
        # Iterate through commits (already newest first) and revert them
        for commit_hash in commits:
            print(f"  Reverting {commit_hash[:7]}...")
            # Use --no-edit to skip editor launch.
            revert_cmd = [git_path, "-C", str(project_dir), "revert", "--no-edit", commit_hash]

            revert_result = subprocess.run(revert_cmd, capture_output=True, text=True)

            if revert_result.returncode != 0:
                print(f"❌ Error reverting commit {commit_hash[:7]}:", file=sys.stderr)
                print(revert_result.stderr, file=sys.stderr)
                print("\nConflict detected or error occurred. Aborting rollback sequence.", file=sys.stderr)
                print("You may need to resolve the conflict manually or run 'git revert --abort'.", file=sys.stderr)
                sys.exit(1)

            reverted_count += 1

    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"\n✅ Successfully reverted {reverted_count} commit(s).")
    sys.exit(0)


def run_cherry_pick(args):
    """Applies the changes from a specific commit onto the current branch."""
    project_dir = args.project_dir.resolve()
    target = args.target

    # --- Pre-flight checks ---
    git_path = shutil.which("git")
    if not git_path:
        print("❌ Error: 'git' command not found. Please ensure Git is installed and in your PATH.", file=sys.stderr)
        sys.exit(1)

    git_dir = project_dir / ".git"
    if not git_dir.exists() or not git_dir.is_dir():
        print("❌ Error: Not a git repository. Cannot cherry-pick.", file=sys.stderr)
        sys.exit(1)

    # --- Target Resolution: Commit Hash vs. Run ID ---
    original_target = target
    # First, check if the target is a valid git object (commit, tag, etc.)
    is_git_ref = False
    try:
        check_commit_result = subprocess.run(
            [git_path, "-C", str(project_dir), "cat-file", "-t", target],
            capture_output=True, text=True
        )
        if check_commit_result.returncode == 0 and check_commit_result.stdout.strip() == "commit":
            is_git_ref = True
    except Exception:
        pass  # Ignore errors, we'll handle the 'not found' case below

    if not is_git_ref:
        print(f"'{target}' is not a known git commit. Assuming it is a Run ID and searching history...")
        commit_hash = _find_commit_by_run_id(project_dir, git_path, target)
        if commit_hash:
            print(f"✅ Found commit '{commit_hash[:7]}' associated with Run ID '{target}'.")
            target = commit_hash
        else:
            print(f"❌ Error: Could not find a git commit for target '{original_target}'.", file=sys.stderr)
            print("Please provide a valid commit hash or a Run ID from the agent's history.", file=sys.stderr)
            sys.exit(1)

    # --- Execute Cherry-Pick ---
    print(f"--- Applying commit {target[:7]} onto the current branch ---")
    try:
        # Use --no-commit to allow the user to inspect the changes before committing
        cmd = [git_path, "-C", str(project_dir), "cherry-pick", "--no-commit", target]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print(result.stdout)
            print(f"\n✅ Successfully cherry-picked commit {target[:7]}.")
            sys.exit(0)
        else:
            print("❌ Error: Cherry-pick failed.", file=sys.stderr)
            print("This is likely due to a merge conflict.", file=sys.stderr)
            print("\n--- Git Output ---", file=sys.stderr)
            print(result.stdout, file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            print("------------------", file=sys.stderr)
            print("\nPlease resolve the conflicts in your editor and then run:", file=sys.stderr)
            print(f"  git cherry-pick --continue", file=sys.stderr)
            print("\nTo abort the cherry-pick and return to the previous state, run:", file=sys.stderr)
            print(f"  git cherry-pick --abort", file=sys.stderr)
            sys.exit(1)

    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        stderr = getattr(e, 'stderr', str(e))
        if isinstance(stderr, bytes):
            stderr = stderr.decode().strip()
        print(f"❌ An unexpected error occurred: {stderr}", file=sys.stderr)
        sys.exit(1)


def run_rewind(args):
    """Resets the project to a previous state (git commit)."""
    project_dir = args.project_dir.resolve()
    target = args.target
    original_target = target  # Keep a copy for error messages

    # --- Pre-flight checks ---
    git_path = shutil.which("git")
    if not git_path:
        print("❌ Error: 'git' command not found. Please ensure Git is installed and in your PATH.", file=sys.stderr)
        sys.exit(1)

    git_dir = project_dir / ".git"
    if not git_dir.exists() or not git_dir.is_dir():
        print("❌ Error: Not a git repository. Cannot rewind.", file=sys.stderr)
        sys.exit(1)

    try:
        status_result = subprocess.run(
            [git_path, "-C", str(project_dir), "status", "--porcelain"],
            capture_output=True, text=True, check=True
        )
        if status_result.stdout.strip():
            print("❌ Error: Your repository has uncommitted changes.", file=sys.stderr)
            print("Please commit or stash them before using rewind.", file=sys.stderr)
            sys.exit(1)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"❌ Error checking git status: {e}", file=sys.stderr)
        sys.exit(1)


    # --- Interactive Mode ---
    if not target:
        print(f"--- Interactive Rewind in: {project_dir} ---")
        try:
            log_result = subprocess.run(
                [git_path, "-C", str(project_dir), "log", "--oneline", "--pretty=format:%h|%s|%cr", "-n", "15"],
                capture_output=True, text=True, check=True
            )
            commits = [line.split('|') for line in log_result.stdout.strip().split('\n')]
            if not commits or not commits[0]:
                print("No commits found in the repository.")
                sys.exit(0)

            print("Select a commit to rewind to (press Enter to cancel):")
            for i, (hash, subject, time) in enumerate(commits):
                print(f"  [{i+1}] {hash} - {subject} ({time})")

            selection = input("> ").strip()
            if not selection:
                print("Aborted.")
                sys.exit(0)

            try:
                index = int(selection) - 1
                if 0 <= index < len(commits):
                    target = commits[index][0]
                else:
                    print("❌ Invalid selection.", file=sys.stderr)
                    sys.exit(1)
            except ValueError:
                print("❌ Invalid input. Please enter a number.", file=sys.stderr)
                sys.exit(1)

        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"❌ Error getting git log: {e}", file=sys.stderr)
            sys.exit(1)
        except (EOFError, KeyboardInterrupt):
            print("\nAborted.")
            sys.exit(0)
    else:
        # --- Target Resolution: Commit Hash vs. Run ID ---
        # First, check if the target is a valid git object (commit, tag, etc.)
        is_git_ref = False
        try:
            check_ref_result = subprocess.run(
                [git_path, "-C", str(project_dir), "show-ref", "--verify", f"refs/heads/{target}"],
                capture_output=True, text=True
            )
            if check_ref_result.returncode == 0:
                is_git_ref = True
            else:
                # Also check if it's a commit hash
                check_commit_result = subprocess.run(
                    [git_path, "-C", str(project_dir), "cat-file", "-t", target],
                    capture_output=True, text=True
                )
                if check_commit_result.returncode == 0 and check_commit_result.stdout.strip() == "commit":
                    is_git_ref = True
        except Exception:
            pass  # Ignore errors, we'll handle the 'not found' case below

        if not is_git_ref:
            print(f"'{target}' is not a known git reference. Assuming it is a Run ID and searching history...")
            commit_hash = _find_commit_by_run_id(project_dir, git_path, target)
            if commit_hash:
                print(f"✅ Found commit '{commit_hash[:7]}' associated with Run ID '{target}'.")
                target = commit_hash
            else:
                print(f"❌ Error: Could not find a git commit for Run ID '{target}'.", file=sys.stderr)
                print("Please provide a valid commit hash, reference, or a Run ID from the agent's history.", file=sys.stderr)
                sys.exit(1)


    # --- Confirmation and Execution ---
    print(f"\nThis will perform a 'git reset --hard' to '{target}'.")
    print("This action is destructive and will discard all commits made after this point.")
    if not args.yes:
        confirm = input("Are you absolutely sure you want to proceed? [y/N]: ").strip().lower()
        if confirm != 'y':
            print("Aborted.")
            sys.exit(0)

    print(f"\nRewinding to {target}...")
    try:
        # Step 1: Clean any ignored files that might be lingering
        subprocess.run(
            [git_path, "-C", str(project_dir), "clean", "-fdx"],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        # Step 2: Reset to the target commit
        subprocess.run(
            [git_path, "-C", str(project_dir), "reset", "--hard", target],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        print("✅ Rewind complete.")
        print("Project state has been reset.")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        stderr = getattr(e, 'stderr', str(e))
        if isinstance(stderr, bytes):
            stderr = stderr.decode().strip()
        print(f"❌ Error during rewind: {stderr}", file=sys.stderr)
        sys.exit(1)

    sys.exit(0)


def run_empty_trash(args):
    """Permanently deletes the .agent_trash directory."""
    print("Warning: The 'empty-trash' command is deprecated and will be removed in a future version. "
          "Use 'trash clear --all' instead.", file=sys.stderr)
    import shutil
    project_dir = args.project_dir.resolve()
    trash_dir = project_dir / ".agent_trash"

    print(f"--- Permanently emptying trash in project: {project_dir} ---")

    if not trash_dir.exists() or not trash_dir.is_dir():
        print("Trash directory (.agent_trash) not found. Nothing to do.")
        sys.exit(0)

    # Count items for user confirmation
    trash_items = list(trash_dir.iterdir())
    if not trash_items:
        print("Trash directory is already empty.")
        # Also remove the empty .agent_trash directory itself
        try:
            trash_dir.rmdir()
            print("Removed empty .agent_trash directory.")
        except OSError as e:
            print(f"Could not remove empty .agent_trash directory: {e}", file=sys.stderr)
        sys.exit(0)

    print(f"The trash directory (.agent_trash) contains {len(trash_items)} item(s).")
    print("This action will permanently delete its contents.")

    if not args.yes:
        confirm = input("\nAre you sure you want to proceed? [y/N]: ").strip().lower()
        if confirm != 'y':
            print("Aborted.")
            sys.exit(0)

    print("\nEmptying trash...")
    try:
        shutil.rmtree(trash_dir)
        print("✅ Trash successfully emptied.")
    except OSError as e:
        print(f"Error while emptying trash: {e}", file=sys.stderr)
        sys.exit(1)

    sys.exit(0)


def run_restore(args):
    """Restores agent-generated artifacts from the most recent trash directory."""
    print("Warning: The 'restore' command is deprecated and will be removed in a future version. "
          "Use 'trash restore' instead.", file=sys.stderr)
    import shutil
    project_dir = args.project_dir.resolve()
    trash_base_dir = project_dir / ".agent_trash"

    print(f"--- Restoring artifacts in project: {project_dir} ---")

    if not trash_base_dir.exists() or not trash_base_dir.is_dir():
        print("Trash directory (.agent_trash) not found. Nothing to restore.")
        sys.exit(0)

    # Find the most recent trash directory (they are timestamped)
    try:
        latest_trash_dir = max(d for d in trash_base_dir.iterdir() if d.is_dir())
    except ValueError:
        print("No trash archives found in .agent_trash directory.")
        sys.exit(0)

    print(f"Found latest trash archive: {latest_trash_dir.name}")

    artifacts_to_restore = list(latest_trash_dir.iterdir())
    if not artifacts_to_restore:
        print("Trash archive is empty. Nothing to restore.")
        latest_trash_dir.rmdir() # Clean up empty dir
        print(f"Removed empty trash archive: {latest_trash_dir.name}")
        sys.exit(0)

    # Check for conflicts
    conflicting_files = []
    for artifact in artifacts_to_restore:
        destination_path = project_dir / artifact.name
        if destination_path.exists():
            conflicting_files.append(artifact.name)

    if conflicting_files:
        print("\n❌ Error: The following files already exist in the project directory:")
        for f in conflicting_files:
            print(f"  - {f}")
        print("Please move or delete these files manually before running restore.")
        sys.exit(1)

    print("\nThe following artifacts will be restored to the project directory:")
    for artifact in artifacts_to_restore:
        print(f"  - {artifact.name}")

    if not args.yes:
        confirm = input("\nAre you sure you want to proceed? [y/N]: ").strip().lower()
        if confirm != 'y':
            print("Aborted.")
            sys.exit(0)

    print("\nRestoring artifacts...")
    try:
        for artifact in artifacts_to_restore:
            dest = project_dir / artifact.name
            shutil.move(str(artifact), str(dest))
            print(f"Restored: {artifact.name}")

        # Clean up the now-empty trash directory
        latest_trash_dir.rmdir()
        print(f"Removed empty trash archive: {latest_trash_dir.name}")

    except OSError as e:
        print(f"Error during restore: {e}", file=sys.stderr)
        sys.exit(1)

    print("\n✅ Restore complete.")
    sys.exit(0)


from shared.cli_utils import (
    get_project_summary,
    get_suggestions,
    _run_enhanced_status_logic,
    _run_tree_logic,
    _run_report_logic,
    _run_dashboard_logic,
    _run_blame_logic,
    _run_next_logic,
    _run_context_show_logic,
    _run_context_analyze_logic,
    _find_metrics_file,
    _parse_metrics,
)

def run_release(args):
    """Manages the release process."""
    from shared.release import (
        get_latest_tag,
        get_commits_since_tag,
        determine_next_version,
        generate_changelog,
        bump_version_file,
        parse_current_version
    )

    project_dir = args.project_dir.resolve()

    # 1. Get current status
    latest_tag = get_latest_tag(project_dir)
    print(f"--- Release Management: {project_dir.name} ---")
    print(f"Latest tag: {latest_tag or 'None'}")

    commits = get_commits_since_tag(project_dir, latest_tag)
    print(f"Commits since tag: {len(commits)}")

    current_version = parse_current_version(project_dir)
    # If no current version in file, fallback to tag
    if not current_version and latest_tag:
        current_version = latest_tag.lstrip("v")

    print(f"Current version (file/tag): {current_version or '0.0.0'}")

    # 2. Determine bump
    if args.force_version:
        next_version = args.force_version
        print(f"Next version (forced): {next_version}")
    else:
        next_version = determine_next_version(current_version, commits)
        print(f"Next version (calculated): {next_version}")

    if next_version == current_version and not args.force_version:
        print("No version bump required based on commits.")
        if not args.yes:
            sys.exit(0)

    # 3. Generate Changelog
    changelog = generate_changelog(commits, next_version)

    if args.action == "plan":
        print("\n--- Plan: Changelog Preview ---")
        print(changelog)
        print("\n--- Plan: Actions ---")
        print(f"1. Update version to {next_version} in config files.")
        print(f"2. Create git tag v{next_version}.")
        sys.exit(0)

    elif args.action == "apply":
        if args.dry_run:
            print("[Dry Run] Would update files and create tag.")
            sys.exit(0)

        print("\n--- Applying Release ---")

        # Bump files
        modified = bump_version_file(project_dir, next_version)
        if modified:
            print(f"Updated version in: {', '.join(modified)}")
            # Commit these changes
            subprocess.run(["git", "-C", str(project_dir), "add"] + modified, check=True)
            subprocess.run(["git", "-C", str(project_dir), "commit", "-m", f"chore: bump version to {next_version}"], check=True)
            print("Committed version bump.")

        # Create tag
        tag_name = f"v{next_version}"
        if not args.no_changelog:
             # Use changelog as tag message
             # Write to temp file for safety
             import tempfile
             with tempfile.NamedTemporaryFile(mode='w+', delete=False) as tf:
                 tf.write(changelog)
                 tf_path = tf.name

             try:
                 subprocess.run(["git", "-C", str(project_dir), "tag", "-a", tag_name, "-F", tf_path], check=True)
             finally:
                 os.unlink(tf_path)
        else:
             subprocess.run(["git", "-C", str(project_dir), "tag", tag_name], check=True)

        print(f"✅ Created tag: {tag_name}")
        print("Don't forget to push: git push --follow-tags")
        sys.exit(0)


async def run_bisect(args):
    """Runs smart bisect."""
    from shared.bisect import run_bisect_logic, analyze_commit

    project_dir = args.project_dir.resolve()

    if args.action == "run":
        if not args.good or not args.bad or not args.command:
             print("Error: --good, --bad, and --command are required for 'run' action.", file=sys.stderr)
             sys.exit(1)

        success = await run_bisect_logic(
            project_dir=project_dir,
            good_commit=args.good,
            bad_commit=args.bad,
            run_command=args.command,
            agent_type=args.agent,
            model=args.model,
            verbose=args.verbose,
            no_analysis=args.no_analysis
        )
        sys.exit(0 if success else 1)

    elif args.action == "analyze":
        if not args.commit:
             print("Error: Commit hash required for analysis.", file=sys.stderr)
             sys.exit(1)

        description = args.bug_description or "A regression was reported on this commit."
        print(f"--- Analyzing Commit: {args.commit} ---")
        analysis = await analyze_commit(
            project_dir=project_dir,
            commit_hash=args.commit,
            bug_description=description,
            agent_type=args.agent,
            model=args.model,
            verbose=args.verbose
        )
        print("\n" + analysis)
        sys.exit(0)


def run_map(args):
    """Generates a code map."""
    from shared.map import _run_map_logic
    _run_map_logic(args.project_dir, args.format, args.focus)
    sys.exit(0)

def run_architecture(args):
    """Checks the project architecture against defined rules."""
    from shared.architecture import check_architecture

    project_dir = args.project_dir.resolve()
    print(f"--- Checking Architecture in: {project_dir} ---")

    rules = []

    # 1. Try to load from specific rules file
    if args.rules and Path(args.rules).exists():
        try:
            with open(args.rules, 'r') as f:
                loaded = yaml.safe_load(f)
                if isinstance(loaded, list):
                    rules = loaded
                elif isinstance(loaded, dict) and "architecture_rules" in loaded:
                    rules = loaded["architecture_rules"]
                else:
                    print(f"❌ Error: Invalid format in rules file {args.rules}. Expected list or dict with 'architecture_rules'.", file=sys.stderr)
                    sys.exit(1)
            print(f"Loaded rules from {args.rules}")
        except Exception as e:
            print(f"❌ Error loading rules file: {e}", file=sys.stderr)
            sys.exit(1)

    # 2. Try to load from agent_config.yaml (if no specific rules file provided or additive?)
    # For now, if rules file is provided, use it. If not, look in config.
    elif not rules:
        from shared.config_loader import load_config_from_file
        config = load_config_from_file()
        if "architecture_rules" in config:
            rules = config["architecture_rules"]
            print("Loaded rules from agent configuration.")

    if not rules:
        print("⚠️  No architecture rules found. Please define 'architecture_rules' in agent_config.yaml or provide a --rules file.")
        print("Example rule format:")
        print("  - source: \"shared/**\"")
        print("    deny: \"agents/**\"")
        sys.exit(0)

    violations = check_architecture(project_dir, rules)

    if violations:
        print(f"\n❌ Found {len(violations)} architecture violation(s):")
        for v in violations:
            print(f"  - {v['source']} imports {v['imported']}")
            print(f"    Rule: {v['rule']}")
        sys.exit(1)
    else:
        print("\n✅ No architecture violations found.")
        sys.exit(0)

def run_analytics(args):
    """Runs project analytics."""
    if args.type == "git":
        from shared.analytics import _run_analytics_git_logic
        _run_analytics_git_logic(args.project_dir)
    elif args.type == "code":
        print(_run_context_analyze_logic(args.project_dir))
    elif args.type == "complexity":
        from shared.complexity import _run_analytics_complexity_logic
        _run_analytics_complexity_logic(args.project_dir)
    sys.exit(0)

def run_duplication(args):
    """Runs the code duplication detector."""
    from shared.duplication import _run_duplication_logic
    _run_duplication_logic(
        project_dir=args.project_dir,
        min_tokens=args.min_tokens,
        files=args.files,
        ignore=args.ignore
    )
    sys.exit(0)

def run_unused(args):
    """Runs the unused code detector."""
    from shared.unused import _run_unused_logic
    _run_unused_logic(
        project_dir=args.project_dir,
        files=args.files,
        ignore=args.ignore
    )
    sys.exit(0)

def run_risk(args):
    """Runs the risk analysis (hotspots)."""
    from shared.risk_analysis import _run_risk_logic
    _run_risk_logic(
        project_dir=args.project_dir,
        limit=args.limit
    )
    sys.exit(0)

def run_impact(args):
    """Runs the predictive impact analysis."""
    from shared.impact import run_impact_logic
    run_impact_logic(
        project_dir=args.project_dir,
        json_output=args.json
    )
    sys.exit(0)

def run_a11y(args):
    """Runs the accessibility scanner."""
    from shared.a11y import _run_a11y_logic
    _run_a11y_logic(
        project_dir=args.project_dir,
        files=args.files,
        ignore=args.ignore,
        output_format=args.format
    )
    sys.exit(0)

def run_license(args):
    """Checks dependency license compliance."""
    from shared.dependencies import DependencyAnalyzer

    analyzer = DependencyAnalyzer(args.project_dir)
    data = analyzer.scan()

    allow_list = args.allow.split(",") if args.allow else None
    deny_list = args.deny.split(",") if args.deny else None

    results = analyzer.check_licenses(data, allow_list=allow_list, deny_list=deny_list)

    if args.action == "list":
        print(f"\n--- License Report for {args.project_dir} ---")
        print(f"  {'Package':<30} | {'License':<20} | {'Status':<10}")
        print("  " + "-" * 70)
        for item in results:
            pkg = item["package"]
            lic = item["license"]
            status = item["status"]

            # Truncate if too long
            if len(pkg) > 30: pkg = pkg[:27] + "..."
            if len(lic) > 20: lic = lic[:17] + "..."

            print(f"  {pkg:<30} | {lic:<20} | {status:<10}")

    elif args.action == "check":
        violations = [r for r in results if r["status"] == "VIOLATION"]
        if not violations:
            print("✅ No license violations found.")
            sys.exit(0)
        else:
            print(f"❌ Found {len(violations)} license violation(s):")
            for v in violations:
                print(f"  - {v['package']} ({v['license']}): {v['message']}")
            sys.exit(1)

    sys.exit(0)

def run_deps(args):
    """Generates a dependency graph or updates dependencies."""
    from shared.dependencies import _run_deps_logic, DependencyAnalyzer, DependencyUpdater

    if args.update:
        # 1. Scan and check for updates
        print("Scanning project and checking for updates...")
        analyzer = DependencyAnalyzer(args.project_dir)
        data = analyzer.scan()
        data = analyzer.check_updates(data)

        # 2. Collect outdated packages
        outdated_list = []
        for lang, files in data.items():
            for file_info in files:
                source = file_info["source"]
                file_path = args.project_dir / source
                for dep in file_info.get("dependencies", []):
                    if dep.get("outdated"):
                        outdated_list.append({
                            "lang": lang,
                            "file": file_path,
                            "name": dep["name"],
                            "current": dep.get("version", ""),
                            "latest": dep.get("latest", ""),
                            "type": dep.get("type", "prod")
                        })

        if not outdated_list:
            print("✅ All dependencies are up to date.")
            sys.exit(0)

        # 3. Interactive Selection
        print("\n--- Outdated Dependencies ---")
        for i, item in enumerate(outdated_list):
            print(f"[{i+1}] {item['name']} ({item['lang']}): {item['current']} -> {item['latest']} (in {item['file'].name})")

        print("\nEnter numbers to update (e.g., '1 3 5'), 'a' for all, or Enter to cancel.")
        try:
            selection = input("> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nAborted.")
            sys.exit(0)

        to_update = []
        if selection == 'a':
            to_update = outdated_list
        elif selection:
            try:
                indices = [int(x) - 1 for x in selection.split()]
                for idx in indices:
                    if 0 <= idx < len(outdated_list):
                        to_update.append(outdated_list[idx])
            except ValueError:
                print("Invalid input.")
                sys.exit(1)
        else:
            print("Aborted.")
            sys.exit(0)

        if not to_update:
            print("No valid packages selected.")
            sys.exit(0)

        # 4. Perform Updates
        updater = DependencyUpdater(args.project_dir)
        print(f"\nUpdating {len(to_update)} packages...")

        for item in to_update:
            print(f"Updating {item['name']}...")
            success = updater.update_dependency(
                item['file'],
                item['name'],
                item['latest'],
                item['type']
            )
            if success:
                print(f"✅ Updated {item['name']}")
            else:
                print(f"❌ Failed to update {item['name']}")

        sys.exit(0)

    print(_run_deps_logic(args.project_dir, args.format, args.check))
    sys.exit(0)

async def run_optimize(args):
    """Runs the optimization logic."""
    from shared.optimize import OptimizationManager

    project_dir = args.project_dir.resolve()
    manager = OptimizationManager(project_dir)

    success = await manager.optimize(
        script_path=Path(args.script),
        args=args.args,
        agent_type=args.agent,
        model=args.model
    )
    sys.exit(0 if success else 1)


def run_perf(args):
    """Runs performance profiling tools."""
    from shared.profiler import ProfilerManager

    project_dir = args.project_dir.resolve()
    manager = ProfilerManager(project_dir)

    if args.action == "run":
        if not args.script:
            print("Error: Script required for 'run' action.", file=sys.stderr)
            sys.exit(1)

        script_path = Path(args.script)
        # Separate script args if any
        script_args = args.script_args if hasattr(args, 'script_args') else []

        success = manager.run(script_path, script_args)
        sys.exit(0 if success else 1)

    elif args.action == "report":
        manager.report(limit=args.limit, sort_by=args.sort)
        sys.exit(0)


async def run_troubleshoot(args):
    """Runs the interactive troubleshooting session."""
    # Setup logging
    logger, _ = setup_logger(name="troubleshoot_logger", log_file=None, verbose=args.verbose, console_output=True)

    success = await run_troubleshoot_logic(
        project_dir=args.project_dir,
        issue=args.issue,
        agent_type=args.agent,
        model=args.model,
        yes=args.yes
    )
    sys.exit(0 if success else 1)


def run_knowledge(args):
    """Manages the agent's knowledge base."""
    from shared.database import init_db
    from shared.knowledge import KnowledgeManager
    from rich.console import Console
    from rich.table import Table

    # Ensure DB is initialized
    config_dir = args.project_dir.resolve()
    config_dir.mkdir(parents=True, exist_ok=True)
    init_db(config_dir / ".agent_db.sqlite")

    manager = KnowledgeManager()
    console = Console()

    if args.action == "list":
        items = manager.list_knowledge(category=args.category)
        if not items:
            console.print("No knowledge items found.", style="yellow")
            sys.exit(0)

        table = Table(title=f"Agent Knowledge ({args.category if args.category else 'All'})")
        table.add_column("ID", justify="right", style="cyan", no_wrap=True)
        table.add_column("Category", style="magenta")
        table.add_column("Source", style="green")
        table.add_column("Content", style="white")

        for item in items:
            table.add_row(str(item.id), item.category, item.source_agent, item.content)

        console.print(table)

    elif args.action == "add":
        if not args.content:
            console.print("Error: Content is required for 'add' action.", style="red")
            sys.exit(1)

        item = manager.add_knowledge(args.content, category=args.category, source="user")
        console.print(f"[green]Added knowledge item #{item.id}[/green]")

    elif args.action == "delete":
        if not args.id:
             console.print("Error: ID is required for 'delete' action.", style="red")
             sys.exit(1)

        if manager.delete_knowledge(int(args.id)):
            console.print(f"[green]Deleted knowledge item #{args.id}[/green]")
        else:
            console.print(f"[red]Item #{args.id} not found.[/red]")

    elif args.action == "graph":
        from shared.knowledge_graph import generate_knowledge_graph
        try:
            output_file = Path(args.output).resolve() if args.output else None
            result = generate_knowledge_graph(
                project_dir=args.project_dir.resolve(),
                output_format=args.format,
                output_file=output_file
            )
            console.print(f"[green]{result}[/green]")
        except Exception as e:
            console.print(f"[red]Error generating graph: {e}[/red]")
            sys.exit(1)

    elif args.action == "questions":
        questions = manager.get_questions(status=args.status)
        if not questions:
            console.print(f"No {args.status} questions found.", style="yellow")
            sys.exit(0)

        table = Table(title=f"Agent Questions ({args.status})")
        table.add_column("ID", justify="right", style="cyan", no_wrap=True)
        table.add_column("Source", style="green")
        table.add_column("Question", style="white")
        if args.status == "answered":
             table.add_column("Answer", style="yellow")

        for q in questions:
            row = [str(q.id), q.source_agent, q.question]
            if args.status == "answered":
                row.append(q.answer)
            table.add_row(*row)

        console.print(table)

    elif args.action == "answer":
         if not args.id or not args.answer:
              console.print("Error: ID and Answer are required.", style="red")
              sys.exit(1)

         if manager.answer_question(int(args.id), args.answer):
              console.print(f"[green]Answered question #{args.id}[/green]")
         else:
              console.print(f"[red]Question #{args.id} not found.[/red]")

    sys.exit(0)


async def run_ask(args):
    """Queries the codebase using the configured agent."""
    # Setup logging
    logger, _ = setup_logger(name="ask_logger", log_file=None, verbose=args.verbose, console_output=True)

    success = await run_ask_logic(
        query=args.query,
        project_dir=args.project_dir,
        agent_type=args.agent,
        model=args.model,
        files=args.files,
        verbose=args.verbose
    )
    sys.exit(0 if success else 1)


async def run_chat(args):
    """Starts an interactive chat session with the agent."""
    from shared.chat import run_chat_logic

    # We don't setup console logging here because ChatManager uses rich Console
    # and we don't want mixed output.
    # But we might want file logging if verbose.
    if args.verbose:
        setup_logger(name="chat_logger", log_file=None, verbose=True, console_output=False)

    await run_chat_logic(
        project_dir=args.project_dir,
        agent_type=args.agent,
        model=args.model,
        verbose=args.verbose
    )
    sys.exit(0)


async def run_do(args):
    """Translates natural language to shell commands."""
    # Setup logging
    logger, _ = setup_logger(name="do_logger", log_file=None, verbose=args.verbose, console_output=True)

    success = await run_do_logic(
        instruction=args.instruction,
        project_dir=args.project_dir,
        agent_type=args.agent,
        model=args.model,
        verbose=args.verbose,
        yes=args.yes
    )
    sys.exit(0 if success else 1)


async def run_debug(args):
    """Executes a command and uses AI to debug if it fails."""
    # Setup logging
    logger, _ = setup_logger(name="debug_logger", log_file=None, verbose=args.verbose, console_output=True)

    if not args.command_to_run:
        print("Error: No command provided to debug.", file=sys.stderr)
        sys.exit(1)

    success = await run_debug_logic(
        command_list=args.command_to_run,
        project_dir=args.project_dir,
        agent_type=args.agent,
        model=args.model,
        verbose=args.verbose
    )
    sys.exit(0 if success else 1)


async def run_code_review(args):
    """Runs an AI-powered code review."""
    # Setup logging
    logger, _ = setup_logger(name="review_logger", log_file=None, verbose=args.verbose, console_output=True)

    success = await run_code_review_logic(
        project_dir=args.project_dir,
        files=args.files,
        diff=args.diff,
        agent_type=args.agent,
        model=args.model,
        verbose=args.verbose
    )
    sys.exit(0 if success else 1)


async def run_explain(args):
    """Explains source code using AI."""
    # Setup logging
    logger, _ = setup_logger(name="explain_logger", log_file=None, verbose=args.verbose, console_output=True)

    success = await run_explain_logic(args)
    sys.exit(0 if success else 1)


async def run_summarize(args):
    """Summarizes git changes using AI."""
    # Setup logging
    logger, _ = setup_logger(name="summarize_logger", log_file=None, verbose=args.verbose, console_output=True)

    success = await run_summarize_logic(
        project_dir=args.project_dir,
        target=args.target,
        agent_type=args.agent,
        model=args.model,
        verbose=args.verbose
    )
    sys.exit(0 if success else 1)


async def run_estimate(args):
    """Estimates the complexity and effort of a feature."""
    from shared.estimate import run_estimate_logic

    # Setup logging
    logger, _ = setup_logger(name="estimate_logger", log_file=None, verbose=args.verbose, console_output=True)

    files = [f.strip() for f in args.files.split(",")] if args.files else None

    success = await run_estimate_logic(
        feature_description=args.feature,
        project_dir=args.project_dir,
        files=files,
        agent_type=args.agent,
        model=args.model,
        verbose=args.verbose
    )
    sys.exit(0 if success else 1)


def run_context(args):
    """Displays an analysis of the agent's context."""
    if args.action == "show":
        context_output = _run_context_show_logic(project_dir=args.project_dir)
        print(context_output)
    elif args.action == "analyze":
        context_output = _run_context_analyze_logic(project_dir=args.project_dir)
        print(context_output)
    sys.exit(0)

def run_next(args):
    """Analyzes the project and executes the next logical command upon confirmation."""
    success = _run_next_logic(project_dir=args.project_dir)
    sys.exit(0 if success else 1)

def run_blame(args):
    """Shows the agent Run ID or author for each line of a file."""
    blame_output = _run_blame_logic(project_dir=args.project_dir, filepath=args.filepath)
    print(blame_output)
    if "❌ Error" in blame_output:
        sys.exit(1)
    sys.exit(0)


def run_smart_search(args):
    """Runs a smart semantic search using BM25."""
    from shared.smart_search import SmartSearchEngine

    project_dir = args.project_dir.resolve()
    print(f"--- Smart Search in: {project_dir} ---")
    print(f"Indexing codebase... (this might take a moment)")

    engine = SmartSearchEngine(project_dir)
    engine.index(file_pattern=args.files)

    print(f"Indexed {engine.num_docs} documents.")
    print(f"Searching for: '{args.query}'")

    results = engine.search(args.query, limit=args.limit)

    if not results:
        print("✅ No relevant results found.")
        sys.exit(0)

    print(f"\nFound {len(results)} relevant results:\n")

    for i, res in enumerate(results):
        print(f"[{i+1}] \033[1m{res['file']}\033[0m (Score: {res['score']:.2f})")
        print(f"    \033[90m{res['snippet']}\033[0m") # Gray snippet
        print()

    sys.exit(0)


def run_search(args):
    """Searches the codebase for a pattern."""
    from shared.search import search_codebase

    project_dir = args.project_dir.resolve()

    print(f"--- Searching in: {project_dir} ---")
    print(f"Pattern: {args.pattern}")

    try:
        results = search_codebase(
            project_dir,
            args.pattern,
            file_pattern=args.files,
            case_sensitive=args.case_sensitive,
            is_regex=args.regex,
            context_lines=args.context
        )
    except Exception as e:
        print(f"❌ Error during search: {e}", file=sys.stderr)
        sys.exit(1)

    if not results:
        print("✅ No matches found.")
        sys.exit(0)

    # Group by file for cleaner output
    results_by_file = {}
    for res in results:
        f = res['file']
        if f not in results_by_file:
            results_by_file[f] = []
        results_by_file[f].append(res)

    for file_path, matches in results_by_file.items():
        print(f"\n📄 \033[1m{file_path}\033[0m") # Bold filename
        for m in matches:
            # Context before
            for ctx in m['context_before']:
                print(f"    \033[90m{ctx}\033[0m") # Gray context

            # Match
            # Highlight the pattern in the content?
            # Simple highlight if not regex or complex
            content = m['content']
            # We skip highlighting for now to avoid messiness with regex matches
            print(f"  \033[32m{m['line']}\033[0m: {content}") # Green line num

            # Context after
            for ctx in m['context_after']:
                print(f"    \033[90m{ctx}\033[0m")

    print(f"\nFound {len(results)} matches in {len(results_by_file)} files.")
    sys.exit(0)


def run_replace(args):
    """Replaces text in the codebase."""
    from shared.replace import replace_in_codebase

    project_dir = args.project_dir.resolve()

    print(f"--- Replacing in: {project_dir} ---")
    print(f"Pattern: {args.pattern}")
    print(f"Replacement: {args.replacement}")
    if args.dry_run:
        print("(Dry Run - No changes will be saved)")

    try:
        stats = replace_in_codebase(
            project_dir,
            args.pattern,
            args.replacement,
            file_pattern=args.files,
            case_sensitive=args.case_sensitive,
            is_regex=args.regex,
            dry_run=args.dry_run
        )
    except Exception as e:
        print(f"❌ Error during replace: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"\nMatched files: {stats['files_matched']}")
    print(f"Files changed: {stats['files_changed']}")
    print(f"Replacements:  {stats['replacements_count']}")

    if stats["diffs"]:
        print("\n--- Diffs ---")
        for file, diff in stats["diffs"].items():
            print(f"📄 {file}")
            print(diff)
            print("-" * 20)

    if args.dry_run and stats['files_changed'] > 0:
        print("\nTo apply these changes, run the command again without --dry-run")

    sys.exit(0)


def run_todos(args):
    """Scans the project for TODO comments."""
    from shared.todos import scan_todos, get_todo_blame

    project_dir = args.project_dir.resolve()
    tags = [t.strip() for t in args.tags.split(",")] if args.tags else None

    if not args.json:
        print(f"--- Scanning for TODOs in: {project_dir} ---")
        if tags:
            print(f"Tags: {', '.join(tags)}")

    try:
        todos = scan_todos(project_dir, tags=tags)
    except Exception as e:
        print(f"❌ Error scanning for TODOs: {e}", file=sys.stderr)
        sys.exit(1)

    if not todos:
        print("✅ No TODOs found.")
        sys.exit(0)

    # Process results (blame if requested)
    if args.blame:
        print("Fetching git blame information (this might take a moment)...")
        for todo in todos:
            blame_info = get_todo_blame(project_dir, todo['file'], todo['line'])
            todo['author'] = blame_info.get('author', 'Unknown')
            todo['date'] = blame_info.get('date', 'Unknown')

    # Output formatting
    if args.json:
        print(json.dumps(todos, indent=2))
        sys.exit(0)

    # Console output
    # Group by file
    todos_by_file = {}
    for todo in todos:
        file_path = todo['file']
        if file_path not in todos_by_file:
            todos_by_file[file_path] = []
        todos_by_file[file_path].append(todo)

    for file_path, file_todos in sorted(todos_by_file.items()):
        print(f"\n📄 {file_path}")
        for todo in file_todos:
            line_str = str(todo['line']).rjust(4)
            tag_str = todo['tag'].ljust(5)
            text = todo['text']

            blame_str = ""
            if args.blame:
                author = todo.get('author', 'Unknown')
                date = todo.get('date', 'Unknown')
                blame_str = f" [{author}, {date}]"

            print(f"  {line_str}: {tag_str} {text}{blame_str}")

    print(f"\nFound {len(todos)} item(s).")
    sys.exit(0)


def run_stash(args):
    """Manages git stashes for the project."""
    project_dir = args.project_dir.resolve()

    # --- Pre-flight checks ---
    git_path = shutil.which("git")
    if not git_path or not (project_dir / ".git").is_dir():
        print("❌ Error: Not a git repository. Cannot manage stashes.", file=sys.stderr)
        sys.exit(1)

    # --- Action Dispatcher ---
    if args.action == "push":
        _stash_push(args, git_path, project_dir)
    elif args.action == "list":
        _stash_list(args, git_path, project_dir)
    elif args.action == "pop":
        _stash_pop(args, git_path, project_dir)
    elif args.action == "drop":
        _stash_drop(args, git_path, project_dir)

def _stash_push(args, git_path, project_dir):
    """Stashes uncommitted changes."""
    print(f"--- Stashing changes in: {project_dir} ---")
    try:
        # Check if there's anything to stash
        status_result = subprocess.run(
            [git_path, "-C", str(project_dir), "status", "--porcelain"],
            capture_output=True, text=True, check=True
        )
        if not status_result.stdout.strip():
            print("✅ No changes to stash.")
            sys.exit(0)

        cmd = [git_path, "-C", str(project_dir), "stash", "push", "-u"]
        if args.message:
            cmd.extend(["-m", args.message])

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Error stashing changes: {result.stderr}", file=sys.stderr)
            sys.exit(1)

        print("✅ Changes stashed successfully.")
        _stash_list(args, git_path, project_dir, count=1) # Show the latest stash

    except subprocess.CalledProcessError as e:
        print(f"❌ An error occurred: {e.stderr}", file=sys.stderr)
        sys.exit(1)

def _stash_list(args, git_path, project_dir, count=None):
    """Lists all available stashes."""
    print(f"--- Stashes in: {project_dir} ---")
    try:
        cmd = [git_path, "-C", str(project_dir), "stash", "list"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        stashes = result.stdout.strip().split('\n')
        if not stashes or not stashes[0]:
            print("No stashes found.")
            return []

        if count:
            stashes = stashes[:count]

        for stash in stashes:
            print(f"  {stash}")
        return stashes

    except subprocess.CalledProcessError as e:
        print(f"❌ Error listing stashes: {e.stderr}", file=sys.stderr)
        return []

def _stash_pop(args, git_path, project_dir):
    """Interactively applies and removes a stash."""
    stashes = _stash_list(args, git_path, project_dir)
    if not stashes:
        sys.exit(0)

    try:
        selection_str = input(f"\nEnter the number of the stash to pop (0-{len(stashes)-1}), or press Enter to cancel: ").strip()
        if not selection_str:
            print("Aborted.")
            sys.exit(0)

        selection = int(selection_str)
        if not (0 <= selection < len(stashes)):
            print("❌ Invalid selection.", file=sys.stderr)
            sys.exit(1)

        stash_ref = f"stash@{{{selection}}}"
        print(f"\nPopping {stash_ref}...")

        result = subprocess.run(
            [git_path, "-C", str(project_dir), "stash", "pop", str(selection)],
            capture_output=True, text=True
        )

        if result.returncode != 0:
            print(f"❌ Error popping stash: {result.stderr}", file=sys.stderr)
            if result.stdout:
                print(f"Output:\n{result.stdout}")
            sys.exit(1)

        print(f"✅ Stash {stash_ref} popped successfully.")
        if result.stdout:
            print(result.stdout)

    except (ValueError, IndexError):
        print("❌ Invalid input. Please enter a valid number.", file=sys.stderr)
        sys.exit(1)
    except (EOFError, KeyboardInterrupt):
        print("\nAborted.")
        sys.exit(0)

def _stash_drop(args, git_path, project_dir):
    """Interactively deletes a stash."""
    stashes = _stash_list(args, git_path, project_dir)
    if not stashes:
        sys.exit(0)

    try:
        selection_str = input(f"\nEnter the number of the stash to drop (0-{len(stashes)-1}), or press Enter to cancel: ").strip()
        if not selection_str:
            print("Aborted.")
            sys.exit(0)

        selection = int(selection_str)
        if not (0 <= selection < len(stashes)):
            print("❌ Invalid selection.", file=sys.stderr)
            sys.exit(1)

        stash_ref = f"stash@{{{selection}}}"

        if not args.yes:
            confirm = input(f"Are you sure you want to delete {stash_ref}? [y/N]: ").strip().lower()
            if confirm != 'y':
                print("Aborted.")
                sys.exit(0)

        print(f"\nDropping {stash_ref}...")
        result = subprocess.run(
            [git_path, "-C", str(project_dir), "stash", "drop", str(selection)],
            check=True, capture_output=True, text=True
        )

        print(f"✅ Stash {stash_ref} dropped successfully.")
        print(result.stdout.strip())

    except (ValueError, IndexError):
        print("❌ Invalid input. Please enter a valid number.", file=sys.stderr)
        sys.exit(1)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        stderr = getattr(e, 'stderr', str(e))
        print(f"❌ Error dropping stash: {stderr}", file=sys.stderr)
        sys.exit(1)
    except (EOFError, KeyboardInterrupt):
        print("\nAborted.")
        sys.exit(0)


def run_timeline(args):
    """Generates a project timeline."""
    from shared.timeline import TimelineCollector, TimelineRenderer

    project_dir = args.project_dir.resolve()
    collector = TimelineCollector(project_dir)
    renderer = TimelineRenderer()

    if not args.output and args.format == "text":
        print(f"--- Collecting timeline events for {project_dir.name} ---")

    events = collector.get_timeline(limit=args.limit)

    output = ""
    if args.format == "text":
        output = renderer.render_text(events)
    elif args.format == "json":
        output = renderer.render_json(events)
    elif args.format == "html":
        output = renderer.render_html(events)

    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output)
            print(f"✅ Timeline saved to {args.output}")
        except Exception as e:
            print(f"❌ Error saving timeline: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(output)

    sys.exit(0)


def run_report(args):
    """Generates a summary report for a specific agent run."""
    success = _run_report_logic(
        run_id=args.run_id,
        output_path=args.output,
        project_dir=args.project_dir
    )
    sys.exit(0 if success else 1)

def run_dashboard(args):
    """Displays a comprehensive dashboard of the project's status."""
    if hasattr(args, 'format') and args.format == "html":
        from shared.html_dashboard import generate_html_dashboard
        output = generate_html_dashboard(args.project_dir)
        output_file = Path(args.output)
        try:
            output_file.write_text(output, encoding='utf-8')
            print(f"✅ Dashboard saved to: {output_file.resolve()}")
        except IOError as e:
            print(f"❌ Error writing dashboard to file: {e}", file=sys.stderr)
            sys.exit(1)
        sys.exit(0)
    else:
        dashboard_text = _run_dashboard_logic(project_dir=args.project_dir)
        print(dashboard_text)
        sys.exit(0)

def run_tree(args):
    """Displays a tree view of the project directory."""
    tree_output = _run_tree_logic(
        project_dir=args.project_dir,
        depth=args.depth,
        full=args.full
    )
    print(tree_output)
    sys.exit(0)


def run_summary(args):
    """Displays a high-level summary of the project's status."""
    print("Warning: The 'summary' command is deprecated and will be removed in a future version. "
          "Please use the 'status' command instead.", file=sys.stderr)
    summary_text = get_project_summary(project_dir=args.project_dir)
    print(summary_text)
    sys.exit(0)


def run_suggest(args):
    """Analyzes the project and suggests the next logical commands to run."""
    suggestions = get_suggestions(project_dir=args.project_dir)
    if not suggestions:
        print("✅ Project is in a clean state. No specific actions to suggest.")
        print("   - To start a new task, run the agent with a --spec or --jira-ticket.")
        sys.exit(0)

    print("--- Suggested Next Steps ---")
    print("Based on the current project state, here are some suggested commands:\n")
    for suggestion in suggestions:
        print(f"👉 {suggestion['command']}")
        print(f"   Reason: {suggestion['reason']}\n")
    sys.exit(0)


def run_status(args):
    """Displays the current status of the agent project."""
    status_text = _run_enhanced_status_logic(project_dir=args.project_dir)
    print(status_text)
    sys.exit(0)


def run_glance(args):
    """Displays a compact, high-level overview of the project's status."""
    project_dir = args.project_dir.resolve()

    # 1. Get Workflow Stage
    stage_key = get_workflow_stage(project_dir)
    stage_info = WORKFLOW_STAGES.get(stage_key, {"name": "Unknown"})

    # 2. Get Git Status Summary (brief)
    git_path = shutil.which("git")
    git_summary = "Git not found"
    if git_path and (project_dir / ".git").is_dir():
        try:
            result = subprocess.run(
                [git_path, "-C", str(project_dir), "status", "--porcelain"],
                capture_output=True, text=True, check=True
            )
            changes = result.stdout.strip().split('\n') if result.stdout.strip() else []
            if not changes:
                git_summary = "✅ Clean"
            else:
                untracked = sum(1 for line in changes if line.startswith('??'))
                tracked_changes = [line for line in changes if not line.startswith('??')]
                staged = sum(1 for line in tracked_changes if line and line[0] != ' ')
                unstaged = sum(1 for line in tracked_changes if line and len(line) > 1 and line[1] != ' ')
                summary_parts = []
                if staged: summary_parts.append(f"{staged} staged")
                if unstaged: summary_parts.append(f"{unstaged} unstaged")
                if untracked: summary_parts.append(f"{untracked} untracked")
                git_summary = f"⚠️ {', '.join(summary_parts)}"
        except (subprocess.CalledProcessError, FileNotFoundError):
            git_summary = "Error checking status"

    # 3. Get Next Suggested Action
    suggestions = get_suggestions(project_dir, limit=1)
    next_action = suggestions[0]['command'] if suggestions else "No specific suggestion."

    # --- Formatting the Output ---
    # Use ANSI escape codes for color and boldness
    BOLD = '\033[1m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    ENDC = '\033[0m'
    CYAN_BOLD = BOLD + CYAN

    print(f"{BOLD}--- Project Glance: {project_dir.name} ---{ENDC}")
    print(f"  {CYAN_BOLD}Stage{ENDC}:     {stage_info['name']}")
    print(f"  {CYAN_BOLD}Git Status{ENDC}: {git_summary}")
    print(f"  {CYAN_BOLD}Next Step{ENDC}:  `{next_action}`")


def _run_history_logic(project_dir):
    """The core logic for displaying agent run history."""
    history_file = project_dir / ".agent_history"
    repo_root = Path(__file__).parent
    logs_dir = repo_root / "agents/logs"

    print(f"--- Agent Run History: {project_dir} ---")

    if not history_file.exists():
        print("No agent run history found for this project.")
        return

    try:
        with open(history_file, "r") as f:
            run_ids = [line.strip() for line in f if line.strip()]
    except IOError as e:
        print(f"Error reading history file: {e}", file=sys.stderr)
        return

    if not run_ids:
        print("History is empty.")
        return

    for i, run_id in enumerate(reversed(run_ids)):
        latest_marker = " (latest)" if i == 0 else ""
        print(f"\n[{len(run_ids)-i}] Run ID: {run_id}{latest_marker}")
        log_file = logs_dir / f"{run_id}.log"
        if log_file.exists():
            try:
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    # Read first line for timestamp
                    first_line_raw = f.readline()
                    first_line = first_line_raw.strip()

                    if not first_line:
                        print("  Log file is empty.")
                    else:
                        timestamp = first_line.split(" - ")[0] if " - " in first_line else "[No Timestamp]"
                        print(f"  Timestamp: {timestamp}")
                        print("  Log Summary (last 5 lines):")

                        # Reset to beginning to get full tail to correctly capture the last 5 lines
                        # even if the file is short or the first line is part of the last 5.
                        f.seek(0)
                        last_lines = deque((line.strip() for line in f if line.strip()), maxlen=5)
                        for line in last_lines:
                            print(f"    {line}")

            except Exception as e:
                print(f"  Error reading log file: {e}")
        else:
            print("  Log file not found.")

def run_history(args):
    """Displays a history of agent runs for the project."""
    _run_history_logic(project_dir=args.project_dir)
    sys.exit(0)


def _run_last_logic(project_dir):
    """The core logic for displaying a summary of the last agent run."""
    print(f"--- Summary of Last Run: {project_dir} ---")

    # 1. Get the last run ID
    history_file = project_dir / ".agent_history"
    if not history_file.exists():
        print("No agent run history found for this project.")
        return False

    try:
        with open(history_file, "r") as f:
            run_ids = [line.strip() for line in f if line.strip()]
        if not run_ids:
            print("History is empty.")
            return False
        last_run_id = run_ids[-1]
        print(f"Last Run ID: {last_run_id}")
    except IOError as e:
        print(f"Error reading history file: {e}", file=sys.stderr)
        return False

    # 2. Display Metrics
    metrics_file = _find_metrics_file(last_run_id, project_dir)
    if metrics_file:
        metrics = _parse_metrics(metrics_file)
        # Reuse the display table but with a different title
        _display_metrics_table(metrics, f"Performance Metrics")
    else:
        print("\n--- Performance Metrics ---")
        print("No metrics file found for the last run.")

    # 3. Display QA Summary
    print("\n--- QA Summary ---")
    qa_summary_file = project_dir / "qa_summary.txt"
    if qa_summary_file.exists():
        try:
            summary_content = qa_summary_file.read_text().strip()
            print(summary_content)
        except IOError as e:
            print(f"Error reading qa_summary.txt: {e}")
    else:
        print("No QA summary found for the last run.")

    # 4. Display Log Summary
    print("\n--- Log Summary (Last 10 lines) ---")
    repo_root = Path(__file__).parent
    log_file = repo_root / f"agents/logs/{last_run_id}.log"
    if log_file.exists():
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                last_lines = deque((line.strip() for line in f if line.strip()), maxlen=10)
                for line in last_lines:
                    print(f"  {line}")
        except IOError as e:
            print(f"Error reading log file: {e}")
    else:
        print("Log file not found.")

    return True

def run_last(args):
    """Displays a summary of the last agent run."""
    success = _run_last_logic(project_dir=args.project_dir)
    sys.exit(0 if success else 1)


def run_last_run_id(args):
    """Prints the ID of the last agent run to stdout."""
    project_dir = args.project_dir.resolve()
    history_file = project_dir / ".agent_history"

    if not history_file.exists():
        # Using stderr for errors to not pollute stdout, which is meant for the ID
        print("No agent run history found for this project.", file=sys.stderr)
        sys.exit(1)

    try:
        with open(history_file, "r") as f:
            run_ids = [line.strip() for line in f if line.strip()]
        if not run_ids:
            print("History is empty.", file=sys.stderr)
            sys.exit(1)
        last_run_id = run_ids[-1]
        print(last_run_id)  # Print the ID to stdout
        sys.exit(0)
    except IOError as e:
        print(f"Error reading history file: {e}", file=sys.stderr)
        sys.exit(1)


def _run_diff_summary_logic(project_dir):
    """The core logic for displaying a git diff summary."""
    git_path = shutil.which("git")
    if not git_path:
        print("❌ Error: 'git' command not found. Please ensure Git is installed and in your PATH.", file=sys.stderr)
        return False

    git_dir = project_dir / ".git"
    if not git_dir.exists() or not git_dir.is_dir():
        print("❌ Error: Not a git repository. Cannot show diff summary.", file=sys.stderr)
        return False

    print(f"--- Diff Summary: {project_dir} ---")
    try:
        cmd = [git_path, "-C", str(project_dir), "diff", "--stat"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        if not result.stdout.strip():
            print("✅ No uncommitted changes.")
        else:
            print(result.stdout)
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.strip()
        print(f"❌ Error getting diff summary: {stderr}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}", file=sys.stderr)
        return False
    return True

def run_diff_summary(args):
    """Displays a summary of uncommitted git changes."""
    success = _run_diff_summary_logic(project_dir=args.project_dir)
    sys.exit(0 if success else 1)


def run_diff(args):
    """Shows a detailed, colorized diff of uncommitted changes or a specific commit."""
    project_dir = args.project_dir.resolve()
    target = args.target

    # --- Pre-flight checks ---
    git_path = shutil.which("git")
    if not git_path:
        print("❌ Error: 'git' command not found. Please ensure Git is installed and in your PATH.", file=sys.stderr)
        sys.exit(1)

    git_dir = project_dir / ".git"
    if not git_dir.exists() or not git_dir.is_dir():
        print("❌ Error: Not a git repository. Cannot show diff.", file=sys.stderr)
        sys.exit(1)

    # --- Logic ---
    try:
        if not target:
            # Case 1: Show uncommitted changes
            print(f"--- Uncommitted Changes (HEAD): {project_dir} ---")
            cmd = [git_path, "-C", str(project_dir), "diff", "--color=always", "HEAD"]
            # Use subprocess.run without capturing output to stream directly
            result = subprocess.run(cmd)
            sys.exit(result.returncode)

        # Case 2: Target is provided (Run ID or commit hash)
        original_target = target
        # Check if it's a known git reference first
        is_git_ref = subprocess.run(
            [git_path, "-C", str(project_dir), "rev-parse", "--verify", f"{target}^{{commit}}"],
            capture_output=True, text=True
        ).returncode == 0

        if not is_git_ref:
            # If not a direct git ref, assume it's a Run ID
            commit_hash = _find_commit_by_run_id(project_dir, git_path, target)
            if not commit_hash:
                print(f"❌ Error: Target '{original_target}' is not a valid commit or Run ID.", file=sys.stderr)
                sys.exit(1)
            target = commit_hash
            print(f"--- Showing diff for Run ID '{original_target}' (Commit: {target[:7]}) ---")
        else:
            print(f"--- Showing diff for Commit: {target} ---")

        # Use 'git show' which nicely formats the commit info and the diff
        cmd = [git_path, "-C", str(project_dir), "show", "--color=always", target]
        result = subprocess.run(cmd)
        sys.exit(result.returncode)

    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        stderr = getattr(e, 'stderr', str(e))
        if isinstance(stderr, bytes): stderr = stderr.decode().strip()
        print(f"❌ An error occurred: {stderr}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)


def _run_log_logic(project_dir, count=None):
    """The core logic for displaying the git commit history."""
    git_path = shutil.which("git")
    if not git_path:
        print("❌ Error: 'git' command not found. Please ensure Git is installed and in your PATH.", file=sys.stderr)
        return False

    git_dir = project_dir / ".git"
    if not git_dir.exists() or not git_dir.is_dir():
        print("❌ Error: Not a git repository. Cannot show log.", file=sys.stderr)
        return False

    print(f"--- Git Commit History: {project_dir} ---")
    try:
        cmd = [
            git_path,
            "-C", str(project_dir),
            "log",
            "--color=always",
            "--graph",
            "--pretty=format:%Cred%h%Creset -%C(yellow)%d%Creset %s %Cgreen(%cr) %C(bold blue)<%an>%Creset",
            "--abbrev-commit",
        ]
        if count is not None:
            cmd.extend(["-n", str(count)])

        result = subprocess.run(cmd)

        if result.returncode != 0:
            print(f"\n❌ Error: git log command failed with exit code {result.returncode}.", file=sys.stderr)
            return False

    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}", file=sys.stderr)
        return False
    return True

def run_log(args):
    """Displays the git commit history for the project."""
    success = _run_log_logic(project_dir=args.project_dir, count=args.count)
    sys.exit(0 if success else 1)


import time
def _run_logs_logic(run_id=None, lines=None, follow=False, grep=None):
    """The core logic for displaying agent logs."""
    repo_root = Path(__file__).parent
    logs_dir = repo_root / "agents/logs"

    if not logs_dir.exists():
        print("Logs directory not found.")
        return False

    # --- Step 1: Determine which log file to use ---
    log_file = None
    if run_id:
        log_file = logs_dir / f"{run_id}.log"
        if not log_file.exists():
            print(f"Log file not found for Run ID: {run_id}")
            return False
    else:
        # If no run_id, we either list logs or operate on the latest one
        try:
            all_logs = sorted(logs_dir.glob('*.log'), key=lambda p: p.stat().st_mtime, reverse=True)
            # Default action: list logs
            if not all_logs and not (lines or follow or grep):
                print("--- Last 10 Agent Logs ---")
                print("No logs found.")
                print("\nUse 'logs <Run ID>' to view a specific log.")
                return True

            if not all_logs:
                print("No logs found to perform the action on.")
                return False

            # If any flags are present, use the latest log
            if lines or follow or grep:
                log_file = all_logs[0]
            else:
                # Default behavior: list the last 10 logs
                print("--- Last 10 Agent Logs ---")
                for i, log_f in enumerate(all_logs[:10]):
                    run_id_from_file = log_f.stem
                    latest_marker = " (latest)" if i == 0 else ""
                    print(f"  - {run_id_from_file}{latest_marker}")
                print("\nUse 'logs <Run ID>' or flags like --lines, --follow on the latest log.")
                return True
        except OSError as e:
            print(f"Error accessing logs directory: {e}", file=sys.stderr)
            return False

    # If we fall through, we have a log_file to process.
    if log_file:
        print(f"--- Displaying logs for: {log_file.name} ---")

    def print_filtered(line):
        if not grep or grep in line:
            print(line, end='')

    try:
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            # If not following, it's simple: read, filter, print.
            if not follow:
                if lines is not None:
                    # To preserve original behavior (filter applied AFTER selecting last N lines):
                    # We must read the last N lines of the file, then filter.
                    # This means we use deque on the raw file, then apply filter.
                    log_lines = deque(f, maxlen=lines)
                else:
                    # Iterator to avoid loading full file
                    log_lines = f

                for line in log_lines:
                    print_filtered(line)

                return True

            # If following, the logic is more complex.
            if lines is not None:
                # Print tail first
                all_lines = f.readlines()
                tail_lines = all_lines[-lines:]
                for line in tail_lines:
                    print_filtered(line)

            # Now, start following from the end of the file
            f.seek(0, 2)
            while True:
                line = f.readline()
                if not line:
                    time.sleep(0.1)
                    continue
                print_filtered(line)

    except IOError as e:
        print(f"Error reading log file: {e}", file=sys.stderr)
        return False
    except KeyboardInterrupt:
        print("\n--- Stopped following log ---")
        return True

    return True

def run_logs(args):
    """Displays agent logs."""
    if hasattr(args, 'explore') and args.explore:
        print("Log Explorer is now integrated into the main TUI. Please run 'tui' command.")
        sys.exit(0)

    success = _run_logs_logic(
        run_id=args.run_id,
        lines=args.lines,
        follow=args.follow,
        grep=args.grep
    )
    sys.exit(0 if success else 1)


# --- Workflow Subcommand Helpers ---
from shared.cli_utils import get_workflow_stage, WORKFLOW_STAGES, WORKFLOW_ORDER

def _workflow_status(args):
    """Displays the current workflow status."""
    project_dir = args.project_dir.resolve()
    current_stage_key = get_workflow_stage(project_dir)
    current_stage = WORKFLOW_STAGES[current_stage_key]
    current_index = WORKFLOW_ORDER.index(current_stage_key)

    print(f"--- Workflow Status: {project_dir} ---")
    print(f"  Current Stage: {current_stage['name']}")

    if current_stage_key == "SIGNED_OFF":
        print("\n  Project is complete. No further workflow actions.")
    else:
        next_stage_key = WORKFLOW_ORDER[current_index + 1]
        next_stage = WORKFLOW_STAGES[next_stage_key]
        print(f"\n  Next action: 'workflow advance' to move to '{next_stage['name']}'.")


def _workflow_advance(args):
    """Advances the project to the next workflow stage."""
    project_dir = args.project_dir.resolve()
    current_stage_key = get_workflow_stage(project_dir)
    current_index = WORKFLOW_ORDER.index(current_stage_key)

    if current_stage_key == "SIGNED_OFF":
        print("Project is already at the final 'Signed Off' stage. Cannot advance further.")
        sys.exit(0)

    next_stage_key = WORKFLOW_ORDER[current_index + 1]
    next_stage = WORKFLOW_STAGES[next_stage_key]
    marker_file_path = project_dir / next_stage["file"]

    print(f"--- Advancing Workflow Stage ---")
    print(f"  Current stage: {WORKFLOW_STAGES[current_stage_key]['name']}")
    print(f"  Next stage:    {next_stage['name']}")
    print(f"  Action:        Create the marker file '{next_stage['file']}'")

    if not args.yes:
        confirm = input("\nAre you sure you want to proceed? [y/N]: ").strip().lower()
        if confirm != 'y':
            print("Aborted.")
            sys.exit(0)

    try:
        marker_file_path.touch()
        print(f"\n✅ Successfully advanced workflow to '{next_stage['name']}'.")
    except OSError as e:
        print(f"\n❌ Error creating marker file: {e}", file=sys.stderr)
        sys.exit(1)


def _workflow_revert(args):
    """Reverts the project to the previous workflow stage."""
    project_dir = args.project_dir.resolve()
    current_stage_key = get_workflow_stage(project_dir)
    current_index = WORKFLOW_ORDER.index(current_stage_key)

    if current_stage_key == "IN_PROGRESS":
        print("Project is already at the initial 'In Progress' stage. Cannot revert further.")
        sys.exit(0)

    previous_stage_key = WORKFLOW_ORDER[current_index - 1]
    previous_stage = WORKFLOW_STAGES[previous_stage_key]
    marker_to_remove = WORKFLOW_STAGES[current_stage_key]["file"]
    marker_file_path = project_dir / marker_to_remove

    print(f"--- Reverting Workflow Stage ---")
    print(f"  Current stage:  {WORKFLOW_STAGES[current_stage_key]['name']}")
    print(f"  Previous stage: {previous_stage['name']}")
    print(f"  Action:         Delete the marker file '{marker_to_remove}'")

    if not args.yes:
        confirm = input("\nAre you sure you want to proceed? [y/N]: ").strip().lower()
        if confirm != 'y':
            print("Aborted.")
            sys.exit(0)

    try:
        marker_file_path.unlink()
        print(f"\n✅ Successfully reverted workflow to '{previous_stage['name']}'.")
    except FileNotFoundError:
        print(f"\n- Warning: Marker file '{marker_to_remove}' was already missing.", file=sys.stderr)
        print(f"  Workflow is now effectively at the '{previous_stage['name']}' stage.")
    except OSError as e:
        print(f"\n❌ Error deleting marker file: {e}", file=sys.stderr)
        sys.exit(1)


def run_workflow(args):
    """Manages the agent's high-level workflow state."""
    if args.action == "status":
        _workflow_status(args)
    elif args.action == "advance":
        _workflow_advance(args)
    elif args.action == "revert":
        _workflow_revert(args)
    sys.exit(0)


def run_shell(args):
    """Starts the interactive shell."""
    shell = InteractiveShell(sys.modules[__name__])
    shell.cmdloop()
    sys.exit(0)


def run_help(args):
    """Displays a structured and user-friendly help message."""
    # ANSI escape codes for formatting
    BOLD = '\033[1m'
    CYAN = '\033[96m'
    YELLOW = '\033[93m'
    ENDC = '\033[0m'

    def print_header(title):
        print(f"\n{BOLD}{CYAN}--- {title} ---{ENDC}")

    def print_command(name, description):
        print(f"  {YELLOW}{name:<20}{ENDC} {description}")

    executable_name = os.path.basename(sys.argv[0])
    print(f"{BOLD}Combined Autonomous Coding Agent{ENDC}")
    print("A unified CLI for running and managing autonomous coding agents.")
    print(f"\n{BOLD}Usage:{ENDC} {executable_name} [command] [options]")
    print(f"       {executable_name} --spec <spec_file> [options]  (to run the agent)")

    print_header("Getting Started")
    print_command("init", "Run an interactive setup wizard for a new project.")
    print_command("setup", "Install project dependencies based on the detected project type.")
    print_command("configure", "Create or update the global agent_config.yaml file.")
    print_command("doctor", "Run a health check on your environment and configuration.")
    print_command("list-agents", "List the available agent types (e.g., gemini, cursor).")
    print_command("models", "List recommended models for each agent type.")
    print_command("validate", "Validate the agent configuration file.")

    print_header("Core Commands")
    print_command("(run agent)", f"The default action. Use `main.py --spec <file>` to start.")
    print_command("plan", "Generate a feature plan from a spec file without executing code.")
    print_command("test", "Automatically detect project type and run tests.")
    print_command("lint", "Automatically detect project type and run a linter.")
    print_command("format", "Automatically detect project type and format code.")

    print_header("Inspection & History")
    print_command("status", "Show a detailed overview of the project's current status.")
    print_command("dashboard", "Display a comprehensive project dashboard.")
    print_command("history", "Show the history of agent runs for the project.")
    print_command("last", "Show a detailed summary of the very last agent run.")
    print_command("log", "Show the git commit history in a formatted view.")
    print_command("logs", "Show agent logs with filtering and real-time follow options.")
    print_command("tree", "Display a tree view of the project directory.")
    print_command("report", "Generate a Markdown summary report for a specific run.")
    print_command("blame", "Show which agent Run ID was responsible for each line in a file.")
    print_command("benchmark", "Analyze and compare performance metrics from different runs.")

    print_header("Git & Workflow")
    print_command("commit", "Stage all changes and create a commit, with interactive prompts.")
    print_command("push", "Safely push the current feature branch to the remote.")
    print_command("pull", "Safely pull the latest changes from the remote.")
    print_command("pr", "Manage GitHub pull requests for the project.")
    print_command("feature", "A guided workflow for branch -> commit -> push -> pr.")
    print_command("diff", "Show a detailed diff of uncommitted changes or a specific commit.")
    print_command("stash", "Stash uncommitted changes for later use.")
    print_command("discard", "Safely discard uncommitted changes by stashing them first.")
    print_command("undo", "Restore changes that were previously discarded.")
    print_command("rewind", "Reset the project state to a previous git commit or Run ID.")
    print_command("workflow", "Manually manage the agent's workflow state (e.g., advance to QA).")

    print_header("Artifact & Sprint Management")
    print_command("artifacts", "Manage trashed and archived agent-generated files.")
    print_command("snapshot", "Create and diff non-destructive snapshots of agent artifacts.")
    print_command("sprint", "Observe and manage the progress of a multi-agent sprint.")
    print_command("worktrees", "Manage git worktrees for concurrent sprint tasks.")

    print_header("Utilities")
    print_command("why", "Explain what a command does and why you might use it.")
    print_command("suggest", "Suggest the next logical command(s) based on project state.")
    print_command("shell", "Start an interactive shell with all commands available.")
    print_command("tui", "Start the interactive Textual User Interface (TUI).")
    print_command("show-config", "Show the final, resolved configuration that will be used for a run.")
    print_command("help", "Show this help message.")

    print(f"\nFor detailed options on a specific command, run: {executable_name} [command] --help")
    sys.exit(0)


def run_prompt_lab(args):
    """Runs the Prompt Lab TUI."""
    # Currently just launches the TUI, as it contains the Prompt Lab tab.
    # In future, this could launch directly into that tab or run headless experiments.
    run_tui(args)


def run_tui(args):
    """Starts the Textual TUI."""
    try:
        from shared.tui import AgentTUI
        app = AgentTUI(project_dir=args.project_dir)
        app.run()
        sys.exit(0)
    except ImportError as e:
        print("Error: Could not import TUI dependencies. Please run 'pip install -r requirements-dev.txt'", file=sys.stderr)
        print(f"Details: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred while running the TUI: {e}", file=sys.stderr)
        sys.exit(1)


def run_completion():
    """Prints the argcomplete shell script."""
    if argcomplete:
        executable_name = os.path.basename(sys.argv[0])
        print(argcomplete.shellcode([executable_name]))
        sys.exit(0)
    else:
        print("argcomplete is not installed. Please install it with 'pip install argcomplete'.", file=sys.stderr)
        sys.exit(1)




def _format_duration(seconds: float) -> str:
    """Formats seconds into a human-readable string (m s)."""
    seconds = float(seconds)
    minutes, seconds = divmod(seconds, 60)
    return f"{int(minutes)}m {seconds:.2f}s"


def run_cost(args):
    """Estimates the cost of the agent run based on token usage."""
    project_dir = args.project_dir.resolve()
    calculator = CostCalculator(project_dir)

    if args.budget:
        status = calculator.check_budget()
        print(f"--- Budget Status ---")
        if status['status'] == "No Limit":
             print("Status: No budget limit set in agent_config.yaml")
             print(f"Total Cost: ${status['current']:.4f}")
        else:
             print(f"Status:    {status['status']}")
             print(f"Limit:     ${status['limit']:.2f}")
             print(f"Used:      ${status['current']:.4f} ({status['percent']:.1f}%)")
             print(f"Remaining: ${status['remaining']:.4f}")
        print("")

    run_id = args.run_id
    if not run_id:
        # Default to latest run
        history_file = project_dir / ".agent_history"
        if history_file.exists():
            try:
                with open(history_file, "r") as f:
                    run_ids = [line.strip() for line in f if line.strip()]
                if run_ids:
                    run_id = run_ids[-1]
            except IOError:
                pass

    if not run_id:
        if args.budget:
            sys.exit(0)
        print("❌ Error: Could not determine Run ID.", file=sys.stderr)
        sys.exit(1)

    result = calculator.calculate_run_cost(run_id)
    if "error" in result:
        if args.budget:
            sys.exit(0)
        print(f"❌ Error: {result['error']}", file=sys.stderr)
        sys.exit(1)

    print(f"--- Cost Estimate for Run: {run_id} ---")
    print(f"Model:         {result['model']}")
    print(f"Input Tokens:  {int(result['input_tokens']):,}")
    print(f"Output Tokens: {int(result['output_tokens']):,}")
    print(f"Total Cost:    ${result['total_cost']:.4f}")

    sys.exit(0)


def _display_metrics_table(metrics: dict, title: str):
    """Displays a formatted table of metrics."""
    print(f"--- {title} ---")
    if not metrics:
        print("No metrics available.")
        return

    # Key metrics to display in a specific order
    key_metrics = [
        "Run ID", "Agent Type", "Model", "Timestamp",
        "Total Execution Time (s)", "Total Iterations",
        "Total Errors", "LLM API Calls", "LLM Tokens Used"
    ]

    # Format values for display
    display_data = {}
    for key, value in metrics.items():
        if "Time" in key and isinstance(value, (int, float)):
            display_data[key] = _format_duration(value)
        else:
            display_data[key] = value

    max_key_len = max(len(k) for k in key_metrics if k in metrics)

    for key in key_metrics:
        if key in metrics:
            print(f"  {key.ljust(max_key_len)} : {display_data.get(key, 'N/A')}")

    # Display any other metrics that weren't in the key list
    other_metrics = {k: v for k, v in metrics.items() if k not in key_metrics}
    if other_metrics:
        print("\n  --- Other Metrics ---")
        max_other_len = max(len(k) for k in other_metrics)
        for key, value in other_metrics.items():
            print(f"  {key.ljust(max_other_len)} : {display_data.get(key, 'N/A')}")


def _benchmark_show(args):
    """Handles the 'benchmark show' action."""
    run_id = args.run_id
    project_dir = args.project_dir.resolve()

    if not run_id:
        # If no run_id, use the metrics from the current project directory
        metrics_file = project_dir / "final_metrics.txt"
        if not metrics_file.exists():
            print("❌ Error: final_metrics.txt not found in the current project directory.", file=sys.stderr)
            print("Please specify a Run ID.", file=sys.stderr)
            sys.exit(1)
        metrics = _parse_metrics(metrics_file)
        if not metrics.get("Run ID"):
             print("❌ Error: Could not determine Run ID from final_metrics.txt.", file=sys.stderr)
             sys.exit(1)
        run_id = metrics["Run ID"]
    else:
        metrics_file = _find_metrics_file(run_id, project_dir)
        if not metrics_file:
            print(f"❌ Error: Could not find metrics for Run ID: {run_id}", file=sys.stderr)
            sys.exit(1)
        metrics = _parse_metrics(metrics_file)

    _display_metrics_table(metrics, f"Metrics for Run: {run_id}")
    sys.exit(0)


def _benchmark_compare(args):
    """Handles the 'benchmark compare' action."""
    project_dir = args.project_dir.resolve()
    run_id_1, run_id_2 = args.run_id_1, args.run_id_2

    file1 = _find_metrics_file(run_id_1, project_dir)
    file2 = _find_metrics_file(run_id_2, project_dir)

    if not file1:
        print(f"❌ Error: Could not find metrics for Run ID: {run_id_1}", file=sys.stderr)
        sys.exit(1)
    if not file2:
        print(f"❌ Error: Could not find metrics for Run ID: {run_id_2}", file=sys.stderr)
        sys.exit(1)

    metrics1 = _parse_metrics(file1)
    metrics2 = _parse_metrics(file2)

    all_keys = sorted(list(set(metrics1.keys()) | set(metrics2.keys())))
    numeric_keys = [
        "Total Execution Time (s)", "Total Iterations", "Total Errors",
        "LLM API Calls", "LLM Tokens Used"
    ]

    print(f"--- Comparison: {run_id_1} vs {run_id_2} ---")
    header = f"{'Metric':<30} | {'Run: ' + run_id_1:<25} | {'Run: ' + run_id_2:<25} | {'Difference'}"
    print(header)
    print("-" * len(header))

    for key in all_keys:
        val1 = metrics1.get(key, "N/A")
        val2 = metrics2.get(key, "N/A")

        diff_str = ""
        if key in numeric_keys and isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
            diff = val2 - val1
            is_improvement = (key != "Total Errors" and diff < 0) or (key == "Total Errors" and diff < 0)
            prefix = "✅ " if is_improvement else "🔻 "
            diff_str = f"{prefix}{diff:+.2f}"
            if "Time" in key:
                 val1_str = _format_duration(val1)
                 val2_str = _format_duration(val2)
                 diff_str = f"{prefix}{_format_duration(abs(diff))}"
            else:
                 val1_str = str(val1)
                 val2_str = str(val2)
        else:
            val1_str = str(val1)
            val2_str = str(val2)
            if val1_str != val2_str:
                diff_str = "(changed)"

        print(f"{key:<30} | {val1_str:<25} | {val2_str:<25} | {diff_str}")

    sys.exit(0)


def _benchmark_summary(args):
    """Handles the 'benchmark summary' action."""
    project_dir = args.project_dir.resolve()
    count = args.count
    history_file = project_dir / ".agent_history"

    if not history_file.exists():
        print("No .agent_history file found. Cannot generate summary.", file=sys.stderr)
        sys.exit(1)

    try:
        with open(history_file, 'r') as f:
            run_ids = [line.strip() for line in f if line.strip()]
    except IOError:
        print("Error reading .agent_history file.", file=sys.stderr)
        sys.exit(1)

    print(f"--- Metrics Summary (Last {count} Runs) ---")

    metrics_list = []
    for run_id in reversed(run_ids):
        if len(metrics_list) >= count:
            break
        metrics_file = _find_metrics_file(run_id, project_dir)
        if metrics_file:
            metrics_list.append(_parse_metrics(metrics_file))

    if not metrics_list:
        print("No metrics found for any runs in the history.")
        sys.exit(0)

    # Define columns and their widths
    columns = {
        "Run ID": 20,
        "Agent": 10,
        "Time": 12,
        "Iterations": 10,
        "Errors": 8,
        "Tokens": 10,
    }
    header = (
        f"{'Run ID':<{columns['Run ID']}} | "
        f"{'Agent':<{columns['Agent']}} | "
        f"{'Time':<{columns['Time']}} | "
        f"{'Iterations':<{columns['Iterations']}} | "
        f"{'Errors':<{columns['Errors']}} | "
        f"{'Tokens':<{columns['Tokens']}}"
    )
    print(header)
    print("-" * len(header))

    for metrics in metrics_list:
        run_id = metrics.get("Run ID", "N/A")
        agent = metrics.get("Agent Type", "N/A")
        time_val = _format_duration(metrics.get("Total Execution Time (s)", 0))
        iters = metrics.get("Total Iterations", "N/A")
        errors = metrics.get("Total Errors", "N/A")
        tokens = metrics.get("LLM Tokens Used", "N/A")

        row = (
            f"{str(run_id):<{columns['Run ID']}} | "
            f"{str(agent):<{columns['Agent']}} | "
            f"{str(time_val):<{columns['Time']}} | "
            f"{str(iters):<{columns['Iterations']}} | "
            f"{str(errors):<{columns['Errors']}} | "
            f"{str(tokens):<{columns['Tokens']}}"
        )
        print(row)

    sys.exit(0)


def run_benchmark(args):
    """Dispatches benchmark actions."""
    if args.action == "show":
        _benchmark_show(args)
    elif args.action == "compare":
        _benchmark_compare(args)
    elif args.action == "summary":
        _benchmark_summary(args)


def _sprint_status(args):
    """Displays the status of the current sprint."""
    import json
    import subprocess
    import shutil

    project_dir = args.project_dir.resolve()
    sprint_plan_path = project_dir / "sprint_plan.json"

    if not sprint_plan_path.exists():
        print("❌ Error: sprint_plan.json not found. Are you in a sprint project?", file=sys.stderr)
        sys.exit(1)

    try:
        with open(sprint_plan_path, 'r') as f:
            plan = json.load(f)
        tasks = plan.get("tasks", [])
    except (json.JSONDecodeError, IOError) as e:
        print(f"❌ Error reading or parsing sprint_plan.json: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"--- Sprint Status: {project_dir} ---")
    if plan.get("sprint_goal"):
        print(f"Goal: {plan['sprint_goal']}")

    if not tasks:
        print("\nNo tasks found in the sprint plan.")
        sys.exit(0)

    # Get worktree status
    active_worktrees = set()
    git_path = shutil.which("git")
    if git_path and (project_dir / ".git").is_dir():
        try:
            result = subprocess.run(
                [git_path, "-C", str(project_dir), "worktree", "list"],
                capture_output=True, text=True, check=True
            )
            for line in result.stdout.strip().split('\n'):
                parts = line.split()
                if len(parts) > 1 and "worktrees/" in parts[0]:
                    worktree_name = Path(parts[0]).name
                    active_worktrees.add(worktree_name)
        except subprocess.CalledProcessError:
            pass

    merged_branches = set()
    if git_path:
        try:
            main_branch = "main"
            try:
                subprocess.run([git_path, "-C", str(project_dir), "show-ref", "--verify", f"refs/heads/{main_branch}"], check=True, capture_output=True)
            except subprocess.CalledProcessError:
                main_branch = "master"

            result = subprocess.run(
                [git_path, "-C", str(project_dir), "branch", "--merged", main_branch],
                capture_output=True, text=True, check=True
            )
            for line in result.stdout.strip().split('\n'):
                branch_name = line.strip().lstrip('* ')
                if branch_name.startswith("sprint/task-"):
                    merged_branches.add(branch_name)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

    print("\n--- Tasks ---")
    header = f"{'ID':<20} | {'Status':<15} | {'Title'}"
    print(header)
    print("-" * (len(header) + 5))

    for task in tasks:
        task_id = task.get("id")
        title = task.get("title", "No Title")
        worktree_name = f"sprint-task-{task_id}"
        branch_name = f"sprint/task-{task_id}"

        status = "Pending"
        if branch_name in merged_branches:
            status = "✅ Merged"
        elif worktree_name in active_worktrees:
            status = "🏃 In Progress"

        print(f"{task_id:<20} | {status:<15} | {title}")

    sys.exit(0)


def run_branch(args):
    """Manages the agent's dedicated feature branch."""
    project_dir = args.project_dir.resolve()
    git_path = shutil.which("git")
    branch_file = project_dir / ".agent_branch"

    if not git_path or not (project_dir / ".git").is_dir():
        print("❌ Error: Not a git repository. Cannot manage branches.", file=sys.stderr)
        sys.exit(1)

    action = args.action
    branch_name = args.branch_name

    current_agent_branch = branch_file.read_text().strip() if branch_file.exists() else None

    if action == "create":
        if not branch_name:
            print("❌ Error: 'create' action requires a branch name.", file=sys.stderr)
            sys.exit(1)
        try:
            print(f"Creating and checking out new branch: {branch_name}")
            subprocess.run([git_path, "-C", str(project_dir), "checkout", "-b", branch_name], check=True, capture_output=True)
            branch_file.write_text(branch_name)
            print(f"✅ Agent branch set to '{branch_name}'.")
        except subprocess.CalledProcessError as e:
            stderr = e.stderr.decode().strip()
            print(f"❌ Error creating branch: {stderr}", file=sys.stderr)
            sys.exit(1)

    elif action == "checkout":
        if not branch_name:
            print("❌ Error: 'checkout' action requires a branch name.", file=sys.stderr)
            sys.exit(1)
        try:
            print(f"Checking out branch: {branch_name}")
            subprocess.run([git_path, "-C", str(project_dir), "checkout", branch_name], check=True, capture_output=True)
            branch_file.write_text(branch_name)
            print(f"✅ Agent branch set to '{branch_name}'.")
        except subprocess.CalledProcessError as e:
            stderr = e.stderr.decode().strip()
            print(f"❌ Error checking out branch: {stderr}", file=sys.stderr)
            sys.exit(1)

    elif action == "status":
        if current_agent_branch:
            print(f"Agent is currently working on branch: '{current_agent_branch}'")
        else:
            print("Agent is not configured to use a specific branch. Using default behavior.")

    elif action == "merge":
        if not current_agent_branch:
            print("❌ Error: No agent branch is set. Nothing to merge.", file=sys.stderr)
            sys.exit(1)

        main_branch = "main"
        try:
            subprocess.run([git_path, "-C", str(project_dir), "checkout", main_branch], check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            if "did not match any file(s) known to git" in e.stderr:
                main_branch = "master" # Fallback to master
                try:
                    subprocess.run([git_path, "-C", str(project_dir), "checkout", main_branch], check=True, capture_output=True, text=True)
                except subprocess.CalledProcessError as e2:
                    stderr = e2.stderr.strip()
                    print(f"❌ Error checking out '{main_branch}': {stderr}", file=sys.stderr)
                    sys.exit(1)
            else:
                stderr = e.stderr.strip()
                print(f"❌ Error checking out '{main_branch}': {stderr}", file=sys.stderr)
                sys.exit(1)

        print(f"Merging '{current_agent_branch}' into '{main_branch}'...")
        try:
            subprocess.run([git_path, "-C", str(project_dir), "merge", current_agent_branch], check=True, capture_output=True)
            print("✅ Merge successful.")
            if not args.keep_branch:
                print(f"Deleting branch '{current_agent_branch}'...")
                subprocess.run([git_path, "-C", str(project_dir), "branch", "-d", current_agent_branch], check=True, capture_output=True)
                branch_file.unlink()
                print("✅ Branch deleted and agent branch config removed.")
        except subprocess.CalledProcessError as e:
            stderr = e.stderr.decode().strip()
            print(f"❌ Error during merge: {stderr}", file=sys.stderr)
            print("Please resolve conflicts manually.")
            sys.exit(1)

    elif action == "list":
        print("--- Agent-Related Branches ---")
        if current_agent_branch:
            print(f"  * {current_agent_branch} (active)")
        try:
            result = subprocess.run([git_path, "-C", str(project_dir), "branch", "--list"], capture_output=True, text=True, check=True)
            for line in result.stdout.strip().split('\n'):
                line = line.strip()
                if line.startswith("*"):
                    line = line[2:]
                if line != current_agent_branch:
                    print(f"    {line}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error listing branches: {e.stderr}", file=sys.stderr)

    sys.exit(0)


async def run_recipes(args):
    """Manages and runs agent recipes."""
    from shared.recipes import RecipeManager

    project_dir = args.project_dir.resolve()
    manager = RecipeManager(project_dir)

    if args.action == "list":
        recipes = manager.list_recipes()
        if not recipes:
            print("No recipes found.")
            sys.exit(0)
        print("--- Available Recipes ---")
        for name, steps in recipes.items():
            print(f"\n🏷️  {name}")
            for i, step in enumerate(steps):
                print(f"  {i+1}. {step}")
        sys.exit(0)

    elif args.action == "show":
        if not args.name:
             print("Error: Name required for 'show' action.", file=sys.stderr)
             sys.exit(1)
        steps = manager.get_recipe(args.name)
        if not steps:
            print(f"Recipe '{args.name}' not found.", file=sys.stderr)
            sys.exit(1)
        print(f"--- Recipe: {args.name} ---")
        for i, step in enumerate(steps):
            print(f"  {i+1}. {step}")
        sys.exit(0)

    elif args.action == "run":
        if not args.name:
             print("Error: Name required for 'run' action.", file=sys.stderr)
             sys.exit(1)
        success = manager.run_recipe(args.name, dry_run=args.dry_run, known_commands=KNOWN_COMMANDS)
        sys.exit(0 if success else 1)

    elif args.action == "delete":
        if not args.name:
             print("Error: Name required for 'delete' action.", file=sys.stderr)
             sys.exit(1)
        if manager.delete_recipe(args.name):
            print(f"✅ Deleted recipe '{args.name}'.")
        else:
             print(f"Recipe '{args.name}' not found.", file=sys.stderr)
             sys.exit(1)

    elif args.action == "learn":
        from shared.recipe_learner import RecipeLearner
        learner = RecipeLearner(project_dir)
        success = await learner.learn_from_run(
            run_id=args.run_id,
            recipe_name=args.name,
            agent_type=args.agent,
            model=args.model
        )
        sys.exit(0 if success else 1)

    elif args.action == "record":
        print("--- Record New Recipe ---")
        name = args.name
        if not name:
            name = input("Recipe name: ").strip()
        if not name:
            print("Aborted.")
            sys.exit(1)

        print(f"Recording recipe '{name}'.")
        print("Type commands to execute. Type 'stop' or 'exit' to finish.")

        steps = []
        current_cwd = project_dir
        import subprocess
        import shlex

        while True:
            # Show prompt with relative path
            try:
                rel_path = current_cwd.relative_to(project_dir)
                prompt_path = f"./{rel_path}" if str(rel_path) != "." else "."
            except ValueError:
                prompt_path = str(current_cwd)

            try:
                cmd_line = input(f"{prompt_path} $ ").strip()
            except (EOFError, KeyboardInterrupt):
                break

            if not cmd_line:
                continue

            if cmd_line in ["stop", "exit"]:
                break

            # Handle cd
            parts = shlex.split(cmd_line)
            if parts and parts[0] == "cd":
                if len(parts) > 1:
                    target = parts[1]
                    new_path = (current_cwd / target).resolve()
                    if new_path.is_dir():
                        current_cwd = new_path
                        steps.append(cmd_line)
                        continue
                    else:
                        print(f"❌ Directory not found: {target}")
                        continue
                else:
                    # cd home -> default to project root for this tool's behavior
                    current_cwd = project_dir
                    steps.append(cmd_line)
                    continue

            # Execute
            try:
                # Check if it's an agent command
                is_agent_cmd = parts[0] in KNOWN_COMMANDS

                # Setup kwargs
                kwargs = {
                    "cwd": current_cwd,
                    "env": os.environ.copy(),
                    "text": True
                }

                if is_agent_cmd:
                    # Execute as agent command
                    executable = sys.executable
                    script = str(Path(sys.argv[0]).resolve())
                    cmd = [executable, script] + parts
                    res = subprocess.run(cmd, **kwargs)
                else:
                    # Execute as shell command
                    res = subprocess.run(cmd_line, shell=True, **kwargs)  # nosec B602

                if res.returncode == 0:
                    steps.append(cmd_line)
                else:
                    print(f"Command failed (exit code {res.returncode}).")
                    confirm = input("Add to recipe anyway? [y/N]: ").strip().lower()
                    if confirm == 'y':
                        steps.append(cmd_line)
            except Exception as e:
                print(f"Error executing command: {e}")

        if steps:
            if manager.add_recipe(name, steps):
                print(f"✅ Recipe '{name}' recorded with {len(steps)} steps.")
            else:
                print("❌ Failed to save recipe.")
        else:
            print("No steps recorded.")
        sys.exit(0)

    elif args.action == "create":
        print("--- Create New Recipe ---")
        name = args.name
        if not name:
            name = input("Recipe name: ").strip()
        if not name:
            print("Aborted.")
            sys.exit(1)

        print(f"Enter commands for recipe '{name}' (one per line).")
        print("Enter an empty line to finish.")
        steps = []
        while True:
            cmd = input(f"Step {len(steps)+1}> ").strip()
            if not cmd:
                break
            steps.append(cmd)

        if not steps:
            print("No steps provided. Aborted.")
            sys.exit(1)

        if manager.add_recipe(name, steps):
            print(f"✅ Recipe '{name}' created successfully.")
        else:
            print("❌ Error saving recipe.")
            sys.exit(1)


def run_hooks(args):
    """Manages git hooks for the project."""
    from shared.hooks import install_hooks, uninstall_hooks, run_hook_logic
    from shared.config_loader import load_config_from_file

    project_dir = args.project_dir.resolve()

    # Load config to get hooks definition
    config = load_config_from_file()
    hooks_config = config.get("git_hooks", {})

    if args.action == "install":
        success = install_hooks(project_dir, hooks_config)
        sys.exit(0 if success else 1)
    elif args.action == "uninstall":
        success = uninstall_hooks(project_dir)
        sys.exit(0 if success else 1)
    elif args.action == "run":
        hook_name = args.hook_name
        if not hook_name:
            # Fallback for manual run without args, usually pre-commit
            hook_name = "pre-commit"
        success = run_hook_logic(project_dir, hook_name, hooks_config)
        sys.exit(0 if success else 1)
    sys.exit(0)


def run_replay(args):
    """Replays an agent run."""
    from shared.replay import ReplayManager
    manager = ReplayManager(args.project_dir)
    manager.replay(args.run_id, speed=args.speed, auto=args.auto)
    sys.exit(0)


def run_git(args):
    """Acts as a proxy to run git commands within a specified task's worktree."""
    project_dir = args.project_dir.resolve()
    task_id = args.task
    git_command = args.git_args

    if not task_id:
        print("❌ Error: The '--task' argument is required.", file=sys.stderr)
        sys.exit(1)

    if not git_command:
        print("❌ Error: No git command provided.", file=sys.stderr)
        sys.exit(1)

    worktree_name = f"sprint-task-{task_id}"
    worktree_path = project_dir / "worktrees" / worktree_name

    git_path = shutil.which("git")
    if not git_path:
        print("❌ Error: 'git' command not found.", file=sys.stderr)
        sys.exit(1)

    if not worktree_path.is_dir():
        print(f"❌ Error: Worktree for task '{task_id}' not found at '{worktree_path}'.", file=sys.stderr)
        sys.exit(1)

    full_command = [git_path] + git_command

    try:
        # Execute the command from within the worktree directory, capturing output.
        result = subprocess.run(
            full_command,
            cwd=worktree_path,
            capture_output=True,
            text=True
        )
        # Print the captured output
        if result.stdout:
            sys.stdout.write(result.stdout)
        if result.stderr:
            sys.stderr.write(result.stderr)
        # Exit with the same code as the git command
        sys.exit(result.returncode)
    except FileNotFoundError:
        print(f"❌ Error: Command '{full_command[0]}' not found.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)


def run_test(args):
    """Detects the project type and runs the appropriate test command."""
    project_dir = args.project_dir.resolve()
    passthrough_args = args.test_args

    print(f"--- Running tests in: {project_dir} ---")

    # --- Smart Mode ---
    if hasattr(args, 'smart') and args.smart:
        # Smart mode currently only supports Python projects
        is_python = (project_dir / "pyproject.toml").exists() or \
                    (project_dir / "requirements.txt").exists()

        if is_python:
            print("🧠 Smart Mode Enabled: Analyzing changes to run relevant tests...")
            analyzer = ImpactAnalyzer(project_dir)
            print("Building dependency graph...")
            analyzer.build_graph()
            changed_files = analyzer.get_changed_files()

            if not changed_files:
                print("✅ No changed files detected. Skipping tests.")
                sys.exit(0)

            _, impacted_tests = analyzer.find_impacted_files(changed_files)

            if not impacted_tests:
                print("⚠️  No tests found that cover the changed files.")
                sys.exit(0)

            print(f"🎯 identified {len(impacted_tests)} relevant test file(s):")
            for t in impacted_tests:
                print(f"  - {t}")

            # Override command to run these tests
            if shutil.which("pytest"):
                full_command = ["pytest"] + list(impacted_tests)
                if passthrough_args:
                    full_command.extend(passthrough_args)

                print(f"Executing command: {' '.join(full_command)}")
                try:
                    result = subprocess.run(full_command, cwd=project_dir)
                    sys.exit(result.returncode)
                except Exception as e:
                    print(f"❌ Error running smart tests: {e}", file=sys.stderr)
                    sys.exit(1)
            else:
                print("❌ Smart mode requires 'pytest' to be installed.", file=sys.stderr)
                sys.exit(1)
        else:
             print("⚠️  Smart test mode is currently only supported for Python projects. Falling back to full suite.")

    # --- Project Detection ---
    command_base = []

    # 1. Node.js Project
    if (project_dir / "package.json").exists():
        print("Detected Node.js project.")
        # Prefer specific package managers if lock files exist
        if (project_dir / "yarn.lock").exists():
            command_base = ["yarn", "test"]
        elif (project_dir / "pnpm-lock.yaml").exists():
            command_base = ["pnpm", "test"]
        else:
            command_base = ["npm", "test"]

    # 2. Python Project
    elif (project_dir / "pyproject.toml").exists() or (project_dir / "requirements.txt").exists():
        print("Detected Python project.")
        # Prefer pytest if available
        if shutil.which("pytest"):
            command_base = ["pytest"]
        else:
            command_base = [sys.executable, "-m", "unittest", "discover"]

    # 3. Go Project
    elif (project_dir / "go.mod").exists():
        print("Detected Go project.")
        command_base = ["go", "test", "./..."]

    # --- Command Construction & Execution ---
    if not command_base:
        print("❌ Error: Could not detect a recognizable project type (Node.js, Python, Go).", file=sys.stderr)
        print("  Please ensure the project has a `package.json`, `pyproject.toml`, `requirements.txt`, or `go.mod` file.", file=sys.stderr)
        sys.exit(1)

    # Construct the full command
    full_command = command_base
    if passthrough_args:
        # npm requires a '--' separator before passing args to the script
        if command_base == ["npm", "test"]:
            full_command.append("--")
        full_command.extend(passthrough_args)


    print(f"Executing command: {' '.join(full_command)}")
    try:
        # Stream the output directly and run in the target project directory
        result = subprocess.run(full_command, cwd=project_dir)
        # Exit with the same code as the test runner
        sys.exit(result.returncode)

    except FileNotFoundError:
        print(f"❌ Error: Command '{full_command[0]}' not found. Is it installed and in your PATH?", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nTest execution interrupted by user.")
        sys.exit(130) # Standard exit code for Ctrl+C
    except Exception as e:
        print(f"❌ An unexpected error occurred while running tests: {e}", file=sys.stderr)
        sys.exit(1)


def run_lint(args):
    """Detects the project type and runs the appropriate linter."""
    project_dir = args.project_dir.resolve()
    passthrough_args = args.lint_args
    is_fix_mode = args.fix

    print(f"--- Running linters in: {project_dir} ---")

    # --- Project Detection ---
    command_base = []
    fix_flags = []

    # 1. Node.js Project
    if (project_dir / "package.json").exists():
        print("Detected Node.js project.")
        # Assumes a 'lint' script is defined in package.json
        # E.g., "lint": "eslint ."
        # E.g., "lint:fix": "eslint . --fix"
        if is_fix_mode:
            # Check for a dedicated fix script first
            try:
                with open(project_dir / "package.json", 'r') as f:
                    package_data = json.load(f)
                    if "lint:fix" in package_data.get("scripts", {}):
                         command_base = ["npm", "run", "lint:fix"]
                    else:
                         command_base = ["npm", "run", "lint"]
                         fix_flags = ["--", "--fix"]
            except (IOError, json.JSONDecodeError):
                 command_base = ["npm", "run", "lint"]
                 fix_flags = ["--", "--fix"]

        else:
            command_base = ["npm", "run", "lint"]

    # 2. Python Project
    elif (project_dir / "pyproject.toml").exists() or (project_dir / "requirements.txt").exists():
        print("Detected Python project.")
        if shutil.which("ruff"):
            command_base = ["ruff", "check", "."]
            if is_fix_mode:
                fix_flags = ["--fix"]
        elif shutil.which("flake8"):
            command_base = ["flake8", "."]
            if is_fix_mode:
                print("Warning: --fix is not supported by flake8. Ignoring.", file=sys.stderr)
        elif shutil.which("pylint"):
            # Pylint is harder to auto-configure well, but we can try
            command_base = ["pylint", str(project_dir)]
            if is_fix_mode:
                print("Warning: --fix is not supported by pylint. Ignoring.", file=sys.stderr)
        else:
             print("Warning: No Python linter (ruff, flake8, pylint) found in PATH.", file=sys.stderr)

    # --- Command Construction & Execution ---
    if not command_base:
        print("❌ Error: Could not detect a recognizable project type or find a suitable linter.", file=sys.stderr)
        sys.exit(1)

    # Construct the full command
    full_command = command_base + (fix_flags if is_fix_mode else []) + passthrough_args

    print(f"Executing command: {' '.join(full_command)}")
    try:
        # Stream the output directly and run in the target project directory
        result = subprocess.run(full_command, cwd=project_dir)
        sys.exit(result.returncode)

    except FileNotFoundError:
        print(f"❌ Error: Command '{full_command[0]}' not found. Is it installed and in your PATH?", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nLinting process interrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"❌ An unexpected error occurred while running linter: {e}", file=sys.stderr)
        sys.exit(1)


def run_format(args):
    """Detects the project type and runs the appropriate code formatter."""
    project_dir = args.project_dir.resolve()
    passthrough_args = args.format_args
    is_check_mode = args.check

    print(f"--- Running code formatter in: {project_dir} ---")

    # --- Project Detection ---
    command_base = []
    check_flags = []

    # 1. Python Project
    if (project_dir / "pyproject.toml").exists() or (project_dir / "setup.py").exists():
        print("Detected Python project.")
        if shutil.which("black"):
            command_base = ["black", "."]
            if is_check_mode:
                check_flags = ["--check"]
        else:
            print("Warning: Python formatter 'black' not found in PATH.", file=sys.stderr)

    # 2. Node.js Project (assuming Prettier)
    elif (project_dir / "package.json").exists():
        print("Detected Node.js project.")
        # Assumes prettier is installed locally or globally
        prettier_executable = None
        local_prettier = project_dir / "node_modules" / ".bin" / "prettier"
        if local_prettier.exists():
            prettier_executable = str(local_prettier)
        elif shutil.which("prettier"):
            prettier_executable = "prettier"
        elif shutil.which("npx"):
            prettier_executable = "npx prettier"


        if prettier_executable:
            command_base = [prettier_executable, "."]
            if is_check_mode:
                check_flags = ["--check"]
            else:
                check_flags = ["--write"] # Prettier's equivalent of formatting
        else:
            print("Warning: Node.js formatter 'prettier' not found.", file=sys.stderr)


    # --- Command Construction & Execution ---
    if not command_base:
        print("❌ Error: Could not detect a recognizable project type or find a suitable formatter.", file=sys.stderr)
        sys.exit(1)

    # Construct the full command
    full_command = command_base + check_flags + passthrough_args

    print(f"Executing command: {' '.join(full_command)}")
    try:
        # Stream the output directly and run in the target project directory
        result = subprocess.run(full_command, cwd=project_dir)
        sys.exit(result.returncode)

    except FileNotFoundError:
        print(f"❌ Error: Command '{full_command[0]}' not found. Is it installed and in your PATH?", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nFormatting process interrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"❌ An unexpected error occurred while running formatter: {e}", file=sys.stderr)
        sys.exit(1)


def run_sprint_command(args):
    """Dispatches sprint actions."""
    if args.action == "status":
        _sprint_status(args)
        sys.exit(0)

    if not args.task_id:
        print("❌ Error: 'diff' and 'merge' actions require a task_id.", file=sys.stderr)
        sys.exit(1)

    worktree_name = f"sprint-task-{args.task_id}"

    mock_args = argparse.Namespace(
        worktree_name=worktree_name,
        project_dir=args.project_dir,
        yes=getattr(args, 'yes', False),
        force=False,
        clean=getattr(args, 'clean', False)
    )

    project_dir = args.project_dir.resolve()
    worktrees_base_dir = project_dir / "worktrees"
    git_path = shutil.which("git")
    if not git_path:
        print("❌ Error: 'git' command not found.", file=sys.stderr)
        sys.exit(1)

    if args.action == "diff":
        _worktree_diff(mock_args, git_path, worktrees_base_dir)
    elif args.action == "merge":
        _worktree_merge(mock_args, git_path, project_dir, worktrees_base_dir)


async def run_plan(args):
    """Generates a feature plan from a spec file without executing it."""
    # This is a stripped down version of the main() function's setup
    logger, _ = setup_logger(name="plan_logger", log_file=None, verbose=args.verbose, console_output=True)

    logger.info("--- Generating Agent Plan ---")

    # Basic validation
    if not args.spec or not Path(args.spec).exists():
        logger.error("❌ Error: A valid --spec file is required for the 'plan' command.")
        sys.exit(1)

    # Load config from file to respect profiles and base settings
    ensure_config_exists()
    file_config = load_config_from_file(profile=args.profile)

    def resolve(cli_arg, config_key, default_val):
        if cli_arg is not None:
            return cli_arg
        if config_key in file_config:
            return file_config[config_key]
        return default_val

    # Create a minimal config for planning
    config = Config(
        project_dir=args.project_dir,
        agent_type=args.agent,
        model=resolve(args.model, "model", None),
        spec_file=args.spec,
        verbose=args.verbose,
        # Force settings for planning mode
        max_iterations=1,
        stream_output=False,
    )

    project_name = os.environ.get("PROJECT_NAME", config.project_dir.resolve().name)

    from shared.utils import generate_agent_id
    try:
        spec_content = config.spec_file.read_text()
        agent_id = generate_agent_id(project_name, spec_content, args.agent)
        config.agent_id = agent_id
    except Exception as e:
        logger.warning(f"Could not generate agent ID: {e}")
        config.agent_id = generate_agent_id(project_name, "", args.agent)

    logger.info(f"Generating plan for spec: {config.spec_file}")
    logger.info(f"Using agent: {config.agent_type}, Model: {config.model or 'default'}")

    # Dispatch to the correct agent type
    agent_class_map = {
        "gemini": GeminiAgent,
        "cursor": CursorAgent,
        "local": LocalAgent,
        "openrouter": OpenRouterAgent,
    }
    agent_class = agent_class_map.get(config.agent_type)

    if not agent_class:
        logger.error(f"Unknown agent type: {config.agent_type}")
        sys.exit(1)

    agent = agent_class(config)

    try:
        # This method will be created in the next step
        plan_generated = await agent.run_planning_session()

        if plan_generated:
            feature_file = config.project_dir / "feature_list.json"
            if feature_file.exists():
                logger.info("\n--- Generated Plan (feature_list.json) ---")
                # Use print to avoid logger formatting for the JSON output
                print(feature_file.read_text())
                logger.info("------------------------------------")
                logger.info("✅ Plan generated successfully.")
            else:
                logger.error("\n❌ Agent finished but did not produce a plan (feature_list.json).")
        else:
            logger.error("\n❌ Agent failed to generate a plan.")

    except Exception as e:
        logger.error(f"An error occurred during planning: {e}", exc_info=True)
        sys.exit(1)

    sys.exit(0)


def run_config(args):
    """Manages agent configuration settings."""
    config_dir = Path(platformdirs.user_config_dir("combined-autonomous-coding"))
    config_path = config_dir / "agent_config.yaml"
    config_dir.mkdir(parents=True, exist_ok=True)

    try:
        if config_path.exists():
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f) or {}
        else:
            config_data = {}
    except (IOError, yaml.YAMLError) as e:
        print(f"❌ Error reading configuration file: {e}", file=sys.stderr)
        return 1

    action = args.action
    key = args.key
    value = args.value

    if action == "list":
        print("--- Current Agent Configuration ---")
        if not config_data:
            print("Configuration is empty.")
        else:
            print(yaml.dump(config_data, indent=2, sort_keys=True))

    elif action == "get":
        if not key:
            print("❌ Error: 'get' action requires a key.", file=sys.stderr)
            return 1

        # Handle nested keys if necessary, e.g., 'jira.url'
        keys = key.split('.')
        current_level = config_data
        for k in keys:
            if isinstance(current_level, dict) and k in current_level:
                current_level = current_level[k]
            else:
                print(f"Key '{key}' not found in configuration.", file=sys.stderr)
                return 1

        print(current_level)

    elif action == "set":
        if not key or value is None:
            print("❌ Error: 'set' action requires a key and a value.", file=sys.stderr)
            return 1

        # Handle nested keys
        keys = key.split('.')
        current_level = config_data
        for i, k in enumerate(keys[:-1]):
            if k not in current_level or not isinstance(current_level.get(k), dict):
                current_level[k] = {}
            current_level = current_level[k]

        # Attempt to parse value as a number or boolean
        if value.lower() == 'true':
            parsed_value = True
        elif value.lower() == 'false':
            parsed_value = False
        else:
            try:
                # Try parsing as integer, then float
                parsed_value = int(value)
            except ValueError:
                try:
                    parsed_value = float(value)
                except ValueError:
                    parsed_value = value # Keep as string

        current_level[keys[-1]] = parsed_value

        try:
            with open(config_path, 'w') as f:
                yaml.dump(config_data, f, indent=2, sort_keys=True)
            os.chmod(config_path, 0o600)
            print(f"✅ Set '{key}' to '{parsed_value}'.")
        except (IOError, yaml.YAMLError) as e:
            print(f"❌ Error writing configuration file: {e}", file=sys.stderr)
            return 1

    return 0


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Autonomous Coding Agent")

    # Core Configuration
    core_group = parser.add_argument_group("Core Configuration")
    core_group.add_argument(
        "--profile",
        type=str,
        help="Select a configuration profile from agent_config.yaml.",
    )
    core_group.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="Directory where the project will be created/modified (default: current directory)",
    )
    core_group.add_argument(
        "-a", "--agent",
        choices=list(AVAILABLE_AGENTS.keys()),
        default="gemini",
        help="Which agent to use (default: gemini)",
    )
    core_group.add_argument(
        "-m", "--model",
        type=str,
        help="Model to use (overrides default). Can also be set via config.",
    )
    core_group.add_argument(
        "-s", "--spec",
        type=Path,
        help="Path to app_spec.txt (required for new projects)",
    )
    core_group.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    # Execution Control
    exec_group = parser.add_argument_group("Execution Control")
    exec_group.add_argument(
        "--max-iterations",
        type=int,
        help="Maximum number of agent iterations. Can also be set via config.",
    )
    exec_group.add_argument(
        "--timeout",
        type=float,
        help="Timeout in seconds for agent execution (default: 600.0). Can also be set via config.",
    )
    exec_group.add_argument(
        "--max-error-wait",
        type=float,
        help="Maximum wait time in seconds for agent error backoff (default: 600.0). Can also be set via config.",
    )
    exec_group.add_argument(
        "--no-stream",
        action="store_true",
        help="Disable streaming output",
    )

    # Manager Agent
    manager_group = parser.add_argument_group("Manager Agent")
    manager_group.add_argument(
        "--manager-frequency",
        type=int,
        help="How often the manager agent runs (default: 10 iterations). Can also be set via config.",
    )
    manager_group.add_argument(
        "--manager-model",
        type=str,
        help="Model to use for the manager agent. Can also be set via config.",
    )
    manager_group.add_argument(
        "--manager-first",
        action="store_true",
        help="Run the manager agent before the first coding session",
    )

    # Dashboard
    dash_group = parser.add_argument_group("Dashboard")
    dash_group.add_argument(
        "--no-dashboard",
        action="store_true",
        help="Disable the standalone dashboard server (enabled by default)",
    )
    dash_group.add_argument(
        "--dashboard-url",
        default="http://localhost:7654",
        help="URL of the dashboard server (default: http://localhost:7654)",
    )
    dash_group.add_argument(
        "--login",
        action="store_true",
        help="Run the agent in login/authentication mode (exit after login)",
    )

    # Sprint Mode
    sprint_group = parser.add_argument_group("Sprint Mode")
    sprint_group.add_argument(
        "--sprint",
        action="store_true",
        help="Run in Sprint Mode (Concurrent Agents)",
    )
    sprint_group.add_argument(
        "--max-agents",
        type=int,
        help="Maximum number of simultaneous agents in Sprint Mode. Can also be set via config.",
    )

    # Jira Integration
    jira_group = parser.add_argument_group("Jira Integration")
    jira_exclusive = jira_group.add_mutually_exclusive_group()
    jira_exclusive.add_argument(
        "--jira-ticket",
        type=str,
        help="Jira ticket ID to work on (e.g., PROJ-123)",
    )
    jira_exclusive.add_argument(
        "--jira-label",
        type=str,
        help="Jira label to search for (picks first 'To Do' ticket)",
    )

    # Advanced
    adv_group = parser.add_argument_group("Advanced")
    adv_group.add_argument(
        "--verify-creation",
        action="store_true",
        help="Run verification test (dummy mode)",
    )
    adv_group.add_argument(
        "--dind",
        "--docker-in-docker",
        action="store_true",
        help="Enable Docker-in-Docker support (mounts docker socket). Can also be set via config.",
    )
    adv_group.add_argument(
        "--dry-run",
        action="store_true",
        help="DEPRECATED: Use the 'show-config' command instead. Prints the final configuration and exits.",
    )

    # Subparsers for commands like 'configure'
    subparsers = parser.add_subparsers(dest="command", help="sub-command help")
    parser_configure = subparsers.add_parser("configure", help="Run interactive configuration setup")

    # Subparser for 'config'
    parser_config = subparsers.add_parser("config", help="Manage agent configuration settings")
    parser_config.add_argument("action", choices=["get", "set", "list"], help="Action to perform")
    parser_config.add_argument("key", nargs="?", help="The configuration key to get or set (e.g., 'model', 'jira.url')")
    parser_config.add_argument("value", nargs="?", help="The value to set for the specified key")

    parser_validate = subparsers.add_parser("validate", help="Validate the agent_config.yaml file")
    parser_list_agents = subparsers.add_parser("list-agents", help="List available agents")
    parser_show_config = subparsers.add_parser("show-config", help="Show the final resolved configuration and exit")

    # Subparser for 'models'
    parser_models = subparsers.add_parser("models", help="List recommended models for each agent")
    parser_models.add_argument(
        "-a", "--agent",
        choices=list(RECOMMENDED_MODELS.keys()),
        help="Filter models for a specific agent.",
    )

    # Subparser for 'doctor'
    parser_doctor = subparsers.add_parser("doctor", help="Run a comprehensive health check on the environment")
    parser_doctor.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to check (default: current directory)",
    )

    # Subparser for 'init'
    parser_init = subparsers.add_parser("init", help="Run an interactive setup wizard for a new project")
    parser_init.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to initialize (default: current directory)",
    )
    parser_init.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip all confirmation prompts",
    )

    # Subparser for 'adr'
    parser_adr = subparsers.add_parser("adr", help="Manage Architecture Decision Records (ADRs)")
    parser_adr.add_argument("action", choices=["init", "new", "list", "status", "generate"], help="Action to perform")
    parser_adr.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="The project directory")
    parser_adr.add_argument("title", nargs="?", help="Title for the new ADR")
    parser_adr.add_argument("--id", help="ADR ID or filename for updates")
    parser_adr.add_argument("--status", help="New status for the ADR")
    parser_adr.add_argument("--context", help="Context for AI generation")
    parser_adr.add_argument("-a", "--agent", choices=list(AVAILABLE_AGENTS.keys()), default="gemini", help="Agent to use for generation")
    parser_adr.add_argument("-m", "--model", type=str, help="Model to use for generation")

    # Subparser for 'status'
    # Subparser for 'glance'
    parser_glance = subparsers.add_parser("glance", help="Show a compact, high-level overview of the project status")
    parser_glance.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to check status for (default: current directory)",
    )

    # Subparser for 'status'
    parser_status = subparsers.add_parser("status", help="Show the current status of the agent project")
    parser_status.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to check status for (default: current directory)",
    )

    # Subparser for 'dashboard'
    parser_dashboard = subparsers.add_parser("dashboard", help="Show a comprehensive dashboard of the project status")
    parser_dashboard.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to display the dashboard for (default: current directory)",
    )
    parser_dashboard.add_argument(
        "--format",
        choices=["text", "html"],
        default="text",
        help="Output format (default: text)."
    )
    parser_dashboard.add_argument(
        "-o", "--output",
        default="dashboard.html",
        help="Output file path for HTML format (default: dashboard.html)."
    )

    # Subparser for 'summary'
    parser_summary = subparsers.add_parser("summary", help="Show a high-level summary of the agent project")
    parser_summary.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to summarize (default: current directory)",
    )

    # Subparser for 'suggest'
    parser_suggest = subparsers.add_parser("suggest", help="Suggest next logical commands based on project state")
    parser_suggest.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to analyze (default: current directory)",
    )

    # Subparser for 'history'
    parser_history = subparsers.add_parser("history", help="Show the history of agent runs for the project")
    parser_history.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to check history for (default: current directory)",
    )

    # Subparser for 'last'
    parser_last = subparsers.add_parser("last", help="Show a summary of the last agent run.")
    parser_last.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to check (default: current directory)",
    )

    # Subparser for 'last-run-id'
    parser_last_run_id = subparsers.add_parser("last-run-id", help="Print the ID of the last agent run to stdout.")
    parser_last_run_id.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to check (default: current directory)",
    )

    # Subparser for 'diff-summary'
    parser_diff_summary = subparsers.add_parser("diff-summary", help="Show a summary of uncommitted git changes")
    parser_diff_summary.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to check for changes (default: current directory)",
    )

    # Subparser for 'diff' (git diff)
    parser_diff = subparsers.add_parser("diff", help="Show a detailed diff of uncommitted changes or a specific commit")
    parser_diff.add_argument(
        "target",
        nargs="?",
        help="Optional: A git commit hash or agent Run ID to diff against.",
    )
    parser_diff.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to show the diff for (default: current directory)",
    )

    # Subparser for 'log' (git log)
    parser_log = subparsers.add_parser("log", help="Show the git commit history for the project")
    parser_log.add_argument(
        "-n", "--count",
        type=int,
        help="Number of recent commits to display.",
    )
    parser_log.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to show the log for (default: current directory)",
    )

    # Subparser for 'logs'
    parser_logs = subparsers.add_parser("logs", help="Show agent logs with advanced filtering")
    parser_logs.add_argument(
        "--explore",
        action="store_true",
        help="Open the interactive Log Explorer TUI.",
    )
    parser_logs.add_argument(
        "-a", "--agent",
        choices=list(AVAILABLE_AGENTS.keys()),
        default="gemini",
        help="Which agent to use for analysis (default: gemini)."
    )
    parser_logs.add_argument(
        "run_id",
        nargs="?",
        help="The Run ID of the log to view. If omitted, lists recent logs or operates on the latest.",
    )
    parser_logs.add_argument(
        "-n", "--lines",
        type=int,
        help="Number of recent lines to display.",
    )
    parser_logs.add_argument(
        "-f", "--follow",
        action="store_true",
        help="Follow the log output in real-time.",
    )
    parser_logs.add_argument(
        "-g", "--grep",
        type=str,
        help="Filter log lines to only those containing this string.",
    )

    # Subparser for 'clean'
    parser_clean = subparsers.add_parser("clean", help="Move agent-generated artifacts to a trash directory")
    parser_clean.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to clean (default: current directory)",
    )
    parser_clean.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation prompt",
    )
    clean_exclusive_group = parser_clean.add_mutually_exclusive_group()
    clean_exclusive_group.add_argument(
        "--force",
        action="store_true",
        help="Permanently delete artifacts instead of moving them to the trash directory",
    )
    clean_exclusive_group.add_argument(
        "--archive",
        action="store_true",
        help="Archive artifacts to the `.agent_archives/` directory instead of moving them to trash",
    )
    clean_exclusive_group.add_argument(
        "--list",
        action="store_true",
        help="List the artifacts that would be cleaned without taking any action",
    )

    # Subparser for 'archive'
    parser_archive = subparsers.add_parser("archive", help="Archive all agent-generated artifacts to a timestamped directory")
    parser_archive.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to clean (default: current directory)",
    )

    # Subparser for 'empty-trash'
    parser_empty_trash = subparsers.add_parser("empty-trash", help="DEPRECATED: Use 'trash clear --all' instead.")
    parser_empty_trash.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory where the trash is located (default: current directory)",
    )
    parser_empty_trash.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation prompt",
    )

    # Subparser for 'restore'
    parser_restore = subparsers.add_parser("restore", help="DEPRECATED: Use 'trash restore' instead.")
    parser_restore.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory where the trash is located (default: current directory)",
    )
    parser_restore.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation prompt",
    )

    # Subparser for 'trash'
    parser_trash = subparsers.add_parser("trash", help="Manage the agent trash directory")
    parser_trash.add_argument(
        "action",
        choices=["list", "restore", "clear", "inspect", "diff"],
        help="Action to perform on the trash",
    )

    # Subparser for 'discard'
    parser_discard = subparsers.add_parser("discard", help="Discard uncommitted changes to specified files or all files")
    parser_discard.add_argument(
        "files",
        nargs="*",
        help="Specific file(s) to discard. If not provided, all uncommitted changes will be discarded.",
    )
    parser_discard.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to discard changes in (default: current directory)",
    )
    parser_discard.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Interactively select which files to discard.",
    )
    parser_discard.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation prompt",
    )
    # Subparser for 'undo'
    parser_undo = subparsers.add_parser("undo", help="Undo a 'discard' operation by restoring the stashed changes.")
    parser_undo.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to run undo in (default: current directory)",
    )
    parser_trash.add_argument(
        "archive_name",
        nargs="?",
        help="The name of the trash archive to restore, clear, or inspect (e.g., trash-2023-10-27_12-30-00)",
    )
    parser_trash.add_argument(
        "file_name",
        nargs="?",
        help="The name of the file to inspect within the archive (for 'inspect' action only)",
    )
    parser_trash.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory where the trash is located",
    )
    parser_trash.add_argument(
        "--all",
        action="store_true",
        help="Option for 'clear' action to remove all archives",
    )
    parser_trash.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation prompts",
    )
    parser_trash.add_argument(
        "-n", "--dry-run",
        action="store_true",
        help="Show what would be done without making any changes",
    )

    # Subparser for 'revert'
    parser_revert = subparsers.add_parser("revert", help="Discard uncommitted changes to specified files or all files")
    parser_revert.add_argument(
        "files",
        nargs="*",
        help="Specific file(s) to revert. If not provided, all uncommitted changes will be discarded.",
    )
    parser_revert.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to revert changes in (default: current directory)",
    )
    parser_revert.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Interactively select which files to revert.",
    )
    parser_revert.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation prompt",
    )


    # Subparser for 'rewind'
    parser_rewind = subparsers.add_parser("rewind", help="Reset the project to a previous state (git commit)")
    parser_rewind.add_argument(
        "target",
        nargs="?",
        help="The git commit hash, reference (e.g., HEAD~2), or Run ID to rewind to. Launches interactive mode if omitted.",
    )
    parser_rewind.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to rewind (default: current directory)",
    )
    parser_rewind.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation prompt",
    )


    # Subparser for 'worktrees'
    parser_worktrees = subparsers.add_parser("worktrees", help="Manage agent-created git worktrees")
    parser_worktrees.add_argument(
        "action",
        choices=["list", "show", "clean", "revert", "create", "merge", "diff", "manage"],
        help="Action to perform on the worktrees",
    )
    parser_worktrees.add_argument(
        "worktree_name",
        nargs="?",
        help="The name of the worktree to create, show, or clean (e.g., 'agent-sprint-task-1')",
    )
    parser_worktrees.add_argument(
        "--branch",
        type=str,
        help="Specify a branch name to create for the worktree (for 'create' action)",
    )
    parser_worktrees.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory where the worktrees are located",
    )
    parser_worktrees.add_argument(
        "--force",
        action="store_true",
        help="Force removal of the worktree, even if it has uncommitted changes (for 'clean' action)",
    )
    parser_worktrees.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation prompts (for 'clean' action)",
    )
    parser_worktrees.add_argument(
        "--clean",
        action="store_true",
        help="Remove the worktree after a successful merge (for 'merge' action)",
    )

    # Subparser for 'snapshot'
    parser_snapshot = subparsers.add_parser("snapshot", help="Manage snapshots of key agent artifacts")
    parser_snapshot.add_argument(
        "action",
        choices=["create", "diff"],
        help="Action to perform: 'create' a new snapshot or 'diff' against an existing one.",
    )
    parser_snapshot.add_argument(
        "name",
        nargs="?",
        help="Name of the snapshot. Optional for 'create', required for 'diff'.",
    )
    parser_snapshot.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory (default: current directory)",
    )
    parser_snapshot.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation prompt for 'create' action",
    )

    # Subparser for 'archives' - mirrors 'trash' but for .agent_archives/
    parser_archives = subparsers.add_parser("archives", help="Manage the agent archives directory")
    parser_archives.add_argument(
        "action",
        choices=["list", "restore", "clear", "inspect", "diff"],
        help="Action to perform on the archives",
    )
    parser_archives.add_argument(
        "archive_name",
        nargs="?",
        help="The name of the archive to restore, clear, or inspect",
    )
    parser_archives.add_argument(
        "file_name",
        nargs="?",
        help="The name of the file to inspect or diff within the archive",
    )
    parser_archives.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory where the archives are located",
    )
    parser_archives.add_argument(
        "--all",
        action="store_true",
        help="Option for 'clear' action to remove all archives",
    )
    parser_archives.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation prompts",
    )
    parser_archives.add_argument(
        "-n", "--dry-run",
        action="store_true",
        help="Show what would be done without making any changes",
    )

    # --- New 'artifacts' command ---
    parser_artifacts = subparsers.add_parser(
        "artifacts",
        help="Unified command to manage agent-generated artifacts (trash and archives)"
    )
    artifacts_subparsers = parser_artifacts.add_subparsers(
        dest="type",
        required=True,
        help="Specify artifact type"
    )

    def add_artifact_actions(subparser):
        """Helper to add common action arguments to trash/archive subparsers."""
        subparser.add_argument(
            "action",
            choices=["list", "restore", "clear", "inspect", "diff"],
            help="Action to perform on the artifacts",
        )
        subparser.add_argument(
            "archive_name",
            nargs="?",
            help="The name of the archive to restore, clear, or inspect",
        )
        subparser.add_argument(
            "file_name",
            nargs="?",
            help="The name of the file to inspect or diff within the archive",
        )
        subparser.add_argument(
            "-p", "--project-dir",
            type=Path,
            default=Path("."),
            help="The project directory where the artifacts are located",
        )
        subparser.add_argument(
            "--all",
            action="store_true",
            help="Option for 'clear' action to remove all archives",
        )
        subparser.add_argument(
            "-y", "--yes",
            action="store_true",
            help="Skip confirmation prompts",
        )
        subparser.add_argument(
            "-n", "--dry-run",
            action="store_true",
            help="Show what would be done without making any changes",
        )

    # Trash sub-command for 'artifacts'
    parser_artifacts_trash = artifacts_subparsers.add_parser(
        "trash",
        help="Manage the agent trash directory (.agent_trash)"
    )
    add_artifact_actions(parser_artifacts_trash)

    # Archive sub-command for 'artifacts'
    parser_artifacts_archive = artifacts_subparsers.add_parser(
        "archive",
        help="Manage the agent archives directory (.agent_archives)"
    )
    add_artifact_actions(parser_artifacts_archive)

    # --- New 'workflow' command ---
    parser_workflow = subparsers.add_parser(
        "workflow",
        help="Manually manage the agent's high-level workflow state (e.g., advancing from QA to Sign-off)."
    )
    parser_workflow.add_argument(
        "action",
        choices=["status", "advance", "revert"],
        help="Action to perform: 'status' to check, 'advance' to move forward, 'revert' to move back.",
    )
    parser_workflow.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to manage the workflow for (default: current directory)",
    )
    parser_workflow.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation prompts for 'advance' or 'revert' actions.",
    )


    # --- New 'plan' command ---
    parser_plan = subparsers.add_parser(
        "plan",
        help="Generate a feature plan from a spec file without executing any code."
    )
    parser_plan.add_argument(
        "-s", "--spec",
        type=Path,
        required=True,
        help="Path to the application specification file (e.g., app_spec.txt).",
    )
    parser_plan.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="Directory where the plan file will be generated (default: current directory).",
    )
    parser_plan.add_argument(
        "-a", "--agent",
        choices=list(AVAILABLE_AGENTS.keys()),
        default="gemini",
        help="Which agent to use for planning (default: gemini).",
    )
    parser_plan.add_argument(
        "-m", "--model",
        type=str,
        help="Model to use for planning (overrides agent's default).",
    )
    parser_plan.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging during the planning phase.",
    )
    parser_plan.add_argument(
        "--profile",
        type=str,
        help="Select a configuration profile from agent_config.yaml.",
    )

    # Subparser for 'shell'
    parser_shell = subparsers.add_parser("shell", help="Start an interactive shell session")

    # Subparser for 'tui'
    parser_tui = subparsers.add_parser("tui", help="Start the interactive Textual TUI")
    parser_tui.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to view in the TUI (default: current directory)",
    )

    # Subparser for 'prompt-lab'
    parser_prompt_lab = subparsers.add_parser("prompt-lab", help="Run the Prompt Engineering Lab.")
    parser_prompt_lab.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory (default: current directory).",
    )

    # Subparser for 'tree'
    parser_tree = subparsers.add_parser("tree", help="Show a tree view of the project directory")
    parser_tree.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to display (default: current directory)",
    )
    parser_tree.add_argument(
        "--depth",
        type=int,
        help="Limit the depth of the directory traversal.",
    )
    parser_tree.add_argument(
        "--full",
        action="store_true",
        help="Show all files, including those ignored by Git.",
    )

    # --- New 'completion' command ---
    parser_completion = subparsers.add_parser(
        "completion",
        help="Display shell completion scripts. To install, use: 'eval \"$(main.py completion)\"'",
    )

    # --- New 'cost' command ---
    parser_cost = subparsers.add_parser(
        "cost",
        help="Estimate the cost of an agent run based on token usage."
    )
    parser_cost.add_argument(
        "run_id",
        nargs="?",
        help="The Run ID to estimate. If omitted, uses the latest run.",
    )
    parser_cost.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory.",
    )
    parser_cost.add_argument(
        "-b", "--budget",
        action="store_true",
        help="Show budget status (total cost vs limit).",
    )

    # --- New 'benchmark' command ---
    parser_benchmark = subparsers.add_parser(
        "benchmark",
        help="Analyze and compare performance metrics from agent runs."
    )
    benchmark_subparsers = parser_benchmark.add_subparsers(
        dest="action",
        required=True,
        help="Specify benchmark action"
    )

    # Benchmark 'show' action
    parser_benchmark_show = benchmark_subparsers.add_parser(
        "show",
        help="Display performance metrics for a specific agent run."
    )
    parser_benchmark_show.add_argument(
        "run_id",
        nargs="?",
        help="The Run ID to inspect. If omitted, shows metrics for the latest run in the current project.",
    )
    parser_benchmark_show.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory where the run occurred.",
    )

    # Benchmark 'compare' action
    parser_benchmark_compare = benchmark_subparsers.add_parser(
        "compare",
        help="Compare the performance metrics of two agent runs side-by-side."
    )
    parser_benchmark_compare.add_argument("run_id_1", help="The first Run ID for comparison.")
    parser_benchmark_compare.add_argument("run_id_2", help="The second Run ID for comparison.")
    parser_benchmark_compare.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory where the runs occurred.",
    )

    # Benchmark 'summary' action
    parser_benchmark_summary = benchmark_subparsers.add_parser(
        "summary",
        help="Display a summary table of metrics from recent agent runs."
    )
    parser_benchmark_summary.add_argument(
        "-n", "--count",
        type=int,
        default=10,
        help="Number of recent runs to include in the summary (default: 10).",
    )
    parser_benchmark_summary.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to generate the summary from.",
    )

    # --- New 'sprint' command ---
    parser_sprint = subparsers.add_parser(
        "sprint",
        help="Observe and manage sprint progress."
    )
    sprint_subparsers = parser_sprint.add_subparsers(
        dest="action",
        required=True,
        help="Specify sprint action"
    )

    # Sprint 'status' action
    parser_sprint_status = sprint_subparsers.add_parser(
        "status",
        help="Display the status of all tasks in the current sprint."
    )
    parser_sprint_status.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory for the sprint.",
    )

    # Sprint 'diff' action
    parser_sprint_diff = sprint_subparsers.add_parser(
        "diff",
        help="Show the git diff for a specific sprint task."
    )
    parser_sprint_diff.add_argument("task_id", help="The ID of the task to diff.")
    parser_sprint_diff.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory for the sprint.",
    )

    # Sprint 'merge' action
    parser_sprint_merge = sprint_subparsers.add_parser(
        "merge",
        help="Merge a completed sprint task back into the main branch."
    )
    parser_sprint_merge.add_argument("task_id", help="The ID of the task to merge.")
    parser_sprint_merge.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory for the sprint.",
    )
    parser_sprint_merge.add_argument(
        "--clean",
        action="store_true",
        help="Remove the worktree and branch after a successful merge.",
    )
    parser_sprint_merge.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation prompts.",
    )

    # --- New 'branch' command ---
    parser_branch = subparsers.add_parser(
        "branch",
        help="Manage a dedicated feature branch for the agent to work on."
    )
    parser_branch.add_argument(
        "action",
        choices=["create", "checkout", "status", "merge", "list"],
        help="Action to perform.",
    )
    parser_branch.add_argument(
        "branch_name",
        nargs="?",
        help="The name of the branch to create or checkout.",
    )
    parser_branch.add_argument(
        "--keep-branch",
        action="store_true",
        help="Do not delete the branch after a successful merge.",
    )
    parser_branch.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory.",
    )

    # --- New 'mutate' command ---
    parser_mutate = subparsers.add_parser(
        "mutate",
        help="Run mutation testing to evaluate test suite quality."
    )
    parser_mutate.add_argument(
        "target_file",
        help="The file to mutate."
    )
    parser_mutate.add_argument(
        "--test-command",
        help="Custom test command (e.g. 'pytest tests/'). If omitted, auto-detected."
    )
    parser_mutate.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory.",
    )

    # --- New 'history-graph' command ---
    parser_history_graph = subparsers.add_parser(
        "history-graph",
        help="Visualize agent history as a graph."
    )
    parser_history_graph.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory.",
    )
    parser_history_graph.add_argument(
        "-m", "--metric",
        choices=["tokens", "duration", "errors", "iterations"],
        default="tokens",
        help="The metric to visualize (default: tokens)."
    )
    parser_history_graph.add_argument(
        "-l", "--limit",
        type=int,
        default=10,
        help="Number of recent runs to show (default: 10)."
    )

    # --- New 'test' command ---
    parser_test = subparsers.add_parser(
        "test",
        help="Automatically detect and run tests for the project."
    )
    # --- New 'report' command ---
    parser_report = subparsers.add_parser(
        "report",
        help="Generate a summary report for a specific agent run."
    )
    parser_report.add_argument(
        "run_id",
        help="The Run ID to generate the report for.",
    )
    parser_report.add_argument(
        "-o", "--output",
        type=Path,
        help="Path to save the Markdown report file. If omitted, prints to console.",
    )
    parser_report.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory where the run occurred.",
    )
    parser_test.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to run tests in (default: current directory).",
    )
    parser_test.add_argument(
        "--smart",
        action="store_true",
        help="Run only tests affected by recent changes (smart test selection).",
    )
    parser_test.add_argument(
        "test_args",
        nargs=argparse.REMAINDER,
        help="Arguments to pass through to the underlying test runner (e.g., specific files, flags).",
    )

    # --- New 'lint' command ---
    parser_lint = subparsers.add_parser(
        "lint",
        help="Automatically detect and run linters for the project."
    )
    parser_lint.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to run linters in (default: current directory).",
    )
    parser_lint.add_argument(
        "--fix",
        action="store_true",
        help="Attempt to automatically fix linting issues.",
    )
    parser_lint.add_argument(
        "lint_args",
        nargs=argparse.REMAINDER,
        help="Arguments to pass through to the underlying linter (e.g., specific files, flags).",
    )

    # --- New 'format' command ---
    parser_format = subparsers.add_parser(
        "format",
        help="Automatically detect and format code for the project."
    )
    parser_format.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to format (default: current directory).",
    )
    parser_format.add_argument(
        "--check",
        action="store_true",
        help="Run the formatter in check-only mode (dry run).",
    )
    parser_format.add_argument(
        "format_args",
        nargs=argparse.REMAINDER,
        help="Arguments to pass through to the underlying formatter (e.g., specific files, flags).",
    )

    # --- New 'hooks' command ---
    parser_hooks = subparsers.add_parser(
        "hooks",
        help="Manage git hooks (pre-commit) for the project."
    )
    hooks_subparsers = parser_hooks.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # Hooks 'install' action
    parser_hooks_install = hooks_subparsers.add_parser(
        "install",
        help="Install the agent's pre-commit hook."
    )
    parser_hooks_install.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory.",
    )

    # Hooks 'uninstall' action
    parser_hooks_uninstall = hooks_subparsers.add_parser(
        "uninstall",
        help="Uninstall the agent's pre-commit hook."
    )
    parser_hooks_uninstall.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory.",
    )

    # Hooks 'run' action
    parser_hooks_run = hooks_subparsers.add_parser(
        "run",
        help="Manually run a hook."
    )
    parser_hooks_run.add_argument(
        "hook_name",
        nargs="?",
        help="Name of the hook to run (e.g., pre-commit)."
    )
    parser_hooks_run.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory.",
    )

    # --- New 'replay' command ---
    parser_replay = subparsers.add_parser(
        "replay",
        help="Replay an agent run interactively."
    )
    parser_replay.add_argument(
        "run_id",
        nargs="?",
        help="The Run ID to replay (defaults to latest).",
    )
    parser_replay.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory.",
    )
    parser_replay.add_argument(
        "--speed",
        type=float,
        default=0.5,
        help="Speed for auto-play (seconds delay between turns).",
    )
    parser_replay.add_argument(
        "--auto",
        action="store_true",
        help="Auto-play without waiting for user input.",
    )

    # --- New 'recipes' command ---
    parser_recipes = subparsers.add_parser(
        "recipes",
        aliases=["macro"],
        help="Manage and run agent recipes (sequences of commands)."
    )
    parser_recipes.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory.",
    )
    recipes_subparsers = parser_recipes.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # Recipes 'list'
    recipes_subparsers.add_parser("list", help="List available recipes.")

    # Recipes 'show'
    parser_recipes_show = recipes_subparsers.add_parser("show", help="Show steps in a recipe.")
    parser_recipes_show.add_argument("name", help="Name of the recipe.")

    # Recipes 'run'
    parser_recipes_run = recipes_subparsers.add_parser("run", help="Execute a recipe.")
    parser_recipes_run.add_argument("name", help="Name of the recipe.")
    parser_recipes_run.add_argument("--dry-run", action="store_true", help="Print commands without executing.")

    # Recipes 'learn'
    parser_recipes_learn = recipes_subparsers.add_parser("learn", help="Learn a recipe from a previous agent run.")
    parser_recipes_learn.add_argument("name", help="Name for the new recipe.")
    parser_recipes_learn.add_argument("--run-id", help="The Run ID to learn from (defaults to latest).")
    parser_recipes_learn.add_argument("-a", "--agent", choices=list(AVAILABLE_AGENTS.keys()), default="gemini", help="Agent to use for analysis.")
    parser_recipes_learn.add_argument("-m", "--model", type=str, help="Model to use.")

    # Recipes 'record'
    parser_recipes_record = recipes_subparsers.add_parser("record", help="Record a new recipe by executing commands.")
    parser_recipes_record.add_argument("name", nargs="?", help="Name of the recipe.")

    # Recipes 'create'
    parser_recipes_create = recipes_subparsers.add_parser("create", help="Create a new recipe interactively.")
    parser_recipes_create.add_argument("name", nargs="?", help="Name of the recipe.")

    # Recipes 'delete'
    parser_recipes_delete = recipes_subparsers.add_parser("delete", help="Delete a recipe.")
    parser_recipes_delete.add_argument("name", help="Name of the recipe.")

    # --- New 'git' command ---
    parser_git = subparsers.add_parser(
        "git",
        help="Run git commands within a specific task's worktree."
    )
    parser_git.add_argument(
        "-t", "--task",
        required=True,
        help="The task ID corresponding to the worktree."
    )
    parser_git.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory where the worktrees are located.",
    )
    parser_git.add_argument(
        "git_args",
        nargs=argparse.REMAINDER,
        help="The git command and its arguments to run.",
    )

    # --- New 'push' command ---
    parser_push = subparsers.add_parser(
        "push",
        help="Push the current feature branch to the remote repository with safety checks."
    )
    parser_push.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to run the push command in (default: current directory).",
    )

    # --- New 'pull' command ---
    parser_pull = subparsers.add_parser(
        "pull",
        help="Pull the latest changes from the remote repository with safety checks."
    )
    parser_pull.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to run the pull command in (default: current directory).",
    )

    # --- New 'patch' command ---
    parser_patch = subparsers.add_parser(
        "patch",
        help="Apply a patch from a file or stdin."
    )
    parser_patch.add_argument(
        "patch_file",
        nargs="?",
        help="The path to the .patch file. If omitted, reads from stdin."
    )
    parser_patch.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory (default: current directory).",
    )
    parser_patch.add_argument(
        "-R", "--reverse",
        action="store_true",
        help="Apply the patch in reverse (unpatch)."
    )

    # --- New 'issues' command ---
    parser_issues = subparsers.add_parser(
        "issues",
        help="List and manage GitHub issues."
    )
    parser_issues.add_argument(
        "--state",
        choices=["open", "closed", "all"],
        default="open",
        help="Filter issues by state (default: open)."
    )
    parser_issues.add_argument(
        "--assignee",
        help="Filter by assignee (username, 'none', or '*')."
    )
    parser_issues.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Enable interactive mode to select an issue and start working."
    )
    parser_issues.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory.",
    )
    parser_issues.add_argument(
        "--profile",
        type=str,
        help="Select a configuration profile from agent_config.yaml.",
    )

    # --- New 'pr' command ---
    parser_pr = subparsers.add_parser(
        "pr",
        help="Manage GitHub pull requests for the project."
    )
    pr_subparsers = parser_pr.add_subparsers(
        dest="action",
        required=True,
        help="Specify pr action"
    )

    # PR 'create' action
    parser_pr_create = pr_subparsers.add_parser(
        "create",
        help="Create a new pull request on GitHub."
    )
    parser_pr_create.add_argument(
        "--title",
        required=True,
        help="The title of the pull request."
    )
    parser_pr_create.add_argument(
        "--body",
        default="",
        help="The body content of the pull request."
    )
    parser_pr_create.add_argument(
        "--base",
        default="main",
        help="The base branch to merge into (default: main)."
    )
    parser_pr_create.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory.",
    )

    # --- New 'commit' command ---
    parser_commit = subparsers.add_parser(
        "commit",
        help="Stage all changes and create a git commit with safety checks."
    )
    parser_commit.add_argument(
        "-m", "--message",
        required=False,
        help="The commit message. If not provided, an interactive prompt will be shown."
    )
    parser_commit.add_argument(
        "-g", "--generate",
        action="store_true",
        help="Generate a commit message using AI based on the staged changes."
    )
    parser_commit.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation for AI-generated message."
    )
    parser_commit.add_argument(
        "-a", "--agent",
        choices=list(AVAILABLE_AGENTS.keys()),
        default="gemini",
        help="Which agent to use for message generation (default: gemini)."
    )
    parser_commit.add_argument(
        "--model",
        type=str,
        help="Model to use for generation (overrides default)."
    )
    parser_commit.add_argument(
        "--run-tests",
        action="store_true",
        help="Run project tests before committing. If tests fail, the commit is aborted."
    )
    parser_commit.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to run the commit command in (default: current directory).",
    )

    # --- New 'feature' command ---
    parser_feature = subparsers.add_parser(
        "feature",
        help="Run a guided workflow for a new feature: branch -> commit -> push -> pr."
    )
    parser_feature.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory for the feature.",
    )

    # --- New 'interact' command ---
    parser_interact = subparsers.add_parser(
        "interact",
        help="Start an interactive session to run common commands."
    )
    parser_interact.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory for the interactive session.",
    )

    # --- New 'profile' command ---
    parser_profile = subparsers.add_parser(
        "profile",
        help="Manage configuration profiles."
    )
    parser_profile.add_argument(
        "action",
        choices=["list", "create", "show", "delete"],
        help="Action to perform on profiles.",
    )
    parser_profile.add_argument(
        "profile_name",
        nargs="?",
        help="The name of the profile to create, show, or delete.",
    )
    parser_profile.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation prompts for 'delete' action.",
    )

    # --- New 'watch' command ---
    parser_watch = subparsers.add_parser(
        "watch",
        help="Watch for file changes and run a command."
    )
    parser_watch.add_argument(
        "watch_command",
        nargs=argparse.REMAINDER,
        help="The command to run when a file changes.",
    )
    parser_watch.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to watch.",
    )

    # --- New 'why' command ---
    parser_why = subparsers.add_parser(
        "why",
        help="Explain what a command does and why you might use it."
    )
    parser_why.add_argument(
        "command_name",
        nargs="?",
        help="The command you want an explanation for.",
    )

    # --- New 'next' command ---
    parser_next = subparsers.add_parser(
        "next",
        help="Suggest and execute the next logical command in the workflow."
    )
    parser_next.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to analyze (default: current directory).",
    )

    # --- New 'optimize' command ---
    parser_optimize = subparsers.add_parser(
        "optimize",
        help="Profile a Python script and suggest AI-driven optimizations."
    )
    parser_optimize.add_argument(
        "script",
        help="The Python script to optimize."
    )
    parser_optimize.add_argument(
        "args",
        nargs=argparse.REMAINDER,
        help="Arguments to pass to the script."
    )
    parser_optimize.add_argument(
        "-a", "--agent",
        choices=list(AVAILABLE_AGENTS.keys()),
        default="gemini",
        help="Which agent to use (default: gemini)."
    )
    parser_optimize.add_argument(
        "-m", "--model",
        type=str,
        help="Model to use (overrides default)."
    )
    parser_optimize.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory (default: current directory)."
    )

    # --- New 'prune' command ---
    parser_prune = subparsers.add_parser(
        "prune",
        help="Identify and remove unused code and dependencies."
    )
    parser_prune.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory."
    )

    # --- New 'quiz' command ---
    parser_quiz = subparsers.add_parser(
        "quiz",
        help="Run an interactive codebase quiz."
    )
    parser_quiz.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory."
    )
    parser_quiz.add_argument(
        "--tui",
        action="store_true",
        help="Run in TUI mode."
    )

    # PR 'list' action
    parser_pr_list = pr_subparsers.add_parser(
        "list",
        help="List open pull requests."
    )
    parser_pr_list.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory."
    )

    # PR 'show' action
    parser_pr_show = pr_subparsers.add_parser(
        "show",
        help="Show details of a pull request."
    )
    parser_pr_show.add_argument(
        "number",
        type=int,
        help="The pull request number."
    )
    parser_pr_show.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory."
    )

    # PR 'merge' action
    parser_pr_merge = pr_subparsers.add_parser(
        "merge",
        help="Merge a pull request."
    )
    parser_pr_merge.add_argument(
        "number",
        type=int,
        help="The pull request number."
    )
    parser_pr_merge.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation."
    )
    parser_pr_merge.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory."
    )

    # PR 'close' action
    parser_pr_close = pr_subparsers.add_parser(
        "close",
        help="Close a pull request without merging."
    )
    parser_pr_close.add_argument(
        "number",
        type=int,
        help="The pull request number."
    )
    parser_pr_close.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation."
    )
    parser_pr_close.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory."
    )
    parser_prune.add_argument(
        "--types",
        type=str,
        help="Comma-separated list of types to prune (deps, files). Default: all."
    )
    parser_prune.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be removed without making changes."
    )
    parser_prune.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation prompt."
    )

    # --- New 'debug' command ---
    parser_debug = subparsers.add_parser(
        "debug",
        help="Execute a command and ask the agent to explain failures."
    )
    parser_debug.add_argument(
        "-a", "--agent",
        choices=list(AVAILABLE_AGENTS.keys()),
        default="gemini",
        help="Which agent to use (default: gemini)."
    )
    parser_debug.add_argument(
        "-m", "--model",
        type=str,
        help="Model to use (overrides default)."
    )
    parser_debug.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging."
    )
    parser_debug.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory (default: current directory)."
    )
    parser_debug.add_argument(
        "command_to_run",
        nargs=argparse.REMAINDER,
        help="The command to execute and debug.",
    )

    # --- New 'blame' command ---
    parser_blame = subparsers.add_parser(
        "blame",
        help="Show the agent Run ID or author for each line of a file, similar to git blame."
    )
    parser_blame.add_argument(
        "filepath",
        type=Path,
        help="The path to the file to blame.",
    )
    parser_blame.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory (default: current directory).",
    )

    # --- New 'knowledge' command ---
    parser_knowledge = subparsers.add_parser(
        "knowledge",
        help="Manage the agent's knowledge base and questions."
    )
    knowledge_subparsers = parser_knowledge.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # Knowledge 'list' action
    parser_knowledge_list = knowledge_subparsers.add_parser("list", help="List knowledge items.")
    parser_knowledge_list.add_argument("--category", help="Filter by category.")
    parser_knowledge_list.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # Knowledge 'add' action
    parser_knowledge_add = knowledge_subparsers.add_parser("add", help="Add a knowledge item.")
    parser_knowledge_add.add_argument("content", help="The knowledge content.")
    parser_knowledge_add.add_argument("--category", default="GENERAL_NOTE", help="Category (default: GENERAL_NOTE).")
    parser_knowledge_add.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # Knowledge 'delete' action
    parser_knowledge_delete = knowledge_subparsers.add_parser("delete", help="Delete a knowledge item.")
    parser_knowledge_delete.add_argument("id", type=int, help="The ID of the item to delete.")
    parser_knowledge_delete.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # Knowledge 'questions' action
    parser_knowledge_questions = knowledge_subparsers.add_parser("questions", help="List agent questions.")
    parser_knowledge_questions.add_argument("--status", default="pending", choices=["pending", "answered"], help="Filter by status.")
    parser_knowledge_questions.add_argument("-i", "--interactive", action="store_true", help="Interactively answer questions.")
    parser_knowledge_questions.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # Knowledge 'answer' action
    parser_knowledge_answer = knowledge_subparsers.add_parser("answer", help="Answer a specific question.")
    parser_knowledge_answer.add_argument("id", type=int, help="The ID of the question.")
    parser_knowledge_answer.add_argument("answer", help="The answer text.")
    parser_knowledge_answer.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # Knowledge 'graph' action
    parser_knowledge_graph = knowledge_subparsers.add_parser("graph", help="Visualize knowledge graph.")
    parser_knowledge_graph.add_argument("--format", choices=["html", "mermaid", "json"], default="html", help="Output format (default: html).")
    parser_knowledge_graph.add_argument("-o", "--output", help="Output file path.")
    parser_knowledge_graph.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")


    # --- New 'chat' command ---
    parser_chat = subparsers.add_parser(
        "chat",
        help="Interactive chat with the agent."
    )
    parser_chat.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory."
    )
    parser_chat.add_argument(
        "-a", "--agent",
        choices=list(AVAILABLE_AGENTS.keys()),
        default="gemini",
        help="Which agent to use (default: gemini)."
    )
    parser_chat.add_argument(
        "-m", "--model",
        type=str,
        help="Model to use (overrides default)."
    )
    parser_chat.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging."
    )

    # --- New 'ask' command ---
    parser_ask = subparsers.add_parser(
        "ask",
        help="Ask a question about the codebase."
    )
    parser_ask.add_argument(
        "query",
        help="The question to ask."
    )
    parser_ask.add_argument(
        "--files",
        nargs="*",
        help="Specific files to include in the context."
    )
    parser_ask.add_argument(
        "-a", "--agent",
        choices=list(AVAILABLE_AGENTS.keys()),
        default="gemini",
        help="Which agent to use (default: gemini)."
    )
    parser_ask.add_argument(
        "-m", "--model",
        type=str,
        help="Model to use (overrides default)."
    )
    parser_ask.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging."
    )
    parser_ask.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to analyze (default: current directory)."
    )

    # --- New 'do' command ---
    parser_do = subparsers.add_parser(
        "do",
        help="Translate a natural language instruction to a shell command."
    )
    parser_do.add_argument(
        "instruction",
        help="The natural language instruction (e.g. 'undo last commit')."
    )
    parser_do.add_argument(
        "-a", "--agent",
        choices=list(AVAILABLE_AGENTS.keys()),
        default="gemini",
        help="Which agent to use (default: gemini)."
    )
    parser_do.add_argument(
        "-m", "--model",
        type=str,
        help="Model to use (overrides default)."
    )
    parser_do.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Execute the suggested command without confirmation."
    )
    parser_do.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging."
    )
    parser_do.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory (default: current directory)."
    )

    # --- New 'code-review' command ---
    parser_code_review = subparsers.add_parser(
        "code-review",
        help="Request an AI code review of specific files or git diffs."
    )
    parser_code_review.add_argument(
        "files",
        nargs="*",
        help="Specific files to review. If omitted, defaults to reviewing uncommitted changes."
    )
    parser_code_review.add_argument(
        "--diff",
        action="store_true",
        help="Include git diff (HEAD) in the review. Implied if no files are provided."
    )
    parser_code_review.add_argument(
        "-a", "--agent",
        choices=list(AVAILABLE_AGENTS.keys()),
        default="gemini",
        help="Which agent to use (default: gemini)."
    )
    parser_code_review.add_argument(
        "-m", "--model",
        type=str,
        help="Model to use (overrides default)."
    )
    parser_code_review.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging."
    )
    parser_code_review.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory (default: current directory)."
    )

    # --- New 'summarize' command ---
    parser_summarize = subparsers.add_parser(
        "summarize",
        help="Summarize git changes using AI."
    )
    parser_summarize.add_argument(
        "target",
        nargs="?",
        help="The git target to summarize (commit hash, range, or omitted for uncommitted changes)."
    )
    parser_summarize.add_argument(
        "-a", "--agent",
        choices=list(AVAILABLE_AGENTS.keys()),
        default="gemini",
        help="Which agent to use (default: gemini)."
    )
    parser_summarize.add_argument(
        "-m", "--model",
        type=str,
        help="Model to use (overrides default)."
    )
    parser_summarize.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging."
    )

    # --- New 'explain' command ---
    parser_explain = subparsers.add_parser(
        "explain",
        help="Explain source code files using AI."
    )
    parser_explain.add_argument(
        "file",
        nargs="+",
        help="The file(s) to explain."
    )
    parser_explain.add_argument(
        "--detail",
        choices=["high", "low"],
        default="high",
        help="Level of detail for the explanation (default: high)."
    )
    parser_explain.add_argument(
        "--diagram",
        action="store_true",
        help="Generate a Mermaid diagram."
    )
    parser_explain.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory."
    )
    parser_explain.add_argument(
        "-a", "--agent",
        choices=list(AVAILABLE_AGENTS.keys()),
        default="gemini",
        help="Which agent to use (default: gemini)."
    )
    parser_explain.add_argument(
        "-m", "--model",
        type=str,
        help="Model to use (overrides default)."
    )
    parser_explain.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging."
    )
    parser_summarize.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory (default: current directory)."
    )

    # --- New 'context' command ---
    parser_context = subparsers.add_parser(
        "context",
        help="Analyze the file context that the agent will use."
    )
    parser_context.add_argument(
        "action",
        choices=["show", "analyze"],
        help="Action to perform: 'show' a detailed tree view with sizes, or 'analyze' by file type.",
    )
    parser_context.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to analyze (default: current directory).",
    )

    # --- New 'todos' command ---
    parser_todos = subparsers.add_parser(
        "todos",
        help="Scan the codebase for TODO, FIXME, and other task tags."
    )
    parser_todos.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to scan (default: current directory).",
    )
    parser_todos.add_argument(
        "--tags",
        type=str,
        help="Comma-separated list of tags to search for (e.g., 'TODO,FIXME').",
    )
    parser_todos.add_argument(
        "--blame",
        action="store_true",
        help="Use git blame to identify the author and date of each TODO (slower).",
    )
    parser_todos.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format.",
    )

    # --- New 'search' command ---
    parser_search = subparsers.add_parser(
        "search",
        help="Search the codebase for a text pattern."
    )
    parser_search.add_argument(
        "pattern",
        help="The text or regex pattern to search for."
    )
    parser_search.add_argument(
        "--files",
        help="Glob pattern to filter files (e.g., '*.py')."
    )
    parser_search.add_argument(
        "--case-sensitive",
        action="store_true",
        help="Enable case-sensitive search."
    )
    parser_search.add_argument(
        "--regex",
        action="store_true",
        help="Treat pattern as a regular expression."
    )
    parser_search.add_argument(
        "-C", "--context",
        type=int,
        default=0,
        help="Number of context lines to show."
    )
    parser_search.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to search (default: current directory)."
    )

    # --- New 'smart-search' command ---
    parser_smart_search = subparsers.add_parser(
        "smart-search",
        aliases=["ssearch"],
        help="Search the codebase using relevance ranking (BM25)."
    )
    parser_smart_search.add_argument(
        "query",
        help="The search query (keywords)."
    )
    parser_smart_search.add_argument(
        "--files",
        help="Glob pattern to filter files (e.g., '*.py')."
    )
    parser_smart_search.add_argument(
        "-l", "--limit",
        type=int,
        default=10,
        help="Number of results to show (default: 10)."
    )
    parser_smart_search.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory."
    )

    # --- New 'replace' command ---
    parser_replace = subparsers.add_parser(
        "replace",
        help="Find and replace text in the codebase."
    )
    parser_replace.add_argument(
        "pattern",
        help="The text or regex pattern to search for."
    )
    parser_replace.add_argument(
        "replacement",
        help="The text to replace matches with."
    )
    parser_replace.add_argument(
        "--files",
        help="Glob pattern to filter files (e.g., '*.py')."
    )
    parser_replace.add_argument(
        "--case-sensitive",
        action="store_true",
        help="Enable case-sensitive match."
    )
    parser_replace.add_argument(
        "--regex",
        action="store_true",
        help="Treat pattern as a regular expression."
    )
    parser_replace.add_argument(
        "--dry-run",
        action="store_true",
        help="Show changes without applying them."
    )
    parser_replace.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory (default: current directory)."
    )

    # --- New 'stash' command ---
    parser_stash = subparsers.add_parser(
        "stash",
        help="Stash away uncommitted changes for later use."
    )
    parser_stash.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory (default: current directory).",
    )
    stash_subparsers = parser_stash.add_subparsers(
        dest="action",
        required=True,
        help="Specify stash action"
    )
    # Stash 'push' action
    parser_stash_push = stash_subparsers.add_parser("push", help="Stash all uncommitted changes (including untracked).")
    parser_stash_push.add_argument("-m", "--message", help="Optional descriptive message for the stash.")
    # Stash 'list' action
    parser_stash_list = stash_subparsers.add_parser("list", help="List all stashes in the repository.")
    # Stash 'pop' action
    parser_stash_pop = stash_subparsers.add_parser("pop", help="Interactively select a stash to apply and remove.")
    # Stash 'drop' action
    parser_stash_drop = stash_subparsers.add_parser("drop", help="Interactively select a stash to delete.")
    parser_stash_drop.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation prompt.",
    )

    # --- New 'onboard' command ---
    parser_onboard = subparsers.add_parser(
        "onboard",
        help="Run an interactive onboarding wizard for new developers."
    )
    parser_onboard.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory.",
    )

    # --- New 'session' command ---
    parser_session = subparsers.add_parser(
        "session",
        help="Manage work sessions (context, files, notes)."
    )
    session_subparsers = parser_session.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # Session 'new'
    parser_sess_new = session_subparsers.add_parser("new", help="Create a new session.")
    parser_sess_new.add_argument("name", help="Name of the session.")
    parser_sess_new.add_argument("-d", "--description", help="Optional description.")
    parser_sess_new.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # Session 'load'
    parser_sess_load = session_subparsers.add_parser("load", help="Load (activate) a session.")
    parser_sess_load.add_argument("name", help="Name of the session.")
    parser_sess_load.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # Session 'list'
    parser_sess_list = session_subparsers.add_parser("list", help="List all sessions.")
    parser_sess_list.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # Session 'info'
    parser_sess_info = session_subparsers.add_parser("info", help="Show info for a session.")
    parser_sess_info.add_argument("name", nargs="?", help="Name of the session (defaults to active).")
    parser_sess_info.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # Session 'add' (file)
    parser_sess_add = session_subparsers.add_parser("add", help="Add a file to a session.")
    parser_sess_add.add_argument("file", help="Path to the file.")
    parser_sess_add.add_argument("-n", "--name", help="Session name (defaults to active).")
    parser_sess_add.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # Session 'remove' (file)
    parser_sess_rem = session_subparsers.add_parser("remove", help="Remove a file from a session.")
    parser_sess_rem.add_argument("file", help="Path to the file.")
    parser_sess_rem.add_argument("-n", "--name", help="Session name (defaults to active).")
    parser_sess_rem.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # Session 'note'
    parser_sess_note = session_subparsers.add_parser("note", help="Add a note to a session.")
    parser_sess_note.add_argument("note", help="The note content.")
    parser_sess_note.add_argument("-n", "--name", help="Session name (defaults to active).")
    parser_sess_note.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # Session 'stop'
    parser_sess_stop = session_subparsers.add_parser("stop", help="Stop (deactivate) the current session.")
    parser_sess_stop.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # Session 'delete'
    parser_sess_del = session_subparsers.add_parser("delete", help="Delete a session.")
    parser_sess_del.add_argument("name", help="Name of the session.")
    parser_sess_del.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # --- New 'secrets' command ---
    parser_secrets = subparsers.add_parser(
        "secrets",
        help="Manage encrypted secrets (API keys, passwords)."
    )
    secrets_subparsers = parser_secrets.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # Secrets 'init'
    parser_sec_init = secrets_subparsers.add_parser("init", help="Generate encryption key.")
    parser_sec_init.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")
    parser_sec_init.add_argument("-f", "--force", action="store_true", help="Overwrite existing key.")

    # Secrets 'set'
    parser_sec_set = secrets_subparsers.add_parser("set", help="Set a secret.")
    parser_sec_set.add_argument("name", help="Secret name.")
    parser_sec_set.add_argument("value", help="Secret value.")
    parser_sec_set.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # Secrets 'get'
    parser_sec_get = secrets_subparsers.add_parser("get", help="Get a secret.")
    parser_sec_get.add_argument("name", help="Secret name.")
    parser_sec_get.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # Secrets 'list'
    parser_sec_list = secrets_subparsers.add_parser("list", help="List secret names.")
    parser_sec_list.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # Secrets 'delete'
    parser_sec_del = secrets_subparsers.add_parser("delete", help="Delete a secret.")
    parser_sec_del.add_argument("name", help="Secret name.")
    parser_sec_del.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # Secrets 'run'
    parser_sec_run = secrets_subparsers.add_parser("run", help="Run a command with secrets in environment.")
    parser_sec_run.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")
    parser_sec_run.add_argument("command_args", nargs=argparse.REMAINDER, help="The command to run (use -- before command).")

    # --- New 'db' command ---
    parser_db = subparsers.add_parser(
        "db",
        aliases=["database"],
        help="Manage application database (init, migrate, seed, query)."
    )
    db_subparsers = parser_db.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # db init
    parser_db_init = db_subparsers.add_parser("init", help="Initialize database configuration.")
    parser_db_init.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # db migrate
    parser_db_migrate = db_subparsers.add_parser("migrate", help="Run database migrations.")
    parser_db_migrate.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # db seed
    parser_db_seed = db_subparsers.add_parser("seed", help="Seed the database with initial data.")
    parser_db_seed.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # db inspect
    parser_db_inspect = db_subparsers.add_parser("inspect", help="Inspect database schema.")
    parser_db_inspect.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # DB 'query'
    parser_db_query = db_subparsers.add_parser("query", help="Query the database using natural language.")
    parser_db_query.add_argument("query", help="The natural language query (e.g. 'Show me all users created yesterday').")
    parser_db_query.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")
    parser_db_query.add_argument("-a", "--agent", choices=list(AVAILABLE_AGENTS.keys()), default="gemini", help="Which agent to use (default: gemini).")
    parser_db_query.add_argument("-m", "--model", type=str, help="Model to use (overrides default).")
    parser_db_query.add_argument("-y", "--yes", action="store_true", help="Skip confirmation prompt for write operations.")
    parser_db_query.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging.")

    # --- New 'playground' command ---
    parser_playground = subparsers.add_parser(
        "playground",
        help="Manage a safe scratchpad for code experiments."
    )
    playground_subparsers = parser_playground.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # Playground 'create'
    parser_pg_create = playground_subparsers.add_parser("create", help="Create a new playground file.")
    parser_pg_create.add_argument("name", nargs="?", default="scratch.py", help="Name of the file (default: scratch.py).")
    parser_pg_create.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # Playground 'run'
    parser_pg_run = playground_subparsers.add_parser("run", help="Run a playground file.")
    parser_pg_run.add_argument("name", help="Name of the file to run.")
    parser_pg_run.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # Playground 'list'
    parser_pg_list = playground_subparsers.add_parser("list", help="List playground files.")
    parser_pg_list.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # Playground 'delete'
    parser_pg_delete = playground_subparsers.add_parser("delete", help="Delete a playground file.")
    parser_pg_delete.add_argument("name", help="Name of the file to delete.")
    parser_pg_delete.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # --- New 'help' command ---
    parser_help = subparsers.add_parser("help", help="Show a structured and user-friendly help message.")

    # --- New 'cherry-pick' command ---
    parser_cherry_pick = subparsers.add_parser(
        "cherry-pick",
        help="Apply the changes from a specific commit or Run ID onto the current branch."
    )
    parser_cherry_pick.add_argument(
        "target",
        help="The git commit hash or agent Run ID to apply.",
    )
    parser_cherry_pick.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory (default: current directory).",
    )

    # --- New 'rollback' command ---
    parser_rollback = subparsers.add_parser(
        "rollback",
        help="Revert all commits associated with a specific agent Run ID."
    )
    parser_rollback.add_argument(
        "run_id",
        nargs="?",
        default="last",
        help="The agent Run ID to rollback (default: last run).",
    )
    parser_rollback.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory (default: current directory).",
    )
    parser_rollback.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation prompt.",
    )

    # --- New 'timeline' command ---
    parser_timeline = subparsers.add_parser(
        "timeline",
        help="Generate a chronological timeline of project events."
    )
    parser_timeline.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory.",
    )
    parser_timeline.add_argument(
        "--format",
        choices=["text", "json", "html"],
        default="text",
        help="Output format (default: text)."
    )
    parser_timeline.add_argument(
        "-l", "--limit",
        type=int,
        default=50,
        help="Number of events to show (default: 50)."
    )
    parser_timeline.add_argument(
        "-o", "--output",
        type=str,
        help="Output file path (optional)."
    )

    # --- New 'analytics' command ---
    parser_analytics = subparsers.add_parser(
        "analytics",
        help="Display project analytics (git stats, code stats)."
    )
    analytics_subparsers = parser_analytics.add_subparsers(
        dest="type",
        required=True,
        help="Type of analytics to run"
    )

    # Analytics 'git' action
    parser_analytics_git = analytics_subparsers.add_parser(
        "git",
        help="Show Git analytics (contributors, hotspots, activity)."
    )
    parser_analytics_git.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory.",
    )

    # Analytics 'code' action
    parser_analytics_code = analytics_subparsers.add_parser(
        "code",
        help="Show code file statistics (count, size, type)."
    )
    parser_analytics_code.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory.",
    )

    # Analytics 'complexity' action
    parser_analytics_complexity = analytics_subparsers.add_parser(
        "complexity",
        help="Show code complexity analysis (cyclomatic complexity)."
    )
    parser_analytics_complexity.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory.",
    )

    # --- New 'deps' command ---
    parser_deps = subparsers.add_parser(
        "deps",
        help="Visualize project dependencies (Tree, Mermaid, JSON)."
    )
    parser_deps.add_argument(
        "--format",
        choices=["tree", "mermaid", "json"],
        default="tree",
        help="Output format (default: tree)."
    )
    parser_deps.add_argument(
        "--check",
        action="store_true",
        help="Check online registries for updates.",
    )
    parser_deps.add_argument(
        "--update",
        action="store_true",
        help="Interactively check and update dependencies.",
    )
    parser_deps.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory.",
    )

    # --- New 'duplication' command ---
    parser_duplication = subparsers.add_parser(
        "duplication",
        help="Scan for code duplication (Copy-Paste Detector)."
    )
    parser_duplication.add_argument(
        "--min-tokens",
        type=int,
        default=50,
        help="Minimum number of tokens to consider a duplicate (default: 50)."
    )
    parser_duplication.add_argument(
        "--files",
        type=str,
        help="Comma-separated glob patterns to include (e.g. '*.py')."
    )
    parser_duplication.add_argument(
        "--ignore",
        type=str,
        help="Comma-separated glob patterns to ignore."
    )
    parser_duplication.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to scan."
    )

    # --- New 'unused' command ---
    parser_unused = subparsers.add_parser(
        "unused",
        help="Scan for potentially unused code (dead code)."
    )
    parser_unused.add_argument(
        "--files",
        type=str,
        help="Glob pattern to include (e.g. '*.py')."
    )
    parser_unused.add_argument(
        "--ignore",
        type=str,
        help="Comma-separated patterns to ignore."
    )
    parser_unused.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to scan."
    )

    # --- New 'risk' command ---
    parser_risk = subparsers.add_parser(
        "risk",
        help="Identify high-risk files based on complexity and churn (Hotspots)."
    )
    parser_risk.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to analyze."
    )
    parser_risk.add_argument(
        "-l", "--limit",
        type=int,
        default=20,
        help="Number of files to show (default: 20)."
    )

    # --- New 'impact' command ---
    parser_impact = subparsers.add_parser(
        "impact",
        help="Predictively analyze the impact of changes (dependency graph)."
    )
    parser_impact.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to analyze."
    )
    parser_impact.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format."
    )

    # --- New 'a11y' command ---
    parser_a11y = subparsers.add_parser(
        "a11y",
        help="Scan for accessibility issues (HTML, JSX, Vue)."
    )
    parser_a11y.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to scan."
    )
    parser_a11y.add_argument(
        "--files",
        type=str,
        help="Glob pattern to include (e.g. '*.html')."
    )
    parser_a11y.add_argument(
        "--ignore",
        type=str,
        help="Comma-separated patterns to ignore."
    )
    parser_a11y.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)."
    )

    # --- New 'license' command (replaced by license-lab) ---

    # --- New 'bisect' command ---
    parser_bisect = subparsers.add_parser(
        "bisect",
        help="Automate regression finding with git bisect and AI analysis."
    )
    bisect_subparsers = parser_bisect.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # Bisect 'run' action
    parser_bisect_run = bisect_subparsers.add_parser(
        "run",
        help="Run an automated git bisect session."
    )
    parser_bisect_run.add_argument(
        "--good",
        required=True,
        help="A known good commit hash or reference."
    )
    parser_bisect_run.add_argument(
        "--bad",
        required=True,
        help="A known bad commit hash or reference."
    )
    parser_bisect_run.add_argument(
        "--test-command",
        required=True,
        dest="test_command",
        help="The shell command to run for testing (exit 0 for good, non-zero for bad)."
    )
    parser_bisect_run.add_argument(
        "--no-analysis",
        action="store_true",
        help="Skip the AI analysis of the bad commit."
    )
    # Common agent args
    parser_bisect_run.add_argument(
        "-a", "--agent",
        choices=list(AVAILABLE_AGENTS.keys()),
        default="gemini",
        help="Which agent to use for analysis (default: gemini)."
    )
    parser_bisect_run.add_argument(
        "-m", "--model",
        type=str,
        help="Model to use (overrides default)."
    )
    parser_bisect_run.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging."
    )
    parser_bisect_run.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory."
    )

    # Bisect 'analyze' action
    parser_bisect_analyze = bisect_subparsers.add_parser(
        "analyze",
        help="Analyze a specific commit for a bug."
    )
    parser_bisect_analyze.add_argument(
        "commit",
        help="The commit hash to analyze."
    )
    parser_bisect_analyze.add_argument(
        "--bug-description",
        help="Description of the bug or failure."
    )
    parser_bisect_analyze.add_argument(
        "-a", "--agent",
        choices=list(AVAILABLE_AGENTS.keys()),
        default="gemini",
        help="Which agent to use (default: gemini)."
    )
    parser_bisect_analyze.add_argument(
        "-m", "--model",
        type=str,
        help="Model to use (overrides default)."
    )
    parser_bisect_analyze.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging."
    )
    parser_bisect_analyze.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory."
    )

    # --- New 'map' command ---
    parser_map = subparsers.add_parser(
        "map",
        help="Visualize the project's internal structure (files, classes, functions)."
    )
    parser_map.add_argument(
        "--format",
        choices=["mermaid", "json", "text"],
        default="mermaid",
        help="Output format (default: mermaid)."
    )
    parser_map.add_argument(
        "--focus",
        type=str,
        help="Focus on a specific file or module pattern."
    )
    parser_map.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory.",
    )

    # --- New 'architecture' command ---
    parser_arch = subparsers.add_parser(
        "architecture",
        aliases=["arch"],
        help="Validate project architecture against rules."
    )
    parser_arch.add_argument(
        "--rules",
        type=str,
        help="Path to a YAML file containing architecture rules."
    )
    parser_arch.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory."
    )

    # --- New 'estimate' command ---
    parser_estimate = subparsers.add_parser(
        "estimate",
        help="Estimate complexity and effort for a feature."
    )
    parser_estimate.add_argument(
        "feature",
        help="Description of the feature to estimate."
    )
    parser_estimate.add_argument(
        "--files",
        type=str,
        help="Comma-separated list of file patterns to include as context."
    )
    parser_estimate.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory."
    )
    parser_estimate.add_argument(
        "-a", "--agent",
        choices=list(AVAILABLE_AGENTS.keys()),
        default="gemini",
        help="Which agent to use (default: gemini)."
    )
    parser_estimate.add_argument(
        "-m", "--model",
        type=str,
        help="Model to use (overrides default)."
    )
    parser_estimate.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging."
    )

    # --- New 'release' command ---
    parser_release = subparsers.add_parser(
        "release",
        help="Manage releases (version bump, changelog, tagging)."
    )
    parser_release.add_argument(
        "action",
        choices=["plan", "apply"],
        default="plan",
        nargs="?",
        help="Action to perform (default: plan)."
    )
    parser_release.add_argument(
        "--force-version",
        type=str,
        help="Manually specify the next version.",
    )
    parser_release.add_argument(
        "--no-changelog",
        action="store_true",
        help="Do not use the generated changelog for the tag message.",
    )
    parser_release.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate the apply action.",
    )
    parser_release.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory.",
    )
    parser_release.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation if no bump detected.",
    )

    # --- New 'review' command ---
    parser_review = subparsers.add_parser(
        "review",
        help="Run an interactive QA review of the agent's completed work."
    )
    parser_review.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to review.",
    )

    # --- New 'env' command ---
    parser_env = subparsers.add_parser(
        "env",
        help="Manage environment variables (.env files)."
    )
    env_subparsers = parser_env.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # Env 'init'
    parser_env_init = env_subparsers.add_parser("init", help="Initialize .env and .env.example.")
    parser_env_init.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # Env 'check'
    parser_env_check = env_subparsers.add_parser("check", help="Check sync status between .env and .env.example.")
    parser_env_check.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # Env 'sync'
    parser_env_sync = env_subparsers.add_parser("sync", help="Synchronize keys between .env and .env.example.")
    parser_env_sync.add_argument("-i", "--interactive", action="store_true", help="Interactively fill values.")
    parser_env_sync.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # Env 'generate'
    parser_env_generate = env_subparsers.add_parser("generate", help="Generate a secure secret for a key.")
    parser_env_generate.add_argument("key", help="The environment variable key.")
    parser_env_generate.add_argument("-l", "--length", type=int, default=32, help="Length of the secret (default: 32).")
    parser_env_generate.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # --- New 'setup' command ---
    parser_setup = subparsers.add_parser(
        "setup",
        help="Detect the project type and install its dependencies."
    )
    parser_setup.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to set up (default: current directory).",
    )

    # --- New 'scaffold' command ---
    parser_scaffold = subparsers.add_parser(
        "scaffold",
        help="Scaffold a new project from a template."
    )
    scaffold_subparsers = parser_scaffold.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # Scaffold 'list'
    parser_scaffold_list = scaffold_subparsers.add_parser("list", help="List available templates.")
    parser_scaffold_list.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # Scaffold 'create'
    parser_scaffold_create = scaffold_subparsers.add_parser("create", help="Create a project from a template.")
    parser_scaffold_create.add_argument("template", help="Template name (run 'list' to see available options).")
    parser_scaffold_create.add_argument("name", nargs="?", help="Project name (creates a subdirectory).")
    parser_scaffold_create.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Base directory.")
    parser_scaffold_create.add_argument("-f", "--force", action="store_true", help="Overwrite existing files.")

    # --- New 'dockerize' command ---
    parser_dockerize = subparsers.add_parser(
        "dockerize",
        help="Generate Dockerfile and docker-compose.yml for the project."
    )
    parser_dockerize.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory.",
    )
    parser_dockerize.add_argument(
        "-f", "--force",
        action="store_true",
        help="Overwrite existing files.",
    )
    parser_dockerize.add_argument(
        "--dry-run",
        action="store_true",
        help="Print contents without writing files.",
    )

    # --- New 'cicd' command ---
    parser_cicd = subparsers.add_parser(
        "cicd",
        help="Generate CI/CD pipeline configuration files."
    )
    parser_cicd.add_argument(
        "--platform",
        choices=["github", "gitlab"],
        default="github",
        help="Target CI/CD platform (default: github)."
    )
    parser_cicd.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory.",
    )
    parser_cicd.add_argument(
        "-f", "--force",
        action="store_true",
        help="Overwrite existing files.",
    )
    parser_cicd.add_argument(
        "--dry-run",
        action="store_true",
        help="Print contents without writing files.",
    )

    # --- New 'verify' command ---
    parser_verify = subparsers.add_parser(
        "verify",
        help="Run comprehensive project verification (Lint, Type, Security, Test)."
    )
    parser_verify.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory.",
    )
    parser_verify.add_argument(
        "--check",
        type=str,
        help="Comma-separated list of checks to run (lint, type, security, test, all). Default: all.",
    )
    parser_verify.add_argument(
        "--fix",
        action="store_true",
        help="Attempt to auto-fix issues (e.g. format code).",
    )
    parser_verify.add_argument(
        "-o", "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )

    # --- New 'troubleshoot' command ---
    parser_troubleshoot = subparsers.add_parser(
        "troubleshoot",
        help="Interactive troubleshooting assistant (Detect, Diagnose, Fix, Learn)."
    )
    parser_troubleshoot.add_argument(
        "--issue",
        help="Description of the issue (optional, otherwise detects automatically)."
    )
    parser_troubleshoot.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory."
    )
    parser_troubleshoot.add_argument(
        "-a", "--agent",
        choices=list(AVAILABLE_AGENTS.keys()),
        default="gemini",
        help="Which agent to use (default: gemini)."
    )
    parser_troubleshoot.add_argument(
        "-m", "--model",
        type=str,
        help="Model to use (overrides default)."
    )
    parser_troubleshoot.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation prompts."
    )
    parser_troubleshoot.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging."
    )

    # --- New 'sentinel' command ---
    parser_sentinel = subparsers.add_parser(
        "sentinel",
        help="Autonomous Sentinel: Watches files, runs checks, and auto-fixes issues."
    )
    parser_sentinel.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to watch."
    )
    parser_sentinel.add_argument(
        "--auto-fix",
        action="store_true",
        help="Enable automatic AI fixing of detected issues."
    )
    parser_sentinel.add_argument(
        "--checks",
        type=str,
        default="lint,test",
        help="Comma-separated list of checks to run (lint,test,type,security). Default: lint,test."
    )
    parser_sentinel.add_argument(
        "-a", "--agent",
        choices=list(AVAILABLE_AGENTS.keys()),
        default="gemini",
        help="Which agent to use for fixing (default: gemini)."
    )
    parser_sentinel.add_argument(
        "-m", "--model",
        type=str,
        help="Model to use (overrides default)."
    )

    # --- New 'health' command ---
    parser_health = subparsers.add_parser(
        "health",
        help="Calculate the overall health score of the project."
    )
    parser_health.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory.",
    )
    parser_health.add_argument(
        "--format",
        choices=["text", "html", "json"],
        default="text",
        help="Output format (default: text)."
    )
    parser_health.add_argument(
        "-o", "--output",
        type=str,
        help="Output file path (optional)."
    )

    # --- New 'debt' command ---
    parser_debt = subparsers.add_parser(
        "debt",
        help="Generate a Technical Debt Report (Scorecard)."
    )
    parser_debt.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory.",
    )
    parser_debt.add_argument(
        "--json",
        action="store_true",
        help="Output report in JSON format."
    )

    # --- New 'check-links' command ---
    parser_check_links = subparsers.add_parser(
        "check-links",
        help="Scan project files for broken HTTP/HTTPS links."
    )
    parser_check_links.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory.",
    )
    parser_check_links.add_argument(
        "--files",
        type=str,
        default="**/*.md",
        help="Glob pattern for files to scan (default: **/*.md)."
    )
    parser_check_links.add_argument(
        "--ignore",
        type=str,
        help="Comma-separated list of URL patterns to ignore."
    )
    parser_check_links.add_argument(
        "--timeout",
        type=int,
        default=5,
        help="Request timeout in seconds (default: 5)."
    )
    parser_check_links.add_argument(
        "--concurrency",
        type=int,
        default=10,
        help="Number of concurrent requests (default: 10)."
    )

    # --- New 'security' command ---
    parser_security = subparsers.add_parser(
        "security",
        help="Audit the project for security issues (SAST, secrets, dependencies)."
    )
    parser_security.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to scan (default: current directory).",
    )
    parser_security.add_argument(
        "--scan-type",
        choices=["all", "sast", "secrets", "deps"],
        default="all",
        help="Type of scan to perform (default: all).",
    )
    parser_security.add_argument(
        "--severity",
        choices=["low", "medium", "high"],
        default="low",
        help="Minimum severity level to report (default: low).",
    )
    parser_security.add_argument(
        "--scan-history",
        action="store_true",
        help="Also scan git history for secrets.",
    )
    parser_security.add_argument(
        "--depth",
        type=int,
        default=100,
        help="Depth of git history to scan (default: 100 commits).",
    )
    parser_security.add_argument(
        "-o", "--output",
        type=str,
        help="Path to save the security report (JSON).",
    )
    parser_security.add_argument(
        "--ignore-add",
        help="Add a file pattern to .secretignore (e.g. 'tests/fixtures/*').",
    )
    parser_security.add_argument(
        "--install-hook",
        action="store_true",
        help="Install a git pre-commit hook that enforces security checks.",
    )
    parser_security.add_argument(
        "--fix",
        action="store_true",
        help="Attempt to automatically fix found vulnerabilities (dependencies only)."
    )
    parser_security.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate the remediation without applying changes."
    )
    parser_security.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation prompts during remediation."
    )

    # --- New 'openapi' command ---
    parser_openapi = subparsers.add_parser(
        "openapi",
        help="Generate an OpenAPI specification from the codebase."
    )
    parser_openapi.add_argument(
        "-o", "--output",
        default="openapi.yaml",
        help="Output file path (default: openapi.yaml)."
    )
    parser_openapi.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory."
    )
    parser_openapi.add_argument(
        "-a", "--agent",
        choices=list(AVAILABLE_AGENTS.keys()),
        default="gemini",
        help="Which agent to use (default: gemini)."
    )
    parser_openapi.add_argument(
        "-m", "--model",
        type=str,
        help="Model to use (overrides default)."
    )

    # --- New 'docstring' command ---
    parser_docstring = subparsers.add_parser(
        "docstring",
        help="Manage Python docstrings (check and generate)."
    )
    parser_docstring.add_argument(
        "action",
        choices=["check", "generate"],
        help="Action to perform."
    )
    parser_docstring.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory.",
    )
    parser_docstring.add_argument(
        "-a", "--agent",
        choices=list(AVAILABLE_AGENTS.keys()),
        default="gemini",
        help="Which agent to use for generation (default: gemini)."
    )
    parser_docstring.add_argument(
        "-m", "--model",
        type=str,
        help="Model to use (overrides default)."
    )
    parser_docstring.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation prompt for 'generate' action."
    )

    # --- New 'refactor' command ---
    parser_refactor = subparsers.add_parser(
        "refactor",
        help="Refactor a file using AI based on a natural language instruction."
    )
    parser_refactor.add_argument(
        "file",
        help="The file to refactor."
    )
    parser_refactor.add_argument(
        "instruction",
        help="The refactoring instruction (e.g., 'Extract the login logic into a separate function')."
    )
    parser_refactor.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory.",
    )
    parser_refactor.add_argument(
        "-a", "--agent",
        choices=list(AVAILABLE_AGENTS.keys()),
        default="gemini",
        help="Which agent to use (default: gemini)."
    )
    parser_refactor.add_argument(
        "-m", "--model",
        type=str,
        help="Model to use (overrides default)."
    )
    parser_refactor.add_argument(
        "--diff-only",
        action="store_true",
        help="Show the diff but do not apply changes.",
    )
    parser_refactor.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation prompt.",
    )

    # --- New 'polish' command ---
    parser_polish = subparsers.add_parser(
        "polish",
        help="Proactively find and refactor code quality issues (e.g. complexity)."
    )
    parser_polish.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory.",
    )
    parser_polish.add_argument(
        "-t", "--threshold",
        type=int,
        default=10,
        help="Complexity threshold to trigger refactoring (default: 10).",
    )
    parser_polish.add_argument(
        "-l", "--limit",
        type=int,
        default=1,
        help="Maximum number of files to polish in one run (default: 1).",
    )
    parser_polish.add_argument(
        "-a", "--agent",
        choices=list(AVAILABLE_AGENTS.keys()),
        default="gemini",
        help="Which agent to use (default: gemini)."
    )
    parser_polish.add_argument(
        "-m", "--model",
        type=str,
        help="Model to use (overrides default)."
    )
    parser_polish.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation prompts (auto-confirm refactor plan).",
    )

    # --- New 'resolve' command ---
    parser_resolve = subparsers.add_parser(
        "resolve",
        help="Interactively resolve TODO/FIXME comments using AI."
    )
    parser_resolve.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory.",
    )
    parser_resolve.add_argument(
        "--no-interactive",
        dest="interactive",
        action="store_false",
        help="Disable interactive selection.",
    )
    parser_resolve.set_defaults(interactive=True)
    parser_resolve.add_argument(
        "-a", "--agent",
        choices=list(AVAILABLE_AGENTS.keys()),
        default="gemini",
        help="Which agent to use (default: gemini)."
    )
    parser_resolve.add_argument(
        "-m", "--model",
        type=str,
        help="Model to use (overrides default)."
    )
    parser_resolve.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation prompt.",
    )

    # --- New 'regex' command ---
    parser_regex = subparsers.add_parser(
        "regex",
        help="Regex Lab: Match, Explain, and Generate regular expressions."
    )
    parser_regex.add_argument(
        "action",
        choices=["match", "explain", "generate", "game"],
        help="Action to perform."
    )
    parser_regex.add_argument(
        "--pattern",
        help="The regex pattern."
    )
    parser_regex.add_argument(
        "--text",
        help="The text to match against, or the description for generation."
    )
    parser_regex.add_argument(
        "--flags",
        help="Regex flags (e.g. 'ims')."
    )
    parser_regex.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory."
    )
    parser_regex.add_argument(
        "-a", "--agent",
        choices=list(AVAILABLE_AGENTS.keys()),
        default="gemini",
        help="Which agent to use (default: gemini)."
    )
    parser_regex.add_argument(
        "-m", "--model",
        type=str,
        help="Model to use (overrides default)."
    )

    # --- New 'cron-lab' command ---
    parser_cron = subparsers.add_parser(
        "cron-lab",
        help="Cron Lab: Next, Explain, and Generate cron expressions."
    )
    parser_cron.add_argument(
        "action",
        choices=["next", "explain", "generate"],
        help="Action to perform."
    )
    parser_cron.add_argument(
        "--expression",
        help="The cron expression."
    )
    parser_cron.add_argument(
        "--description",
        help="The description for generation."
    )
    parser_cron.add_argument(
        "--count",
        type=int,
        default=5,
        help="Number of occurrences to calculate (default: 5)."
    )
    parser_cron.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory."
    )
    parser_cron.add_argument(
        "-a", "--agent",
        choices=list(AVAILABLE_AGENTS.keys()),
        default="gemini",
        help="Which agent to use (default: gemini)."
    )
    parser_cron.add_argument(
        "-m", "--model",
        type=str,
        help="Model to use (overrides default)."
    )

    # --- New 'resolve-conflicts' command ---
    parser_resolve_conflicts = subparsers.add_parser(
        "resolve-conflicts",
        aliases=["fix-conflicts"],
        help="Resolve git merge conflicts using AI."
    )
    parser_resolve_conflicts.add_argument(
        "files",
        nargs="*",
        help="Specific files to resolve."
    )
    parser_resolve_conflicts.add_argument(
        "--all",
        action="store_true",
        help="Scan and resolve all files with conflicts."
    )
    parser_resolve_conflicts.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory.",
    )
    parser_resolve_conflicts.add_argument(
        "-a", "--agent",
        choices=list(AVAILABLE_AGENTS.keys()),
        default="gemini",
        help="Which agent to use (default: gemini)."
    )
    parser_resolve_conflicts.add_argument(
        "-m", "--model",
        type=str,
        help="Model to use (overrides default)."
    )
    parser_resolve_conflicts.add_argument(
        "--diff",
        action="store_true",
        help="Show diff before applying.",
    )
    parser_resolve_conflicts.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation prompt.",
    )
    parser_resolve_conflicts.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging."
    )

    # --- New 'generate-tests' command ---
    parser_gentest = subparsers.add_parser(
        "generate-tests",
        aliases=["gentest"],
        help="Generate unit tests for a specific file."
    )
    parser_gentest.add_argument(
        "file",
        help="The source file to generate tests for."
    )
    parser_gentest.add_argument(
        "-o", "--output",
        help="The output path for the test file (optional)."
    )
    parser_gentest.add_argument(
        "-f", "--framework",
        default="pytest",
        help="The testing framework to use (default: pytest)."
    )
    parser_gentest.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory."
    )
    parser_gentest.add_argument(
        "-a", "--agent",
        choices=list(AVAILABLE_AGENTS.keys()),
        default="gemini",
        help="Which agent to use (default: gemini)."
    )
    parser_gentest.add_argument(
        "-m", "--model",
        type=str,
        help="Model to use (overrides default)."
    )

    # --- New 'perf' command ---
    parser_perf = subparsers.add_parser(
        "perf",
        help="Performance profiling tools (run, report)."
    )
    perf_subparsers = parser_perf.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # perf run
    parser_perf_run = perf_subparsers.add_parser("run", help="Run a script with profiling enabled.")
    parser_perf_run.add_argument("script", help="The script to run.")
    parser_perf_run.add_argument("script_args", nargs=argparse.REMAINDER, help="Arguments for the script.")
    parser_perf_run.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="The project directory.")

    # perf report
    parser_perf_report = perf_subparsers.add_parser("report", help="Show profiling report.")
    parser_perf_report.add_argument("-l", "--limit", type=int, default=20, help="Number of functions to show.")
    parser_perf_report.add_argument("-s", "--sort", default="tottime", choices=["tottime", "cumtime", "ncalls"], help="Sort key.")
    parser_perf_report.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="The project directory.")

    # --- New 'snippets' command ---
    parser_snippets = subparsers.add_parser(
        "snippets",
        help="Manage code snippets and components."
    )
    snippets_subparsers = parser_snippets.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # snippets list
    parser_snippets_list = snippets_subparsers.add_parser("list", help="List available snippets.")
    parser_snippets_list.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # snippets show
    parser_snippets_show = snippets_subparsers.add_parser("show", help="Show snippet content.")
    parser_snippets_show.add_argument("name", help="Snippet name.")
    parser_snippets_show.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # snippets add
    parser_snippets_add = snippets_subparsers.add_parser("add", help="Add a snippet from a file.")
    parser_snippets_add.add_argument("name", help="Snippet name.")
    parser_snippets_add.add_argument("file", help="Source file path.")
    parser_snippets_add.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # snippets create
    parser_snippets_create = snippets_subparsers.add_parser("create", help="Create a snippet interactively.")
    parser_snippets_create.add_argument("name", help="Snippet name.")
    parser_snippets_create.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # snippets delete
    parser_snippets_delete = snippets_subparsers.add_parser("delete", help="Delete a snippet.")
    parser_snippets_delete.add_argument("name", help="Snippet name.")
    parser_snippets_delete.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # snippets apply
    parser_snippets_apply = snippets_subparsers.add_parser("apply", help="Apply a snippet to a file.")
    parser_snippets_apply.add_argument("name", help="Snippet name.")
    parser_snippets_apply.add_argument("target", help="Target file path.")
    parser_snippets_apply.add_argument("--mode", choices=["append", "prepend", "overwrite"], default="append", help="Application mode (default: append).")
    parser_snippets_apply.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # --- New 'dataset' command ---
    parser_dataset = subparsers.add_parser(
        "dataset",
        help="Generate datasets for fine-tuning LLMs."
    )
    dataset_subparsers = parser_dataset.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # Dataset 'generate'
    parser_ds_gen = dataset_subparsers.add_parser("generate", help="Generate a JSONL dataset from agent history.")
    parser_ds_gen.add_argument(
        "-o", "--output",
        default="fine_tuning_dataset.jsonl",
        help="Output file path (default: fine_tuning_dataset.jsonl)."
    )
    parser_ds_gen.add_argument(
        "--run-id",
        help="Specific run ID to process (defaults to last run if not specified)."
    )
    parser_ds_gen.add_argument(
        "--all",
        action="store_true",
        help="Process all available history."
    )
    parser_ds_gen.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory."
    )

    # --- New 'frontend' command ---
    parser_frontend = subparsers.add_parser(
        "frontend",
        help="Frontend Verification (snapshot, verify)."
    )
    frontend_subparsers = parser_frontend.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # frontend snapshot
    parser_frontend_snap = frontend_subparsers.add_parser("snapshot", help="Capture a baseline snapshot.")
    parser_frontend_snap.add_argument("url", help="URL to capture.")
    parser_frontend_snap.add_argument("--name", required=True, help="Unique name for this snapshot.")
    parser_frontend_snap.add_argument("--baseline", action="store_true", help="Save as baseline directly.")
    parser_frontend_snap.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # frontend verify
    parser_frontend_verify = frontend_subparsers.add_parser("verify", help="Verify current state against baseline.")
    parser_frontend_verify.add_argument("url", help="URL to verify.")
    parser_frontend_verify.add_argument("--name", required=True, help="Unique name (matches baseline).")
    parser_frontend_verify.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # frontend list
    parser_frontend_list = frontend_subparsers.add_parser("list", help="List baselines.")
    parser_frontend_list.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # frontend approve
    parser_frontend_approve = frontend_subparsers.add_parser("approve", help="Promote current snapshot to baseline.")
    parser_frontend_approve.add_argument("--name", required=True, help="Name of the snapshot.")
    parser_frontend_approve.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # --- New 'mock' command ---
    parser_mock = subparsers.add_parser(
        "mock",
        help="Mock Data Tools (generate, serve)."
    )
    mock_subparsers = parser_mock.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # mock generate
    parser_mock_gen = mock_subparsers.add_parser("generate", help="Generate mock data based on a JSON schema.")
    parser_mock_gen.add_argument(
        "schema",
        help="Path to the JSON schema file."
    )
    parser_mock_gen.add_argument(
        "--count",
        type=int,
        default=1,
        help="Number of records to generate (default: 1)."
    )
    parser_mock_gen.add_argument(
        "--format",
        choices=["json", "csv", "sql"],
        default="json",
        help="Output format (default: json)."
    )
    parser_mock_gen.add_argument(
        "--output",
        help="Output file path (optional)."
    )
    parser_mock_gen.add_argument(
        "--table-name",
        default="mock_data",
        help="Table name for SQL export (default: mock_data)."
    )

    # mock serve
    parser_mock_serve = mock_subparsers.add_parser("serve", help="Serve a mock API.")
    parser_mock_serve.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to listen on (default: 8000)."
    )
    parser_mock_serve.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory."
    )
    parser_mock_serve.add_argument(
        "-a", "--agent",
        choices=list(AVAILABLE_AGENTS.keys()),
        default="gemini",
        help="Which agent to use (default: gemini)."
    )
    parser_mock_serve.add_argument(
        "-m", "--model",
        type=str,
        help="Model to use (overrides default)."
    )

    # --- New 'i18n' command ---
    parser_i18n = subparsers.add_parser(
        "i18n",
        help="Manage Internationalization (translation, verification)."
    )
    i18n_subparsers = parser_i18n.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # i18n 'translate'
    parser_i18n_translate = i18n_subparsers.add_parser("translate", help="Translate translation files using AI.")
    parser_i18n_translate.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")
    parser_i18n_translate.add_argument("--source", type=str, default="locales/en.json", help="Source language file (default: locales/en.json).")
    parser_i18n_translate.add_argument("--langs", type=str, required=True, help="Comma-separated target languages (e.g. es,fr).")
    parser_i18n_translate.add_argument("-a", "--agent", choices=list(AVAILABLE_AGENTS.keys()), default="gemini", help="Which agent to use.")
    parser_i18n_translate.add_argument("-m", "--model", type=str, help="Model to use.")
    parser_i18n_translate.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging.")

    # i18n 'verify'
    parser_i18n_verify = i18n_subparsers.add_parser("verify", help="Verify translation consistency.")
    parser_i18n_verify.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")
    parser_i18n_verify.add_argument("--source", type=str, default="locales/en.json", help="Source language file (default: locales/en.json).")
    parser_i18n_verify.add_argument("--langs", type=str, required=True, help="Comma-separated target languages (e.g. es,fr).")
    parser_i18n_verify.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging.")

    # --- New 'api-lab' command ---
    parser_api_lab = subparsers.add_parser(
        "api-lab",
        help="Interactive API Lab (list endpoints, run requests)."
    )
    api_lab_subparsers = parser_api_lab.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # api-lab 'list'
    parser_api_lab_list = api_lab_subparsers.add_parser("list", help="List available endpoints from OpenAPI spec.")
    parser_api_lab_list.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # api-lab 'run'
    parser_api_lab_run = api_lab_subparsers.add_parser("run", help="Execute an API request.")
    parser_api_lab_run.add_argument("method", choices=["GET", "POST", "PUT", "DELETE", "PATCH"], help="HTTP method.")
    parser_api_lab_run.add_argument("url", help="URL path (e.g. /users) or full URL.")
    parser_api_lab_run.add_argument("--body", type=str, help="Request body (JSON string).")
    parser_api_lab_run.add_argument("--headers", type=str, help="Request headers (JSON string).")
    parser_api_lab_run.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # api-lab 'fuzz'
    parser_api_lab_fuzz = api_lab_subparsers.add_parser("fuzz", help="Fuzz an API endpoint to find bugs.")
    parser_api_lab_fuzz.add_argument("method", choices=["GET", "POST", "PUT", "DELETE", "PATCH"], help="HTTP method.")
    parser_api_lab_fuzz.add_argument("url", help="URL path (e.g. /users) as defined in spec, or full URL.")
    parser_api_lab_fuzz.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # api-lab 'load-test'
    parser_api_lab_load = api_lab_subparsers.add_parser("load-test", help="Run a load test against an API endpoint.")
    parser_api_lab_load.add_argument("method", choices=["GET", "POST", "PUT", "DELETE", "PATCH"], help="HTTP method.")
    parser_api_lab_load.add_argument("url", help="URL path (e.g. /users) or full URL.")
    parser_api_lab_load.add_argument("--users", type=int, default=10, help="Number of concurrent users (default: 10).")
    parser_api_lab_load.add_argument("--duration", type=int, default=10, help="Duration in seconds (default: 10).")
    parser_api_lab_load.add_argument("--body", type=str, help="Request body (JSON string).")
    parser_api_lab_load.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # api-lab 'collections'
    parser_api_collections = api_lab_subparsers.add_parser("collections", aliases=["saved"], help="Manage API collections.")
    collections_subparsers = parser_api_collections.add_subparsers(
        dest="collection_action",
        required=True,
        help="Collection action."
    )

    # api-lab collections save
    parser_coll_save = collections_subparsers.add_parser("save", help="Save a request.")
    parser_coll_save.add_argument("--name", required=True, help="Request name.")
    parser_coll_save.add_argument("--method", required=True, help="HTTP method.")
    parser_coll_save.add_argument("--url", required=True, help="URL.")
    parser_coll_save.add_argument("--headers", help="JSON headers.")
    parser_coll_save.add_argument("--body", help="Request body.")

    # api-lab collections list
    parser_coll_list = collections_subparsers.add_parser("list", help="List saved requests.")

    # api-lab collections delete
    parser_coll_delete = collections_subparsers.add_parser("delete", help="Delete a request.")
    parser_coll_delete.add_argument("id", help="Request ID.")

    # api-lab collections run
    parser_coll_run = collections_subparsers.add_parser("run", help="Run a saved request.")
    parser_coll_run.add_argument("id", help="Request ID.")

    # --- New 'research' command ---
    parser_research = subparsers.add_parser(
        "research",
        help="Research a topic by crawling a URL and saving to Knowledge Base."
    )
    parser_research.add_argument(
        "url",
        help="The starting URL to research."
    )
    parser_research.add_argument(
        "--depth",
        type=int,
        default=0,
        help="Recursion depth for crawling links (default: 0)."
    )
    parser_research.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Maximum number of pages to fetch (default: 5)."
    )

    # --- New 'presentation' command ---
    parser_presentation = subparsers.add_parser(
        "presentation",
        help="Generate a Marp-compatible Markdown presentation summarizing the project."
    )
    parser_presentation.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory.",
    )
    parser_presentation.add_argument(
        "-o", "--output",
        default="presentation.md",
        help="Output file path (default: presentation.md)."
    )
    parser_presentation.add_argument(
        "--theme",
        default="default",
        help="Marp theme (default, gaia, uncover)."
    )
    parser_presentation.add_argument(
        "-a", "--agent",
        choices=list(AVAILABLE_AGENTS.keys()),
        default="gemini",
        help="Which agent to use (default: gemini)."
    )
    parser_presentation.add_argument(
        "-m", "--model",
        type=str,
        help="Model to use (overrides default)."
    )

    # --- New 'serve' command ---
    parser_serve = subparsers.add_parser(
        "serve",
        help="Start a local development server with auto-detection."
    )
    parser_serve.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory."
    )
    parser_serve.add_argument(
        "--port",
        type=int,
        help="Port to bind to (overrides auto-detection)."
    )
    parser_serve.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)."
    )
    parser_serve.add_argument(
        "--command",
        dest="command_str",
        help="Manually specify the start command (e.g. 'npm run dev')."
    )
    parser_serve.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the start command without running it."
    )

    # --- New 'ide' command ---
    parser_ide = subparsers.add_parser(
        "ide",
        help="Generate IDE configuration files (vscode, cursor)."
    )
    ide_subparsers = parser_ide.add_subparsers(
        dest="action",
        required=True,
        help="Editor to configure."
    )

    # ide vscode
    parser_ide_vscode = ide_subparsers.add_parser("vscode", help="Configure VS Code.")
    parser_ide_vscode.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")
    parser_ide_vscode.add_argument("--dry-run", action="store_true", help="Print config without writing.")
    parser_ide_vscode.add_argument("--force", action="store_true", help="Overwrite existing config.")

    # ide cursor (alias)
    parser_ide_cursor = ide_subparsers.add_parser("cursor", help="Configure Cursor (same as VS Code).")
    parser_ide_cursor.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")
    parser_ide_cursor.add_argument("--dry-run", action="store_true", help="Print config without writing.")
    parser_ide_cursor.add_argument("--force", action="store_true", help="Overwrite existing config.")

    # --- New 'scheduler' command ---
    parser_scheduler = subparsers.add_parser(
        "scheduler",
        help="Run the autonomous maintenance scheduler."
    )
    scheduler_subparsers = parser_scheduler.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # scheduler init
    parser_scheduler_init = scheduler_subparsers.add_parser("init", help="Create default schedule config.")
    parser_scheduler_init.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # scheduler list
    parser_scheduler_list = scheduler_subparsers.add_parser("list", help="List scheduled tasks.")
    parser_scheduler_list.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # scheduler start
    parser_scheduler_start = scheduler_subparsers.add_parser("start", help="Start the scheduler loop.")
    parser_scheduler_start.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # --- New 'chaos' command ---
    parser_chaos = subparsers.add_parser(
        "chaos",
        help="Run chaos engineering experiments to test resilience."
    )
    chaos_subparsers = parser_chaos.add_subparsers(
        dest="action",
        required=True,
        help="Chaos experiment to run."
    )

    # chaos list
    parser_chaos_list = chaos_subparsers.add_parser("list", help="List available experiments.")
    parser_chaos_list.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # chaos kill-process
    parser_chaos_kill = chaos_subparsers.add_parser("kill-process", help="Kill random development processes.")
    parser_chaos_kill.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")
    parser_chaos_kill.add_argument("--dry-run", action="store_true", help="Simulate the action.")
    parser_chaos_kill.add_argument("-y", "--yes", action="store_true", help="Skip confirmation.")

    # chaos file-jitter
    parser_chaos_jitter = chaos_subparsers.add_parser("file-jitter", help="Touch random source files.")
    parser_chaos_jitter.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")
    parser_chaos_jitter.add_argument("--dry-run", action="store_true", help="Simulate the action.")
    parser_chaos_jitter.add_argument("-y", "--yes", action="store_true", help="Skip confirmation.")

    # chaos network-latency
    parser_chaos_latency = chaos_subparsers.add_parser("network-latency", help="Inject network latency.")
    parser_chaos_latency.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")
    parser_chaos_latency.add_argument("--interface", "-i", default="eth0", help="Network interface (default: eth0).")
    parser_chaos_latency.add_argument("--dry-run", action="store_true", help="Simulate the action.")
    parser_chaos_latency.add_argument("-y", "--yes", action="store_true", help="Skip confirmation.")

    # chaos network-loss
    parser_chaos_loss = chaos_subparsers.add_parser("network-loss", help="Inject network packet loss.")
    parser_chaos_loss.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")
    parser_chaos_loss.add_argument("--interface", "-i", default="eth0", help="Network interface (default: eth0).")
    parser_chaos_loss.add_argument("--dry-run", action="store_true", help="Simulate the action.")
    parser_chaos_loss.add_argument("-y", "--yes", action="store_true", help="Skip confirmation.")

    # chaos network-reset
    parser_chaos_reset = chaos_subparsers.add_parser("network-reset", help="Reset network rules.")
    parser_chaos_reset.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")
    parser_chaos_reset.add_argument("--interface", "-i", default="eth0", help="Network interface (default: eth0).")
    parser_chaos_reset.add_argument("--dry-run", action="store_true", help="Simulate the action.")
    parser_chaos_reset.add_argument("-y", "--yes", action="store_true", help="Skip confirmation.")

    # --- New 'guardrails' command ---
    parser_guardrails = subparsers.add_parser(
        "guardrails",
        help="Enforce project policies and standards."
    )
    guardrails_subparsers = parser_guardrails.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # guardrails init
    parser_gr_init = guardrails_subparsers.add_parser("init", help="Create default configuration.")
    parser_gr_init.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # guardrails list
    parser_gr_list = guardrails_subparsers.add_parser("list", help="List active policies.")
    parser_gr_list.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # guardrails check
    parser_gr_check = guardrails_subparsers.add_parser("check", help="Run policy checks.")
    parser_gr_check.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # --- New 'logic-lab' command ---
    parser_logic_lab = subparsers.add_parser(
        "logic-lab",
        help="Truth Table Generator and Logic Lab."
    )
    logic_lab_subparsers = parser_logic_lab.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # logic-lab table
    parser_logic_table = logic_lab_subparsers.add_parser("table", help="Generate a truth table.")
    parser_logic_table.add_argument("--expression", "-e", required=True, help="Boolean expression (e.g. 'A and B').")

    # --- New 'devtools' command ---
    parser_devtools = subparsers.add_parser(
        "devtools",
        help="Developer utilities (epoch, base64, uuid, hash, json)."
    )
    devtools_subparsers = parser_devtools.add_subparsers(
        dest="action",
        required=True,
        help="Tool to use."
    )

    # devtools epoch
    parser_dt_epoch = devtools_subparsers.add_parser("epoch", help="Convert timestamp <-> date.")
    parser_dt_epoch.add_argument("value", nargs="?", help="Timestamp or Date string (optional, defaults to now).")

    # devtools uuid
    parser_dt_uuid = devtools_subparsers.add_parser("uuid", help="Generate UUID v4.")

    # devtools base64
    parser_dt_b64 = devtools_subparsers.add_parser("base64", help="Encode/Decode Base64.")
    parser_dt_b64.add_argument("text", help="Text to process.")
    parser_dt_b64.add_argument("--decode", "-d", action="store_true", help="Decode instead of encode.")

    # devtools hash
    parser_dt_hash = devtools_subparsers.add_parser("hash", help="Calculate hash.")
    parser_dt_hash.add_argument("text", help="Text to hash.")
    parser_dt_hash.add_argument("--algo", default="sha256", help="Algorithm (default: sha256).")

    # devtools json
    parser_dt_json = devtools_subparsers.add_parser("json", help="Format/Validate JSON.")
    parser_dt_json.add_argument("text", help="JSON string.")

    # --- New 'kata' command ---
    parser_kata = subparsers.add_parser(
        "kata",
        help="Play the Refactoring Kata game."
    )
    kata_subparsers = parser_kata.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # kata list
    parser_kata_list = kata_subparsers.add_parser("list", help="List available challenges.")
    parser_kata_list.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")
    parser_kata_list.add_argument("-l", "--limit", type=int, default=10, help="Limit number of challenges.")

    # kata start
    parser_kata_start = kata_subparsers.add_parser("start", help="Start a challenge.")
    parser_kata_start.add_argument("--index", type=int, required=True, help="Challenge number from list.")
    parser_kata_start.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")
    parser_kata_start.add_argument("-l", "--limit", type=int, default=10, help="Limit number of challenges (to match list index).")

    # kata verify
    parser_kata_verify = kata_subparsers.add_parser("verify", help="Verify solution.")
    parser_kata_verify.add_argument("--file", required=True, help="File path.")
    parser_kata_verify.add_argument("--function", required=True, help="Function name.")
    parser_kata_verify.add_argument("--target", type=int, required=True, help="Original complexity.")
    parser_kata_verify.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # --- New 'standup' command ---
    parser_standup = subparsers.add_parser(
        "standup",
        help="Generate a daily standup report based on git activity."
    )
    parser_standup.add_argument(
        "--since",
        default="24 hours ago",
        help="Time window to analyze (default: '24 hours ago')."
    )
    parser_standup.add_argument(
        "--author",
        help="Filter commits by author (defaults to current user)."
    )
    parser_standup.add_argument(
        "-a", "--agent",
        choices=list(AVAILABLE_AGENTS.keys()),
        default="gemini",
        help="Which agent to use (default: gemini)."
    )
    parser_standup.add_argument(
        "-m", "--model",
        type=str,
        help="Model to use (overrides default)."
    )
    parser_standup.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging."
    )

    # --- New 'network' command ---
    parser_network = subparsers.add_parser(
        "network",
        help="Generate an interactive network graph of the codebase (files, imports, authors)."
    )
    parser_network.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory."
    )
    parser_network.add_argument(
        "-o", "--output",
        default="network_graph.html",
        help="Output HTML file path (default: network_graph.html)."
    )
    parser_network.add_argument(
        "--include-authors",
        action="store_true",
        help="Include authors as nodes in the graph."
    )
    parser_network.add_argument(
        "--no-git",
        dest="include_git",
        action="store_false",
        help="Disable git history analysis (co-edits)."
    )
    parser_network.set_defaults(include_git=True)
    parser_network.add_argument(
        "-l", "--limit",
        type=int,
        default=100,
        help="Limit the number of commits to analyze for co-edits (default: 100)."
    )

    # --- New 'tour' command ---
    parser_tour = subparsers.add_parser(
        "tour",
        help="Manage interactive code tours."
    )
    tour_subparsers = parser_tour.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # tour list
    parser_tour_list = tour_subparsers.add_parser("list", help="List available tours.")
    parser_tour_list.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # tour create
    parser_tour_create = tour_subparsers.add_parser("create", help="Create a new tour.")
    parser_tour_create.add_argument("name", help="Tour name.")
    parser_tour_create.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # tour delete
    parser_tour_delete = tour_subparsers.add_parser("delete", help="Delete a tour.")
    parser_tour_delete.add_argument("name", help="Tour name.")
    parser_tour_delete.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # tour add-step
    parser_tour_add = tour_subparsers.add_parser("add-step", help="Add a step to a tour.")
    parser_tour_add.add_argument("name", help="Tour name.")
    parser_tour_add.add_argument("file", help="File path.")
    parser_tour_add.add_argument("line", type=int, help="Line number.")
    parser_tour_add.add_argument("description", nargs="?", help="Description.")
    parser_tour_add.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # tour play
    parser_tour_play = tour_subparsers.add_parser("play", help="Play a tour.")
    parser_tour_play.add_argument("name", help="Tour name.")
    parser_tour_play.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # --- New 'sanitize' command ---
    parser_sanitize = subparsers.add_parser(
        "sanitize",
        help="Sanitize PII (Personally Identifiable Information) from files or text."
    )
    sanitize_subparsers = parser_sanitize.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # sanitize text
    parser_sanitize_text = sanitize_subparsers.add_parser("text", help="Sanitize a text string.")
    parser_sanitize_text.add_argument("text", help="Text to sanitize.")

    # sanitize file
    parser_sanitize_file = sanitize_subparsers.add_parser("file", help="Sanitize a file.")
    parser_sanitize_file.add_argument("file", help="File path.")
    parser_sanitize_file.add_argument("-o", "--output", help="Output path (default: overwrite).")
    parser_sanitize_file.add_argument("--dry-run", action="store_true", help="Check without modifying.")

    # sanitize check
    parser_sanitize_check = sanitize_subparsers.add_parser("check", help="Check for PII without modifying.")
    parser_sanitize_check.add_argument("--text", help="Text to check.")
    parser_sanitize_check.add_argument("--file", help="File to check.")

    # --- New 'gantt' command ---
    parser_gantt = subparsers.add_parser(
        "gantt",
        help="Visualize the sprint plan as a Gantt chart."
    )
    parser_gantt.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory."
    )

    # --- New 'kanban' command ---
    parser_kanban = subparsers.add_parser(
        "kanban",
        help="Manage tasks with a Kanban board."
    )
    parser_kanban.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory."
    )
    parser_kanban.set_defaults(action="view")

    kanban_subparsers = parser_kanban.add_subparsers(
        dest="action",
        required=False,
        help="Action to perform."
    )

    # kanban view
    parser_kanban_view = kanban_subparsers.add_parser("view", help="View the Kanban board.")
    parser_kanban_view.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="The project directory.")

    # kanban move
    parser_kanban_move = kanban_subparsers.add_parser("move", help="Move a task to a new status.")
    parser_kanban_move.add_argument("task_id", help="The ID of the task to move.")
    parser_kanban_move.add_argument("status", help="The new status (todo, in_progress, done).")
    parser_kanban_move.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="The project directory.")

    # --- New 'resume' command ---
    parser_resume = subparsers.add_parser(
        "resume",
        help="Generate a professional Project Resume (One-Pager)."
    )
    parser_resume.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory.",
    )
    parser_resume.add_argument(
        "-o", "--output",
        help="Output file path (default: print to stdout)."
    )
    parser_resume.add_argument(
        "-a", "--agent",
        choices=list(AVAILABLE_AGENTS.keys()),
        default="gemini",
        help="Which agent to use (default: gemini)."
    )
    parser_resume.add_argument(
        "-m", "--model",
        type=str,
        help="Model to use (overrides default)."
    )

    # --- New 'retro' command ---
    parser_retro = subparsers.add_parser(
        "retro",
        help="Conduct a retrospective on agent execution runs."
    )
    parser_retro.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory.",
    )
    parser_retro.add_argument(
        "--run-id",
        help="Specific run ID to analyze (defaults to last run)."
    )
    parser_retro.add_argument(
        "-o", "--output",
        help="Output file for the retrospective report."
    )
    parser_retro.add_argument(
        "-a", "--agent",
        choices=list(AVAILABLE_AGENTS.keys()),
        default="gemini",
        help="Which agent to use for analysis (default: gemini)."
    )
    parser_retro.add_argument(
        "-m", "--model",
        type=str,
        help="Model to use (overrides default)."
    )

    # --- New 'smart-context' command ---
    parser_smart_context = subparsers.add_parser(
        "smart-context",
        help="Generate a dependency-aware context bundle for a file."
    )
    parser_smart_context.add_argument(
        "file",
        help="Target file to analyze."
    )
    parser_smart_context.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory."
    )
    parser_smart_context.add_argument(
        "--depth",
        type=int,
        default=1,
        help="Depth of import analysis (default: 1)."
    )
    parser_smart_context.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Limit for history/coupling analysis (default: 10)."
    )
    parser_smart_context.add_argument(
        "-o", "--output",
        choices=["text", "json"],
        default="text",
        help="Output format."
    )

    # --- New 'port' command ---
    parser_port = subparsers.add_parser(
        "port",
        help="Manage network ports (check, list, kill)."
    )
    port_subparsers = parser_port.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # port list
    parser_port_list = port_subparsers.add_parser("list", help="List listening ports.")

    # port check
    parser_port_check = port_subparsers.add_parser("check", help="Check if a port is in use.")
    parser_port_check.add_argument("port", type=int, help="Port number.")

    # port kill
    parser_port_kill = port_subparsers.add_parser("kill", help="Kill process on port.")
    parser_port_kill.add_argument("port", type=int, help="Port number.")
    parser_port_kill.add_argument("-f", "--force", action="store_true", help="Force kill.")

    # port wait
    parser_port_wait = port_subparsers.add_parser("wait", help="Wait for port state.")
    parser_port_wait.add_argument("port", type=int, help="Port number.")
    parser_port_wait.add_argument("state", choices=["open", "closed"], help="State to wait for.")
    parser_port_wait.add_argument("-t", "--timeout", type=int, default=30, help="Timeout in seconds.")

    # --- New 'color-lab' command ---
    parser_color_lab = subparsers.add_parser(
        "color-lab",
        help="Color utilities (WCAG contrast, palette, blindness simulation)."
    )
    color_lab_subparsers = parser_color_lab.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # color-lab check
    parser_cl_check = color_lab_subparsers.add_parser("check", help="Check contrast between two colors.")
    parser_cl_check.add_argument("color1", help="Foreground color (hex, rgb).")
    parser_cl_check.add_argument("color2", help="Background color (hex, rgb).")

    # color-lab palette
    parser_cl_palette = color_lab_subparsers.add_parser("palette", help="Generate a color palette.")
    parser_cl_palette.add_argument("base", help="Base color.")
    parser_cl_palette.add_argument(
        "--algorithm", "-a",
        choices=["complementary", "analogous", "triadic", "tetradic", "monochromatic"],
        default="complementary",
        help="Palette algorithm."
    )

    # color-lab simulate
    parser_cl_sim = color_lab_subparsers.add_parser("simulate", help="Simulate color blindness.")
    parser_cl_sim.add_argument("color", help="Color to simulate.")

    # color-lab convert
    parser_cl_conv = color_lab_subparsers.add_parser("convert", help="Convert color formats.")
    parser_cl_conv.add_argument("color", help="Color to convert.")

    # color-lab extract
    parser_cl_ext = color_lab_subparsers.add_parser("extract", help="Extract prominent colors from an image.")
    parser_cl_ext.add_argument("image", help="Image file path.")
    parser_cl_ext.add_argument("--limit", "-l", type=int, default=5, help="Number of colors to extract.")

    # --- New 'data-lab' command ---
    parser_data_lab = subparsers.add_parser(
        "data-lab",
        help="Data utilities (convert, validate, info)."
    )
    parser_data_lab.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")
    data_lab_subparsers = parser_data_lab.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # data-lab convert
    parser_dl_convert = data_lab_subparsers.add_parser("convert", help="Convert data file format.")
    parser_dl_convert.add_argument("source", help="Source file path.")
    parser_dl_convert.add_argument("target_format", choices=["json", "yaml", "csv", "xml"], help="Target format.")
    parser_dl_convert.add_argument("-o", "--output", help="Output file path (default: stdout).")

    # data-lab validate
    parser_dl_validate = data_lab_subparsers.add_parser("validate", help="Validate data file.")
    parser_dl_validate.add_argument("file", help="File to validate.")
    parser_dl_validate.add_argument("--schema", help="JSON Schema file path (for JSON files).")

    # data-lab info
    parser_dl_info = data_lab_subparsers.add_parser("info", help="Show data statistics.")
    parser_dl_info.add_argument("file", help="File to analyze.")

    # --- New 'schema-lab' command ---
    parser_schema_lab = subparsers.add_parser(
        "schema-lab",
        help="Schema tools (infer from data, convert to TS/Pydantic)."
    )
    parser_schema_lab.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")
    schema_lab_subparsers = parser_schema_lab.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # schema-lab infer
    parser_sl_infer = schema_lab_subparsers.add_parser("infer", help="Infer JSON Schema from a data file.")
    parser_sl_infer.add_argument("file", help="Input data file (JSON/YAML).")
    parser_sl_infer.add_argument("-o", "--output", help="Output schema file (default: stdout).")

    # schema-lab convert
    parser_sl_convert = schema_lab_subparsers.add_parser("convert", help="Convert JSON Schema to other formats.")
    parser_sl_convert.add_argument("file", help="Input JSON Schema file.")
    parser_sl_convert.add_argument("format", choices=["ts", "pydantic"], help="Target format.")
    parser_sl_convert.add_argument("-n", "--name", help="Root interface/model name.")
    parser_sl_convert.add_argument("-o", "--output", help="Output file (default: stdout).")

    # --- New 'code-query' command ---
    parser_cq = subparsers.add_parser(
        "code-query",
        aliases=["cq"],
        help="Query the codebase structure (find classes, functions, etc.)."
    )
    parser_cq.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")
    parser_cq.add_argument("--name", help="Filter by name (glob or regex).")
    parser_cq.add_argument("--type", choices=["class", "function", "module"], help="Filter by type.")
    parser_cq.add_argument("--imports", help="Filter by imported module (glob or regex).")
    parser_cq.add_argument("--bases", help="Filter by base class (glob or regex).")
    parser_cq.add_argument("--decorator", help="Filter by decorator (glob or regex).")
    parser_cq.add_argument("--json", action="store_true", help="Output results as JSON.")

    # --- New 'badges' command ---
    parser_badges = subparsers.add_parser(
        "badges",
        help="Generate status badges for the project."
    )
    parser_badges.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")
    badges_subparsers = parser_badges.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # badges create
    parser_badges_create = badges_subparsers.add_parser("create", help="Create a custom badge.")
    parser_badges_create.add_argument("--label", required=True, help="Badge label (left side).")
    parser_badges_create.add_argument("--value", required=True, help="Badge value (right side).")
    parser_badges_create.add_argument("--color", default="#4c1", help="Badge color (hex).")
    parser_badges_create.add_argument("-o", "--output", help="Output file path (default: badge.svg).")

    # badges generate
    parser_badges_gen = badges_subparsers.add_parser("generate", help="Generate standard project badges.")
    parser_badges_gen.add_argument("--update-readme", action="store_true", help="Inject/Update badges in README.md.")

    # --- New 'cidr-lab' command ---
    parser_cidr_lab = subparsers.add_parser(
        "cidr-lab",
        aliases=["cidr"],
        help="CIDR and IP utilities (info, contains, overlaps, subnet)."
    )
    cidr_lab_subparsers = parser_cidr_lab.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # cidr-lab info
    parser_cl_info = cidr_lab_subparsers.add_parser("info", help="Get details about a CIDR block.")
    parser_cl_info.add_argument("cidr", help="CIDR block (e.g. 192.168.1.0/24).")

    # cidr-lab contains
    parser_cl_contains = cidr_lab_subparsers.add_parser("contains", help="Check if IP/CIDR is inside another.")
    parser_cl_contains.add_argument("cidr", help="Container CIDR.")
    parser_cl_contains.add_argument("target", help="Target IP or CIDR to check.")

    # cidr-lab overlaps
    parser_cl_overlaps = cidr_lab_subparsers.add_parser("overlaps", help="Check if two subnets overlap.")
    parser_cl_overlaps.add_argument("cidr1", help="First CIDR.")
    parser_cl_overlaps.add_argument("cidr2", help="Second CIDR.")

    # cidr-lab subnet
    parser_cl_subnet = cidr_lab_subparsers.add_parser("subnet", help="Split a network into smaller subnets.")
    parser_cl_subnet.add_argument("cidr", help="Base CIDR.")
    parser_cl_subnet.add_argument("new_prefix", type=int, help="New prefix length.")

    # --- New 'jwt-lab' command ---
    parser_jwt = subparsers.add_parser(
        "jwt-lab",
        help="JWT utilities (decode, sign, verify)."
    )
    jwt_subparsers = parser_jwt.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # jwt-lab decode
    parser_jwt_decode = jwt_subparsers.add_parser("decode", help="Decode a JWT token (no verification).")
    parser_jwt_decode.add_argument("token", help="The JWT token.")

    # jwt-lab sign
    parser_jwt_sign = jwt_subparsers.add_parser("sign", help="Sign a JWT token.")
    parser_jwt_sign.add_argument("--payload", required=True, help="JSON payload string.")
    parser_jwt_sign.add_argument("--secret", required=True, help="Secret key.")

    # jwt-lab verify
    parser_jwt_verify = jwt_subparsers.add_parser("verify", help="Verify a JWT token signature.")
    parser_jwt_verify.add_argument("token", help="The JWT token.")
    parser_jwt_verify.add_argument("--secret", required=True, help="Secret key.")
    parser_jwt_verify.add_argument("-v", "--verbose", action="store_true", help="Show decoded content if valid.")

    # --- New 'uuid-lab' command ---
    parser_uuid = subparsers.add_parser(
        "uuid-lab",
        aliases=["uuid"],
        help="UUID Generator and Inspector."
    )
    uuid_subparsers = parser_uuid.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # uuid generate
    parser_uuid_gen = uuid_subparsers.add_parser("generate", aliases=["gen"], help="Generate UUIDs.")
    parser_uuid_gen.add_argument("--version", "-v", type=int, choices=[1, 3, 4, 5], default=4, help="UUID version (default: 4).")
    parser_uuid_gen.add_argument("--count", "-c", type=int, default=1, help="Number of UUIDs to generate.")
    parser_uuid_gen.add_argument("--namespace", "-ns", help="Namespace for v3/v5 (DNS, URL, OID, X500, or UUID).")
    parser_uuid_gen.add_argument("--name", "-n", help="Name for v3/v5.")

    # uuid inspect
    parser_uuid_inspect = uuid_subparsers.add_parser("inspect", aliases=["info", "decode"], help="Inspect a UUID.")
    parser_uuid_inspect.add_argument("uuid", help="The UUID to inspect.")

    # uuid validate
    parser_uuid_validate = uuid_subparsers.add_parser("validate", aliases=["check"], help="Validate a UUID.")
    parser_uuid_validate.add_argument("uuid", help="The UUID to validate.")

    # uuid bulk
    parser_uuid_bulk = uuid_subparsers.add_parser("bulk", help="Generate bulk v4 UUIDs.")
    parser_uuid_bulk.add_argument("count", type=int, help="Number of UUIDs.")

    # --- New 'password-lab' command ---
    parser_pwd = subparsers.add_parser(
        "password-lab",
        aliases=["pwd-lab"],
        help="Password utilities (generate, check, hash)."
    )
    pwd_subparsers = parser_pwd.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # password-lab generate
    parser_pwd_gen = pwd_subparsers.add_parser("generate", help="Generate a secure random password.")
    parser_pwd_gen.add_argument("-l", "--length", type=int, default=16, help="Password length (default: 16).")
    parser_pwd_gen.add_argument("--no-upper", action="store_true", help="Exclude uppercase letters.")
    parser_pwd_gen.add_argument("--no-lower", action="store_true", help="Exclude lowercase letters.")
    parser_pwd_gen.add_argument("--no-digits", action="store_true", help="Exclude digits.")
    parser_pwd_gen.add_argument("--no-symbols", action="store_true", help="Exclude symbols.")
    parser_pwd_gen.add_argument("-v", "--verbose", action="store_true", help="Show strength analysis.")

    # password-lab check
    parser_pwd_check = pwd_subparsers.add_parser("check", help="Check strength of a password.")
    parser_pwd_check.add_argument("password", nargs="?", help="Password to check (prompts if omitted).")

    # password-lab hash
    parser_pwd_hash = pwd_subparsers.add_parser("hash", help="Hash a password.")
    parser_pwd_hash.add_argument("password", nargs="?", help="Password to hash (prompts if omitted).")
    parser_pwd_hash.add_argument("--algo", choices=["scrypt", "pbkdf2"], default="scrypt", help="Hashing algorithm.")
    parser_pwd_hash.add_argument("--salt", help="Optional salt (random if omitted).")

    # --- New 'text-lab' command ---
    parser_text_lab = subparsers.add_parser(
        "text-lab",
        aliases=["txt"],
        help="Text utilities (transform, encode, info, diff)."
    )
    text_lab_subparsers = parser_text_lab.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # text-lab transform
    parser_tl_transform = text_lab_subparsers.add_parser("transform", help="Transform text case.")
    parser_tl_transform.add_argument("--type", "-t", required=True, choices=["upper", "lower", "title", "camel", "snake", "kebab", "pascal", "constant"], help="Transformation type.")
    parser_tl_transform.add_argument("text", nargs="?", help="Input text (optional, reads from stdin if omitted).")

    # text-lab encode
    parser_tl_encode = text_lab_subparsers.add_parser("encode", help="Encode/Decode text.")
    parser_tl_encode.add_argument("--type", "-t", required=True, choices=["base64", "url", "html", "hex"], help="Encoding type.")
    parser_tl_encode.add_argument("--decode", "-d", action="store_true", help="Decode instead of encode.")
    parser_tl_encode.add_argument("text", nargs="?", help="Input text (optional, reads from stdin if omitted).")

    # text-lab info
    parser_tl_info = text_lab_subparsers.add_parser("info", help="Show text statistics.")
    parser_tl_info.add_argument("text", nargs="?", help="Input text (optional, reads from stdin if omitted).")

    # text-lab diff
    parser_tl_diff = text_lab_subparsers.add_parser("diff", help="Diff two text inputs.")
    parser_tl_diff.add_argument("text1", help="First text.")
    parser_tl_diff.add_argument("text2", help="Second text.")

    # text-lab sort-lines
    parser_tl_sort = text_lab_subparsers.add_parser("sort-lines", aliases=["sort"], help="Sort lines.")
    parser_tl_sort.add_argument("--reverse", "-r", action="store_true", help="Sort in reverse order.")
    parser_tl_sort.add_argument("text", nargs="?", help="Input text (optional, reads from stdin if omitted).")

    # text-lab unique-lines
    parser_tl_unique = text_lab_subparsers.add_parser("unique-lines", aliases=["unique", "uniq"], help="Remove duplicate lines.")
    parser_tl_unique.add_argument("text", nargs="?", help="Input text (optional, reads from stdin if omitted).")

    # text-lab reverse-lines
    parser_tl_reverse = text_lab_subparsers.add_parser("reverse-lines", aliases=["reverse", "rev"], help="Reverse lines.")
    parser_tl_reverse.add_argument("text", nargs="?", help="Input text (optional, reads from stdin if omitted).")

    # text-lab shuffle-lines
    parser_tl_shuffle = text_lab_subparsers.add_parser("shuffle-lines", aliases=["shuffle"], help="Shuffle lines.")
    parser_tl_shuffle.add_argument("text", nargs="?", help="Input text (optional, reads from stdin if omitted).")

    # text-lab number-lines
    parser_tl_number = text_lab_subparsers.add_parser("number-lines", aliases=["number", "num"], help="Number lines.")
    parser_tl_number.add_argument("text", nargs="?", help="Input text (optional, reads from stdin if omitted).")

    # text-lab trim-lines
    parser_tl_trim = text_lab_subparsers.add_parser("trim-lines", aliases=["trim"], help="Trim lines.")
    parser_tl_trim.add_argument("text", nargs="?", help="Input text (optional, reads from stdin if omitted).")

    # text-lab filter-lines
    parser_tl_filter = text_lab_subparsers.add_parser("filter-lines", aliases=["filter", "grep"], help="Filter lines by regex.")
    parser_tl_filter.add_argument("pattern", help="Regex pattern.")
    parser_tl_filter.add_argument("--exclude", "-v", action="store_true", help="Exclude matches.")
    parser_tl_filter.add_argument("text", nargs="?", help="Input text (optional, reads from stdin if omitted).")

    # --- New 'html-lab' command ---
    parser_html = subparsers.add_parser(
        "html-lab",
        aliases=["html"],
        help="HTML utilities (extract, clean, table, validate)."
    )
    parser_html.add_argument("--file", help="Input HTML file (defaults to stdin).")
    html_subparsers = parser_html.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # html-lab extract
    parser_html_extract = html_subparsers.add_parser("extract", help="Extract content from tags.")
    parser_html_extract.add_argument("--tag", help="Tag name to extract.")
    parser_html_extract.add_argument("--attr", help="Attribute to extract (returns text if omitted).")
    parser_html_extract.add_argument("--id", help="Filter by ID.")
    parser_html_extract.add_argument("--class-name", help="Filter by class name.")

    # html-lab clean
    parser_html_clean = html_subparsers.add_parser("clean", help="Strip tags from HTML.")
    parser_html_clean.add_argument("--keep", help="Comma-separated list of tags to keep.")

    # html-lab table
    parser_html_table = html_subparsers.add_parser("table", help="Parse HTML table to CSV/JSON.")
    parser_html_table.add_argument("--index", type=int, default=0, help="Table index (default: 0).")
    parser_html_table.add_argument("--format", choices=["csv", "json"], default="csv", help="Output format.")

    # html-lab validate
    parser_html_validate = html_subparsers.add_parser("validate", help="Validate HTML structure.")

    # --- New 'url-lab' command ---
    parser_url_lab = subparsers.add_parser(
        "url-lab",
        aliases=["url"],
        help="URL utilities (parse, encode, decode, join, params, normalize)."
    )
    url_lab_subparsers = parser_url_lab.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # url-lab parse
    parser_ul_parse = url_lab_subparsers.add_parser("parse", help="Parse a URL into components.")
    parser_ul_parse.add_argument("url", help="URL to parse.")

    # url-lab encode
    parser_ul_encode = url_lab_subparsers.add_parser("encode", help="URL encode text.")
    parser_ul_encode.add_argument("text", help="Text to encode.")

    # url-lab decode
    parser_ul_decode = url_lab_subparsers.add_parser("decode", help="URL decode text.")
    parser_ul_decode.add_argument("text", help="Text to decode.")

    # url-lab join
    parser_ul_join = url_lab_subparsers.add_parser("join", help="Join a base URL with paths.")
    parser_ul_join.add_argument("base", help="Base URL.")
    parser_ul_join.add_argument("paths", nargs="+", help="Paths to join.")

    # url-lab params
    parser_ul_params = url_lab_subparsers.add_parser("params", help="Manage query parameters.")
    parser_ul_params.add_argument("url", help="Base URL.")
    parser_ul_params.add_argument("mode", choices=["list", "add", "remove", "set", "get"], help="Action mode.")
    parser_ul_params.add_argument("--key", help="Parameter key.")
    parser_ul_params.add_argument("--value", help="Parameter value.")

    # url-lab normalize
    parser_ul_norm = url_lab_subparsers.add_parser("normalize", help="Normalize a URL.")
    parser_ul_norm.add_argument("url", help="URL to normalize.")

    # --- New 'cert-lab' command ---
    parser_cert = subparsers.add_parser(
        "cert-lab",
        aliases=["cert"],
        help="Certificate utilities (inspect, generate)."
    )
    cert_subparsers = parser_cert.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # cert-lab inspect
    parser_cert_inspect = cert_subparsers.add_parser("inspect", help="Inspect a certificate (file or host).")
    parser_cert_inspect.add_argument("target", help="File path or host:port.")

    # cert-lab generate
    parser_cert_gen = cert_subparsers.add_parser("generate", help="Generate a self-signed certificate.")
    parser_cert_gen.add_argument("--common-name", "--cn", required=True, help="Common Name (CN).")
    parser_cert_gen.add_argument("--san", action="append", help="Subject Alternative Name (repeatable).")
    parser_cert_gen.add_argument("--days", type=int, default=365, help="Validity in days.")
    parser_cert_gen.add_argument("-o", "--output", help="Output directory.")

    # --- New 'time-lab' command ---
    parser_time = subparsers.add_parser(
        "time-lab",
        aliases=["time"],
        help="Time utilities (now, convert, diff, epoch, zones)."
    )
    time_subparsers = parser_time.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # time-lab now
    parser_time_now = time_subparsers.add_parser("now", help="Show current time.")
    parser_time_now.add_argument("--timezone", "-z", help="Timezone (default: UTC).")

    # time-lab convert
    parser_time_convert = time_subparsers.add_parser("convert", help="Convert time to timezone.")
    parser_time_convert.add_argument("time", help="Time string or timestamp.")
    parser_time_convert.add_argument("to_zone", help="Target timezone.")

    # time-lab diff
    parser_time_diff = time_subparsers.add_parser("diff", help="Calculate time difference.")
    parser_time_diff.add_argument("time1", help="First time.")
    parser_time_diff.add_argument("time2", help="Second time.")

    # time-lab epoch
    parser_time_epoch = time_subparsers.add_parser("epoch", help="Get Unix timestamp.")
    parser_time_epoch.add_argument("time", nargs="?", help="Time string (default: now).")

    # time-lab zones
    parser_time_zones = time_subparsers.add_parser("zones", help="List timezones.")
    parser_time_zones.add_argument("search", nargs="?", help="Search term.")

    # --- New 'math-lab' command ---
    parser_math = subparsers.add_parser(
        "math-lab",
        aliases=["math"],
        help="Math utilities (evaluate, stats, prime)."
    )
    math_subparsers = parser_math.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # math-lab eval
    parser_math_eval = math_subparsers.add_parser("eval", help="Evaluate a math expression.")
    parser_math_eval.add_argument("expression", nargs="?", help="Expression to evaluate (or stdin).")

    # math-lab stats
    parser_math_stats = math_subparsers.add_parser("stats", help="Calculate statistics.")
    parser_math_stats.add_argument("numbers", nargs="*", help="List of numbers (or stdin).")

    # math-lab prime
    parser_math_prime = math_subparsers.add_parser("prime", help="Prime number utilities.")
    parser_math_prime.add_argument("subaction", choices=["check", "next", "factors"], help="Operation: check, next, factors.")
    parser_math_prime.add_argument("number", help="The integer to process.")

    # --- New 'calc-lab' command ---
    parser_calc = subparsers.add_parser(
        "calc-lab",
        aliases=["calc"],
        help="Programmer's Calculator."
    )
    parser_calc.add_argument("expression", nargs="*", help="Mathematical expression to evaluate (or start REPL).")

    # --- New 'unit-lab' command ---
    parser_unit = subparsers.add_parser(
        "unit-lab",
        aliases=["unit"],
        help="Unit conversion utilities (storage, time, length, weight, temperature)."
    )
    unit_subparsers = parser_unit.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # unit-lab convert
    parser_unit_convert = unit_subparsers.add_parser("convert", help="Convert between units.")
    parser_unit_convert.add_argument("value", help="Value to convert.")
    parser_unit_convert.add_argument("from_unit", help="Source unit (e.g., mb, kg, c).")
    parser_unit_convert.add_argument("to_unit", help="Target unit (e.g., gb, lb, f).")

    # unit-lab list
    parser_unit_list = unit_subparsers.add_parser("list", help="List available units.")
    parser_unit_list.add_argument("category", nargs="?", help="Filter by category (storage, time, length, weight, temperature).")

    # --- New 'semver-lab' command ---
    parser_semver = subparsers.add_parser(
        "semver-lab",
        aliases=["semver"],
        help="SemVer utilities (parse, bump, compare, sort, satisfies)."
    )
    semver_subparsers = parser_semver.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # semver-lab parse
    parser_sv_parse = semver_subparsers.add_parser("parse", help="Parse and validate a version string.")
    parser_sv_parse.add_argument("version", help="Version string.")

    # semver-lab bump
    parser_sv_bump = semver_subparsers.add_parser("bump", help="Bump a version part.")
    parser_sv_bump.add_argument("version", help="Base version.")
    parser_sv_bump.add_argument("part", choices=["major", "minor", "patch", "prerelease", "premajor", "preminor", "prepatch"], help="Part to bump.")
    parser_sv_bump.add_argument("--pre-id", default="alpha", help="Identifier for prereleases (default: alpha).")

    # semver-lab compare
    parser_sv_compare = semver_subparsers.add_parser("compare", help="Compare two versions.")
    parser_sv_compare.add_argument("v1", help="First version.")
    parser_sv_compare.add_argument("operator", choices=["==", "eq", "!=", "ne", ">", "gt", "<", "lt", ">=", "ge", "<=", "le"], help="Operator.")
    parser_sv_compare.add_argument("v2", help="Second version.")

    # semver-lab sort
    parser_sv_sort = semver_subparsers.add_parser("sort", help="Sort a list of versions.")
    parser_sv_sort.add_argument("versions", nargs="*", help="Versions to sort (reads from stdin if omitted).")

    # semver-lab satisfies
    parser_sv_satisfies = semver_subparsers.add_parser("satisfies", help="Check if a version satisfies a range.")
    parser_sv_satisfies.add_argument("version", help="Version string.")
    parser_sv_satisfies.add_argument("range", help="Range string (e.g., '>=1.0.0').")

    # --- New 'sys-lab' command ---
    parser_sys = subparsers.add_parser(
        "sys-lab",
        aliases=["sys"],
        help="System utilities (info, proc, kill, disk)."
    )
    sys_subparsers = parser_sys.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # sys-lab info
    parser_sys_info = sys_subparsers.add_parser("info", help="Show system information.")

    # sys-lab proc
    parser_sys_proc = sys_subparsers.add_parser("proc", help="List processes.")
    parser_sys_proc.add_argument("--sort", choices=["cpu", "mem", "pid", "name"], default="cpu", help="Sort by.")
    parser_sys_proc.add_argument("--limit", type=int, default=20, help="Limit number of processes.")
    parser_sys_proc.add_argument("--filter", help="Filter by name.")
    parser_sys_proc.add_argument("--user", help="Filter by user.")

    # sys-lab kill
    parser_sys_kill = sys_subparsers.add_parser("kill", help="Kill a process.")
    parser_sys_kill.add_argument("--pid", type=int, help="Process PID.")
    parser_sys_kill.add_argument("--name", help="Process name.")
    parser_sys_kill.add_argument("--signal", type=int, default=15, help="Signal to send (default: 15/SIGTERM).")
    parser_sys_kill.add_argument("--force", action="store_true", help="Force kill matching processes.")

    # sys-lab disk
    parser_sys_disk = sys_subparsers.add_parser("disk", help="Analyze disk usage.")
    parser_sys_disk.add_argument("path", nargs="?", default=".", help="Directory to analyze.")
    parser_sys_disk.add_argument("--limit", type=int, default=20, help="Limit number of items.")

    # --- New 'log-lab' command ---
    parser_log_lab = subparsers.add_parser(
        "log-lab",
        aliases=["ll"],
        help="Log analysis utilities (parse, filter, stats)."
    )
    parser_log_lab.add_argument("--file", "-f", help="Log file to process.")
    parser_log_lab.add_argument("--run-id", help="Run ID to find log file.")

    log_lab_subparsers = parser_log_lab.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # log-lab parse
    parser_log_parse = log_lab_subparsers.add_parser("parse", help="Parse log file.")
    parser_log_parse.add_argument("--mode", choices=["steps", "raw"], default="steps", help="Parsing mode.")

    # log-lab filter
    parser_log_filter = log_lab_subparsers.add_parser("filter", help="Filter log entries.")
    parser_log_filter.add_argument("--level", "-l", help="Filter by level (INFO, ERROR, etc).")
    parser_log_filter.add_argument("--pattern", "-p", help="Regex pattern to match.")
    parser_log_filter.add_argument("--limit", "-n", type=int, help="Limit results.")
    parser_log_filter.add_argument("--json", action="store_true", help="Output as JSON.")

    # log-lab stats
    parser_log_stats = log_lab_subparsers.add_parser("stats", help="Show log statistics.")
    parser_log_stats.add_argument("--json", action="store_true", help="Output as JSON.")

    # --- New 'sql-lab' command ---
    parser_sql = subparsers.add_parser(
        "sql-lab",
        aliases=["sql"],
        help="SQL utilities (run, list, schema, export)."
    )
    parser_sql.add_argument("--url", help="Database connection URL (defaults to DATABASE_URL env var or auto-detect).")
    sql_subparsers = parser_sql.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # sql-lab run
    parser_sql_run = sql_subparsers.add_parser("run", help="Run a SQL query.")
    parser_sql_run.add_argument("query", help="SQL query to execute.")

    # sql-lab list
    parser_sql_list = sql_subparsers.add_parser("list", help="List tables.")

    # sql-lab schema
    parser_sql_schema = sql_subparsers.add_parser("schema", help="Show schema.")
    parser_sql_schema.add_argument("table", nargs="?", help="Specific table name.")

    # sql-lab export
    parser_sql_export = sql_subparsers.add_parser("export", help="Export query results.")
    parser_sql_export.add_argument("query", help="SQL query to execute.")
    parser_sql_export.add_argument("--format", choices=["csv", "json"], default="csv", help="Output format.")
    parser_sql_export.add_argument("--output", "-o", required=True, help="Output file path.")

    # sql-lab game
    parser_sql_game = sql_subparsers.add_parser("game", help="Play the SQL Learning Game.")

    # --- New 'csv-lab' command ---
    parser_csv = subparsers.add_parser(
        "csv-lab",
        aliases=["csv"],
        help="CSV utilities (read, stats, filter, sort, select)."
    )
    parser_csv.add_argument("--file", "-f", help="Input CSV file.")
    csv_subparsers = parser_csv.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # csv-lab read
    parser_csv_read = csv_subparsers.add_parser("read", help="Read and pretty print CSV.")
    parser_csv_read.add_argument("--limit", type=int, default=50, help="Limit rows displayed.")

    # csv-lab stats
    parser_csv_stats = csv_subparsers.add_parser("stats", help="Show CSV statistics.")

    # csv-lab headers
    parser_csv_headers = csv_subparsers.add_parser("headers", help="List headers.")

    # csv-lab filter
    parser_csv_filter = csv_subparsers.add_parser("filter", help="Filter CSV rows.")
    parser_csv_filter.add_argument("column", help="Column to filter by.")
    parser_csv_filter.add_argument("value", help="Value to match.")
    parser_csv_filter.add_argument("--operator", choices=["eq", "neq", "gt", "lt", "gte", "lte", "contains"], default="eq", help="Comparison operator.")
    parser_csv_filter.add_argument("--output", "-o", help="Output file (default stdout).")

    # csv-lab sort
    parser_csv_sort = csv_subparsers.add_parser("sort", help="Sort CSV rows.")
    parser_csv_sort.add_argument("column", help="Column to sort by.")
    parser_csv_sort.add_argument("--reverse", action="store_true", help="Sort descending.")
    parser_csv_sort.add_argument("--numeric", action="store_true", help="Treat values as numbers.")
    parser_csv_sort.add_argument("--output", "-o", help="Output file (default stdout).")

    # csv-lab select
    parser_csv_select = csv_subparsers.add_parser("select", help="Select specific columns.")
    parser_csv_select.add_argument("columns", help="Comma-separated list of columns.")
    parser_csv_select.add_argument("--output", "-o", help="Output file (default stdout).")

    # --- New 'excel-lab' command ---
    parser_excel = subparsers.add_parser(
        "excel-lab",
        aliases=["xls", "xlsx", "excel"],
        help="Excel utilities (info, read)."
    )
    parser_excel.add_argument("--file", "-f", required=True, help="Input Excel file.")
    excel_subparsers = parser_excel.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # excel-lab info
    parser_excel_info = excel_subparsers.add_parser("info", help="Show Excel file metadata.")

    # excel-lab read
    parser_excel_read = excel_subparsers.add_parser("read", help="Read and output Excel sheet.")
    parser_excel_read.add_argument("--sheet", "-s", help="Sheet name (defaults to active sheet).")
    parser_excel_read.add_argument("--format", choices=["table", "csv", "json"], default="table", help="Output format.")
    parser_excel_read.add_argument("--limit", type=int, default=50, help="Limit rows displayed (table format only).")
    parser_excel_read.add_argument("--output", "-o", help="Output file path (optional).")

    # --- New 'template-lab' command ---
    parser_template = subparsers.add_parser(
        "template-lab",
        aliases=["tpl", "template"],
        help="Template utilities (render, inspect, lint)."
    )
    template_subparsers = parser_template.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # template-lab render
    parser_template_render = template_subparsers.add_parser("render", help="Render a template.")
    parser_template_render.add_argument("template", help="Template file path.")
    parser_template_render.add_argument("--data", "-d", help="Data file (JSON/YAML).")
    parser_template_render.add_argument("--output", "-o", help="Output file path.")
    parser_template_render.add_argument("--var", action="append", help="Override variable (key=value).")

    # template-lab inspect
    parser_template_inspect = template_subparsers.add_parser("inspect", help="Inspect template variables.")
    parser_template_inspect.add_argument("template", help="Template file path.")

    # template-lab lint
    parser_template_lint = template_subparsers.add_parser("lint", help="Lint template syntax.")
    parser_template_lint.add_argument("template", help="Template file path.")

    # --- New 'json-lab' command ---
    parser_json = subparsers.add_parser(
        "json-lab",
        aliases=["json"],
        help="JSON utilities (get, set, del, minify, diff)."
    )
    json_subparsers = parser_json.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # json-lab get
    parser_json_get = json_subparsers.add_parser("get", help="Get value from JSON.")
    parser_json_get.add_argument("input", help="JSON string or file path.")
    parser_json_get.add_argument("path", nargs="?", help="Path to value (e.g. key.subkey[0]).")

    # json-lab set
    parser_json_set = json_subparsers.add_parser("set", help="Set value in JSON.")
    parser_json_set.add_argument("input", help="JSON string or file path.")
    parser_json_set.add_argument("path", help="Path to set.")
    parser_json_set.add_argument("value", help="Value to set.")

    # json-lab del
    parser_json_del = json_subparsers.add_parser("del", help="Delete value from JSON.")
    parser_json_del.add_argument("input", help="JSON string or file path.")
    parser_json_del.add_argument("path", help="Path to delete.")

    # json-lab minify
    parser_json_minify = json_subparsers.add_parser("minify", help="Minify JSON.")
    parser_json_minify.add_argument("input", help="JSON string or file path.")

    # json-lab diff
    parser_json_diff = json_subparsers.add_parser("diff", help="Diff two JSON files.")
    parser_json_diff.add_argument("file1", help="First file.")
    parser_json_diff.add_argument("file2", help="Second file.")

    # --- New 'yaml-lab' command ---
    parser_yaml = subparsers.add_parser(
        "yaml-lab",
        aliases=["yaml"],
        help="YAML utilities (get, set, del, format, merge, json, to-yaml, validate)."
    )
    yaml_subparsers = parser_yaml.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # yaml-lab get
    parser_yaml_get = yaml_subparsers.add_parser("get", help="Get value from YAML.")
    parser_yaml_get.add_argument("input", help="YAML string or file path.")
    parser_yaml_get.add_argument("path", nargs="?", help="Path to value (e.g. key.subkey[0]).")

    # yaml-lab set
    parser_yaml_set = yaml_subparsers.add_parser("set", help="Set value in YAML.")
    parser_yaml_set.add_argument("input", help="YAML string or file path.")
    parser_yaml_set.add_argument("path", help="Path to set.")
    parser_yaml_set.add_argument("value", help="Value to set.")

    # yaml-lab del
    parser_yaml_del = yaml_subparsers.add_parser("del", help="Delete value from YAML.")
    parser_yaml_del.add_argument("input", help="YAML string or file path.")
    parser_yaml_del.add_argument("path", help="Path to delete.")

    # yaml-lab format
    parser_yaml_format = yaml_subparsers.add_parser("format", help="Format YAML.")
    parser_yaml_format.add_argument("input", help="YAML string or file path.")

    # yaml-lab json
    parser_yaml_json = yaml_subparsers.add_parser("json", help="Convert YAML to JSON.")
    parser_yaml_json.add_argument("input", help="YAML string or file path.")

    # yaml-lab to-yaml
    parser_yaml_to_yaml = yaml_subparsers.add_parser("to-yaml", help="Convert JSON to YAML.")
    parser_yaml_to_yaml.add_argument("input", help="JSON string or file path.")

    # yaml-lab merge
    parser_yaml_merge = yaml_subparsers.add_parser("merge", help="Merge two YAML files.")
    parser_yaml_merge.add_argument("base", help="Base YAML file.")
    parser_yaml_merge.add_argument("override", help="Override YAML file.")

    # yaml-lab validate
    parser_yaml_validate = yaml_subparsers.add_parser("validate", help="Validate YAML.")
    parser_yaml_validate.add_argument("input", help="YAML string or file path.")

    # --- New 'toml-lab' command ---
    parser_toml = subparsers.add_parser(
        "toml-lab",
        aliases=["toml"],
        help="TOML utilities (get, set, del, format, json, to-toml, merge, validate)."
    )
    parser_toml.add_argument("--input", "-i", help="Input file or string (default: stdin).")

    toml_subparsers = parser_toml.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # toml-lab get
    parser_toml_get = toml_subparsers.add_parser("get", help="Get value at path.")
    parser_toml_get.add_argument("path", nargs="?", help="Path (dot notation).")

    # toml-lab set
    parser_toml_set = toml_subparsers.add_parser("set", help="Set value at path.")
    parser_toml_set.add_argument("path", help="Path (dot notation).")
    parser_toml_set.add_argument("value", help="Value to set.")

    # toml-lab del
    parser_toml_del = toml_subparsers.add_parser("del", help="Delete key at path.")
    parser_toml_del.add_argument("path", help="Path (dot notation).")

    # toml-lab format
    parser_toml_format = toml_subparsers.add_parser("format", help="Format TOML.")

    # toml-lab json
    parser_toml_json = toml_subparsers.add_parser("json", help="Convert to JSON.")

    # toml-lab to-toml
    parser_toml_to_toml = toml_subparsers.add_parser("to-toml", help="Convert JSON to TOML.")

    # toml-lab merge
    parser_toml_merge = toml_subparsers.add_parser("merge", help="Merge two TOML files.")
    parser_toml_merge.add_argument("base", help="Base TOML file.")
    parser_toml_merge.add_argument("override", help="Override TOML file.")

    # toml-lab validate
    parser_toml_validate = toml_subparsers.add_parser("validate", help="Validate TOML.")
    parser_toml_validate.add_argument("input", nargs="?", default="-", help="Input TOML file or string.")

    # --- New 'crypto-lab' command ---
    parser_crypto = subparsers.add_parser(
        "crypto-lab",
        aliases=["crypto"],
        help="Crypto utilities (hash, encrypt, decrypt, gen-key, random)."
    )
    crypto_subparsers = parser_crypto.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # crypto-lab hash
    parser_crypto_hash = crypto_subparsers.add_parser("hash", help="Calculate hash.")
    parser_crypto_hash.add_argument("--text", help="Input text.")
    parser_crypto_hash.add_argument("--file", help="Input file.")
    parser_crypto_hash.add_argument("--algo", default="sha256", help="Algorithm (md5, sha1, sha256, sha512).")

    # crypto-lab gen-key
    parser_crypto_gen = crypto_subparsers.add_parser("gen-key", help="Generate encryption key.")
    parser_crypto_gen.add_argument("--output", "-o", help="Save key to file.")

    # crypto-lab encrypt
    parser_crypto_enc = crypto_subparsers.add_parser("encrypt", help="Encrypt data.")
    parser_crypto_enc.add_argument("--input", help="Input text.")
    parser_crypto_enc.add_argument("--input-file", help="Input file.")
    parser_crypto_enc.add_argument("--key", help="Key string.")
    parser_crypto_enc.add_argument("--key-file", help="Key file.")
    parser_crypto_enc.add_argument("--output", "-o", help="Output file.")

    # crypto-lab decrypt
    parser_crypto_dec = crypto_subparsers.add_parser("decrypt", help="Decrypt data.")
    parser_crypto_dec.add_argument("--input", help="Input text (base64 encoded if encrypted).")
    parser_crypto_dec.add_argument("--input-file", help="Input file.")
    parser_crypto_dec.add_argument("--key", help="Key string.")
    parser_crypto_dec.add_argument("--key-file", help="Key file.")
    parser_crypto_dec.add_argument("--output", "-o", help="Output file.")

    # crypto-lab random
    parser_crypto_rand = crypto_subparsers.add_parser("random", help="Generate random data.")
    parser_crypto_rand.add_argument("--length", type=int, default=32, help="Length.")
    parser_crypto_rand.add_argument("--type", choices=["hex", "base64", "uuid", "int"], default="hex", help="Type.")

    # --- New 'image-lab' command ---
    parser_image = subparsers.add_parser(
        "image-lab",
        aliases=["img"],
        help="Image utilities (info, convert, resize, placeholder)."
    )
    image_subparsers = parser_image.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # image-lab info
    parser_image_info = image_subparsers.add_parser("info", help="Get image metadata.")
    parser_image_info.add_argument("file", help="Image file path.")

    # image-lab convert
    parser_image_convert = image_subparsers.add_parser("convert", help="Convert image format.")
    parser_image_convert.add_argument("input", help="Input image file.")
    parser_image_convert.add_argument("output", help="Output image file.")
    parser_image_convert.add_argument("--quality", type=int, help="Quality (1-100) for JPEG/WebP.")

    # image-lab resize
    parser_image_resize = image_subparsers.add_parser("resize", help="Resize image.")
    parser_image_resize.add_argument("input", help="Input image file.")
    parser_image_resize.add_argument("output", help="Output image file.")
    parser_image_resize.add_argument("--width", type=int, help="Target width.")
    parser_image_resize.add_argument("--height", type=int, help="Target height.")
    parser_image_resize.add_argument("--no-aspect", action="store_true", help="Do not maintain aspect ratio.")

    # image-lab placeholder
    parser_image_placeholder = image_subparsers.add_parser("placeholder", help="Generate placeholder image.")
    parser_image_placeholder.add_argument("output", help="Output image file.")
    parser_image_placeholder.add_argument("--width", type=int, default=640, help="Width.")
    parser_image_placeholder.add_argument("--height", type=int, default=480, help="Height.")
    parser_image_placeholder.add_argument("--color", default="#CCCCCC", help="Background color.")
    parser_image_placeholder.add_argument("--text", help="Text to overlay.")
    parser_image_placeholder.add_argument("--text-color", default="black", help="Text color.")

    # image-lab hide
    parser_img_hide = image_subparsers.add_parser("hide", help="Hide a secret message in an image.")
    parser_img_hide.add_argument("input", help="Input image path.")
    parser_img_hide.add_argument("output", help="Output image path (will be saved as PNG).")
    parser_img_hide.add_argument("--message", "-m", help="Message to hide (reads from stdin if omitted).")

    # image-lab reveal
    parser_img_reveal = image_subparsers.add_parser("reveal", help="Reveal a secret message from an image.")
    parser_img_reveal.add_argument("input", help="Input image path.")

    # --- New 'media-lab' command ---
    parser_media = subparsers.add_parser(
        "media-lab",
        aliases=["media"],
        help="Media utilities (info, convert, resize, trim, extract-audio)."
    )
    media_subparsers = parser_media.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # media-lab info
    parser_media_info = media_subparsers.add_parser("info", help="Get media metadata.")
    parser_media_info.add_argument("file", help="Input file.")

    # media-lab convert
    parser_media_convert = media_subparsers.add_parser("convert", help="Convert media format.")
    parser_media_convert.add_argument("input", help="Input file.")
    parser_media_convert.add_argument("output", help="Output file.")

    # media-lab resize
    parser_media_resize = media_subparsers.add_parser("resize", help="Resize video.")
    parser_media_resize.add_argument("input", help="Input file.")
    parser_media_resize.add_argument("output", help="Output file.")
    parser_media_resize.add_argument("--width", type=int, help="Target width (-1 for aspect ratio).", default=-1)
    parser_media_resize.add_argument("--height", type=int, help="Target height (-1 for aspect ratio).", default=-1)

    # media-lab extract-audio
    parser_media_audio = media_subparsers.add_parser("extract-audio", help="Extract audio from video.")
    parser_media_audio.add_argument("input", help="Input file.")
    parser_media_audio.add_argument("output", help="Output audio file.")

    # media-lab trim
    parser_media_trim = media_subparsers.add_parser("trim", help="Trim media file.")
    parser_media_trim.add_argument("input", help="Input file.")
    parser_media_trim.add_argument("output", help="Output file.")
    parser_media_trim.add_argument("--start", required=True, help="Start time (e.g. 00:00:10).")
    parser_media_trim.add_argument("--end", help="End time (e.g. 00:00:20).")
    parser_media_trim.add_argument("--duration", help="Duration (e.g. 10).")

    # --- New 'xml-lab' command ---
    parser_xml = subparsers.add_parser(
        "xml-lab",
        aliases=["xml"],
        help="XML utilities (format, validate, xpath, edit, json)."
    )
    parser_xml.add_argument("--input", "-i", help="Input XML file (or stdin if -).")
    xml_subparsers = parser_xml.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # xml-lab format
    parser_xml_format = xml_subparsers.add_parser("format", help="Format XML.")

    # xml-lab validate
    parser_xml_validate = xml_subparsers.add_parser("validate", help="Validate XML.")

    # xml-lab xpath
    parser_xml_xpath = xml_subparsers.add_parser("xpath", help="Run XPath query.")
    parser_xml_xpath.add_argument("--query", "-q", required=True, help="XPath query.")

    # xml-lab edit
    parser_xml_edit = xml_subparsers.add_parser("edit", help="Edit XML.")
    parser_xml_edit.add_argument("--query", "-q", required=True, help="XPath to target element(s).")
    parser_xml_edit.add_argument("--value", "-v", required=True, help="New value.")
    parser_xml_edit.add_argument("--attr", "-a", help="Attribute to modify (modify text content if omitted).")
    parser_xml_edit.add_argument("--output", "-o", help="Output file (default stdout).")

    # xml-lab json
    parser_xml_json = xml_subparsers.add_parser("json", help="Convert to JSON.")

    # --- New 'markdown-lab' command ---
    parser_md = subparsers.add_parser(
        "markdown-lab",
        aliases=["md", "md-lab"],
        help="Markdown utilities (toc, stats, table, lint)."
    )
    md_subparsers = parser_md.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # md-lab toc
    parser_md_toc = md_subparsers.add_parser("toc", help="Generate Table of Contents.")
    parser_md_toc.add_argument("--file", "-f", help="Input file.")
    parser_md_toc.add_argument("--depth", type=int, default=3, help="Max header depth.")
    parser_md_toc.add_argument("--insert", action="store_true", help="Insert into file.")

    # md-lab stats
    parser_md_stats = md_subparsers.add_parser("stats", help="Get markdown statistics.")
    parser_md_stats.add_argument("--file", "-f", help="Input file.")

    # md-lab table
    parser_md_table = md_subparsers.add_parser("table", help="Format markdown tables.")
    parser_md_table.add_argument("--file", "-f", help="Input file.")
    parser_md_table.add_argument("--output", "-o", help="Output file.")

    # md-lab lint
    parser_md_lint = md_subparsers.add_parser("lint", help="Lint markdown file.")
    parser_md_lint.add_argument("--file", "-f", help="Input file.")
    parser_md_lint.add_argument("--root", help="Root directory for link checking.")

    # --- New 'net-lab' command ---
    parser_net = subparsers.add_parser(
        "net-lab",
        aliases=["net"],
        help="Network utilities (scan, dns, head, ping, ip)."
    )
    net_subparsers = parser_net.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # net-lab scan
    parser_net_scan = net_subparsers.add_parser("scan", help="Scan ports.")
    parser_net_scan.add_argument("host", help="Target host.")
    parser_net_scan.add_argument("--ports", help="Ports to scan (e.g. 80,443 or 1-100).")

    # net-lab dns
    parser_net_dns = net_subparsers.add_parser("dns", help="DNS Lookup.")
    parser_net_dns.add_argument("domain", help="Domain to lookup.")
    parser_net_dns.add_argument("--type", default="A", help="Record type (A, AAAA).")

    # net-lab head
    parser_net_head = net_subparsers.add_parser("head", help="HTTP Headers.")
    parser_net_head.add_argument("url", help="Target URL.")

    # net-lab ping
    parser_net_ping = net_subparsers.add_parser("ping", help="Ping host.")
    parser_net_ping.add_argument("host", help="Target host.")
    parser_net_ping.add_argument("--count", type=int, default=4, help="Ping count.")

    # net-lab ip
    parser_net_ip = net_subparsers.add_parser("ip", help="Get IP info.")

    # --- New 'pdf-lab' command ---
    parser_pdf = subparsers.add_parser(
        "pdf-lab",
        aliases=["pdf"],
        help="PDF utilities (info, text, merge, split)."
    )
    pdf_subparsers = parser_pdf.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # pdf-lab info
    parser_pdf_info = pdf_subparsers.add_parser("info", help="Get PDF metadata.")
    parser_pdf_info.add_argument("file", help="PDF file path.")

    # pdf-lab text
    parser_pdf_text = pdf_subparsers.add_parser("text", help="Extract text from PDF.")
    parser_pdf_text.add_argument("file", help="PDF file path.")
    parser_pdf_text.add_argument("--start", type=int, help="Start page (0-indexed).")
    parser_pdf_text.add_argument("--end", type=int, help="End page.")
    parser_pdf_text.add_argument("--output", "-o", help="Output text file.")

    # pdf-lab merge
    parser_pdf_merge = pdf_subparsers.add_parser("merge", help="Merge multiple PDFs.")
    parser_pdf_merge.add_argument("output", help="Output PDF file.")
    parser_pdf_merge.add_argument("inputs", nargs="+", help="Input PDF files.")

    # pdf-lab split
    parser_pdf_split = pdf_subparsers.add_parser("split", help="Split PDF into pages.")
    parser_pdf_split.add_argument("file", help="Input PDF file.")
    parser_pdf_split.add_argument("output_dir", help="Output directory.")

    # --- New 'archive-lab' command ---
    parser_archive = subparsers.add_parser(
        "archive-lab",
        aliases=["arc"],
        help="Archive utilities (list, extract, create, add, info)."
    )
    archive_subparsers = parser_archive.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # arc list
    parser_archive_list = archive_subparsers.add_parser("list", help="List contents.")
    parser_archive_list.add_argument("archive", help="Archive path.")

    # arc extract
    parser_archive_extract = archive_subparsers.add_parser("extract", help="Extract archive.")
    parser_archive_extract.add_argument("archive", help="Archive path.")
    parser_archive_extract.add_argument("dest", nargs="?", help="Destination directory.")

    # arc create
    parser_archive_create = archive_subparsers.add_parser("create", help="Create archive.")
    parser_archive_create.add_argument("archive", help="Archive path.")
    parser_archive_create.add_argument("files", nargs="+", help="Files to include.")

    # arc add
    parser_archive_add = archive_subparsers.add_parser("add", help="Add to archive.")
    parser_archive_add.add_argument("archive", help="Archive path.")
    parser_archive_add.add_argument("files", nargs="+", help="Files to add.")

    # arc info
    parser_archive_info = archive_subparsers.add_parser("info", help="Archive metadata.")
    parser_archive_info.add_argument("archive", help="Archive path.")

    # --- New 'uni-lab' command ---
    parser_uni = subparsers.add_parser(
        "uni-lab",
        aliases=["uni"],
        help="Unicode utilities (inspect, search, escape, unescape)."
    )
    uni_subparsers = parser_uni.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # uni-lab inspect
    parser_uni_inspect = uni_subparsers.add_parser("inspect", help="Inspect characters.")
    parser_uni_inspect.add_argument("--text", help="Input text.")

    # uni-lab search
    parser_uni_search = uni_subparsers.add_parser("search", help="Search characters by name.")
    parser_uni_search.add_argument("--query", "-q", required=True, help="Search query.")
    parser_uni_search.add_argument("--limit", "-l", type=int, default=50, help="Limit results.")

    # uni-lab escape
    parser_uni_escape = uni_subparsers.add_parser("escape", help="Escape non-ASCII chars.")
    parser_uni_escape.add_argument("--text", help="Input text.")

    # uni-lab unescape
    parser_uni_unescape = uni_subparsers.add_parser("unescape", help="Unescape \\u sequences.")
    parser_uni_unescape.add_argument("--text", help="Input text.")

    # --- New 'docs-lab' command ---
    parser_docs = subparsers.add_parser(
        "docs-lab",
        aliases=["docs"],
        help="Documentation Generator (generate, clean)."
    )
    docs_subparsers = parser_docs.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # docs-lab generate
    parser_docs_gen = docs_subparsers.add_parser("generate", help="Generate Markdown docs.")
    parser_docs_gen.add_argument("--source", "-s", help="Source directory (default: current).")
    parser_docs_gen.add_argument("--output", "-o", help="Output directory (default: docs/api).")

    # docs-lab clean
    parser_docs_clean = docs_subparsers.add_parser("clean", help="Clean generated docs.")
    parser_docs_clean.add_argument("--output", "-o", help="Output directory to clean.")

    # --- New 'qr-lab' command ---
    parser_qr = subparsers.add_parser(
        "qr-lab",
        aliases=["qr"],
        help="QR Code utilities (gen, wifi)."
    )
    qr_subparsers = parser_qr.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # qr-lab gen
    parser_qr_gen = qr_subparsers.add_parser("gen", help="Generate QR code.")
    parser_qr_gen.add_argument("text", help="Text to encode.")
    parser_qr_gen.add_argument("--output", "-o", help="Output image file (PNG/SVG).")
    parser_qr_gen.add_argument("--fill-color", default="black", help="Fill color (default: black).")
    parser_qr_gen.add_argument("--back-color", default="white", help="Background color (default: white).")

    # qr-lab wifi
    parser_qr_wifi = qr_subparsers.add_parser("wifi", help="Generate WiFi config QR code.")
    parser_qr_wifi.add_argument("--ssid", required=True, help="Network SSID.")
    parser_qr_wifi.add_argument("--password", "-p", help="Network password.")
    parser_qr_wifi.add_argument("--type", choices=["WPA", "WEP", "nopass"], default="WPA", help="Security type.")
    parser_qr_wifi.add_argument("--hidden", action="store_true", help="Hidden network.")
    parser_qr_wifi.add_argument("--output", "-o", help="Output image file (PNG/SVG).")

    # --- New 'http-lab' command ---
    parser_http = subparsers.add_parser(
        "http-lab",
        aliases=["http", "req"],
        help="HTTP Client (get, post, put, delete, etc)."
    )
    parser_http.add_argument("method", choices=["get", "post", "put", "delete", "patch", "head", "options"], type=str.lower, help="HTTP Method.")
    parser_http.add_argument("url", help="Target URL.")
    parser_http.add_argument("--header", "-H", action="append", help="HTTP Header (e.g. 'Content-Type: application/json').")
    parser_http.add_argument("--data", "-d", help="Request body (form data).")
    parser_http.add_argument("--json", "-j", help="Request body (JSON string).")
    parser_http.add_argument("--output", "-o", help="Save response body to file.")
    parser_http.add_argument("--follow", action="store_true", help="Follow redirects.")
    parser_http.add_argument("--no-verify", action="store_true", help="Disable SSL verification.")
    parser_http.add_argument("--timeout", type=float, default=10.0, help="Request timeout.")
    parser_http.add_argument("--proxy", help="Proxy URL.")
    parser_http.add_argument("--verbose", "-v", action="store_true", help="Show detailed request/response info.")

    # --- New 'proxy-lab' command ---
    parser_proxy = subparsers.add_parser(
        "proxy-lab",
        aliases=["proxy"],
        help="HTTP/HTTPS Proxy Server for debugging."
    )
    parser_proxy.add_argument("--port", "-p", type=int, default=8080, help="Port to listen on (default: 8080).")
    parser_proxy.add_argument("--host", default="127.0.0.1", help="Host interface (default: 127.0.0.1).")

    # --- New 'webhook-lab' command ---
    parser_webhook = subparsers.add_parser(
        "webhook-lab",
        aliases=["webhook", "hook"],
        help="Webhook Lab: Capture, inspect, and replay HTTP requests."
    )
    webhook_subparsers = parser_webhook.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # webhook-lab listen
    parser_wh_listen = webhook_subparsers.add_parser("listen", help="Start listening for webhooks.")
    parser_wh_listen.add_argument("--port", "-p", type=int, default=8000, help="Port to listen on (default: 8000).")
    parser_wh_listen.add_argument("--forward", "-f", help="Forward requests to this URL.")

    # webhook-lab list
    parser_wh_list = webhook_subparsers.add_parser("list", help="List captured webhooks.")
    parser_wh_list.add_argument("--limit", "-n", type=int, default=10, help="Number of requests to show.")

    # webhook-lab show
    parser_wh_show = webhook_subparsers.add_parser("show", help="Show details of a webhook.")
    parser_wh_show.add_argument("id", help="Request ID.")

    # webhook-lab replay
    parser_wh_replay = webhook_subparsers.add_parser("replay", help="Replay a captured webhook.")
    parser_wh_replay.add_argument("id", help="Request ID.")
    parser_wh_replay.add_argument("target", help="Target URL.")

    # --- New 'proc-lab' command ---
    parser_proc = subparsers.add_parser(
        "proc-lab",
        aliases=["proc"],
        help="Process Manager (start, list, run, check)."
    )
    parser_proc.add_argument("--file", "-f", help="Path to Procfile (default: Procfile).")

    proc_subparsers = parser_proc.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # proc start
    parser_proc_start = proc_subparsers.add_parser("start", help="Start all processes.")

    # proc list
    parser_proc_list = proc_subparsers.add_parser("list", help="List processes.")

    # proc run
    parser_proc_run = proc_subparsers.add_parser("run", help="Run a specific process.")
    parser_proc_run.add_argument("process", help="Name of the process to run.")

    # proc check
    parser_proc_check = proc_subparsers.add_parser("check", help="Validate Procfile.")

    # --- New 'geo-lab' command ---
    parser_geo = subparsers.add_parser(
        "geo-lab",
        aliases=["geo"],
        help="Geolocation utilities (locate, distance, map)."
    )
    geo_subparsers = parser_geo.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # geo-lab locate
    parser_geo_locate = geo_subparsers.add_parser("locate", help="Locate IP or Domain.")
    parser_geo_locate.add_argument("query", help="IP address or domain name.")

    # geo-lab distance
    parser_geo_dist = geo_subparsers.add_parser("distance", help="Calculate distance between two coordinates.")
    parser_geo_dist.add_argument("point1", help="Start point (lat,lon).")
    parser_geo_dist.add_argument("point2", help="End point (lat,lon).")

    # geo-lab map
    parser_geo_map = geo_subparsers.add_parser("map", help="Get Google Maps link.")
    parser_geo_map.add_argument("point", help="Coordinates (lat,lon).")

    # --- New 'struct-lab' command ---
    parser_struct = subparsers.add_parser(
        "struct-lab",
        aliases=["struct", "bin"],
        help="Binary structure utilities (hex, pack, unpack, calc)."
    )
    struct_subparsers = parser_struct.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # struct-lab hex
    parser_struct_hex = struct_subparsers.add_parser("hex", help="Hex dump of file.")
    parser_struct_hex.add_argument("file", help="Input file.")
    parser_struct_hex.add_argument("--offset", type=int, default=0, help="Start offset.")
    parser_struct_hex.add_argument("--length", type=int, help="Length to read.")

    # struct-lab calc
    parser_struct_calc = struct_subparsers.add_parser("calc", help="Calculate size of format.")
    parser_struct_calc.add_argument("format", help="Struct format string (e.g. '2i4s').")

    # struct-lab unpack
    parser_struct_unpack = struct_subparsers.add_parser("unpack", help="Unpack binary file.")
    parser_struct_unpack.add_argument("format", help="Struct format string.")
    parser_struct_unpack.add_argument("file", help="Input file.")
    parser_struct_unpack.add_argument("--offset", type=int, default=0, help="Start offset.")

    # struct-lab pack
    parser_struct_pack = struct_subparsers.add_parser("pack", help="Pack values into binary file.")
    parser_struct_pack.add_argument("format", help="Struct format string.")
    parser_struct_pack.add_argument("output", help="Output file.")
    parser_struct_pack.add_argument("values", nargs="+", help="Values to pack.")

    # --- New 'chart-lab' command ---
    parser_chart = subparsers.add_parser(
        "chart-lab",
        aliases=["chart"],
        help="Chart utilities (bar, scatter, line)."
    )
    parser_chart.add_argument("--file", help="Input file (CSV/JSON). Default: stdin.")
    parser_chart.add_argument("--width", type=int, help="Chart width (default: terminal width).")
    parser_chart.add_argument("--height", type=int, help="Chart height (default: terminal height).")

    chart_subparsers = parser_chart.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # chart-lab bar
    parser_chart_bar = chart_subparsers.add_parser("bar", help="Bar chart.")
    parser_chart_bar.add_argument("--x", required=True, help="Column for X-axis (labels).")
    parser_chart_bar.add_argument("--y", required=True, help="Column for Y-axis (values).")

    # chart-lab scatter
    parser_chart_scatter = chart_subparsers.add_parser("scatter", help="Scatter plot.")
    parser_chart_scatter.add_argument("--x", required=True, help="Column for X-axis (numeric).")
    parser_chart_scatter.add_argument("--y", required=True, help="Column for Y-axis (numeric).")

    # chart-lab line
    parser_chart_line = chart_subparsers.add_parser("line", help="Line chart.")
    parser_chart_line.add_argument("--x", required=True, help="Column for X-axis.")
    parser_chart_line.add_argument("--y", required=True, help="Column for Y-axis.")

    # --- New 'enc-lab' command ---
    parser_enc = subparsers.add_parser(
        "enc-lab",
        aliases=["enc", "encode"],
        help="Encoding utilities (base64, url, html, hex, rot13)."
    )
    enc_subparsers = parser_enc.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # Common args for enc-lab
    def add_enc_args(p):
        p.add_argument("text", nargs="?", help="Input text (optional, reads from stdin if omitted).")
        p.add_argument("--decode", "-d", action="store_true", help="Decode input.")

    # enc-lab base64
    parser_enc_b64 = enc_subparsers.add_parser("base64", help="Base64 encode/decode.")
    add_enc_args(parser_enc_b64)

    # enc-lab url
    parser_enc_url = enc_subparsers.add_parser("url", help="URL encode/decode.")
    add_enc_args(parser_enc_url)

    # enc-lab html
    parser_enc_html = enc_subparsers.add_parser("html", help="HTML entity encode/decode.")
    add_enc_args(parser_enc_html)

    # enc-lab hex
    parser_enc_hex = enc_subparsers.add_parser("hex", help="Hex encode/decode.")
    add_enc_args(parser_enc_hex)

    # enc-lab rot13
    parser_enc_rot13 = enc_subparsers.add_parser("rot13", help="ROT13 transform.")
    parser_enc_rot13.add_argument("text", nargs="?", help="Input text.")
    # rot13 doesn't need --decode really, but we'll accept it to not break shared logic if passed
    parser_enc_rot13.add_argument("--decode", "-d", action="store_true", help="Ignored for ROT13.")

    # --- New 'rss-lab' command ---
    parser_rss = subparsers.add_parser(
        "rss-lab",
        aliases=["rss"],
        help="RSS/Atom Feed utilities (read, inspect)."
    )
    rss_subparsers = parser_rss.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # rss-lab read
    parser_rss_read = rss_subparsers.add_parser("read", help="Read feed entries.")
    parser_rss_read.add_argument("url", help="Feed URL.")
    parser_rss_read.add_argument("--limit", "-l", type=int, default=10, help="Number of entries to show.")

    # rss-lab inspect
    parser_rss_inspect = rss_subparsers.add_parser("inspect", help="Inspect raw feed structure.")
    parser_rss_inspect.add_argument("url", help="Feed URL.")

    # --- New 'fs-lab' command ---
    parser_fs = subparsers.add_parser(
        "fs-lab",
        aliases=["fs", "files"],
        help="FileSystem utilities (info, find, dedup, clean, shred, usage)."
    )
    fs_subparsers = parser_fs.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # fs-lab info
    parser_fs_info = fs_subparsers.add_parser("info", help="Get file metadata.")
    parser_fs_info.add_argument("path", help="File or directory path.")

    # fs-lab find
    parser_fs_find = fs_subparsers.add_parser("find", help="Find files.")
    parser_fs_find.add_argument("--root", "-r", default=".", help="Root directory.")
    parser_fs_find.add_argument("--name", help="Name pattern (glob).")
    parser_fs_find.add_argument("--size", help="Size constraint (e.g. '>10MB', '<5k').")
    parser_fs_find.add_argument("--mtime", help="Modified time constraint (e.g. '>1d', '<2h').")
    parser_fs_find.add_argument("--type", choices=['f', 'd'], help="File type (f=file, d=dir).")
    parser_fs_find.add_argument("--content", help="Regex content search.")

    # fs-lab dedup
    parser_fs_dedup = fs_subparsers.add_parser("dedup", help="Find duplicate files.")
    parser_fs_dedup.add_argument("--root", "-r", default=".", help="Root directory.")
    parser_fs_dedup.add_argument("--delete", action="store_true", help="Delete duplicates.")
    parser_fs_dedup.add_argument("--force", action="store_true", help="Actually delete (disable dry-run).")

    # fs-lab clean
    parser_fs_clean = fs_subparsers.add_parser("clean", help="Clean temp files/empty dirs.")
    parser_fs_clean.add_argument("--root", "-r", default=".", help="Root directory.")
    parser_fs_clean.add_argument("--force", action="store_true", help="Actually delete (disable dry-run).")

    # fs-lab shred
    parser_fs_shred = fs_subparsers.add_parser("shred", help="Securely delete file.")
    parser_fs_shred.add_argument("path", help="File path.")
    parser_fs_shred.add_argument("--passes", type=int, default=3, help="Number of overwrite passes.")
    parser_fs_shred.add_argument("--force", action="store_true", help="Skip confirmation.")

    # fs-lab usage
    parser_fs_usage = fs_subparsers.add_parser("usage", help="Show disk usage tree.")
    parser_fs_usage.add_argument("--root", "-r", default=".", help="Root directory.")
    parser_fs_usage.add_argument("--depth", "-d", type=int, default=2, help="Depth of tree.")

    # --- New 'ws-lab' command ---
    parser_ws = subparsers.add_parser(
        "ws-lab",
        aliases=["ws"],
        help="WebSocket Client (connect, send, listen)."
    )
    parser_ws.add_argument("url", nargs="?", help="WebSocket URL (required for client mode).")
    parser_ws.add_argument("--header", "-H", action="append", help="Custom Header (e.g. 'Authorization: Bearer ...').")
    parser_ws.add_argument("--message", "-m", help="Initial message to send.")
    parser_ws.add_argument("--interactive", "-i", action="store_true", help="Interactive mode (read from stdin).")
    parser_ws.add_argument("--listen", "-l", action="store_true", help="Listen mode (keep connection open).")
    parser_ws.add_argument("--server", "-s", action="store_true", help="Run as a WebSocket server.")
    parser_ws.add_argument("--port", "-p", type=int, default=8765, help="Port to listen on (server mode).")

    # --- New 'hash-lab' command ---
    parser_hash = subparsers.add_parser(
        "hash-lab",
        aliases=["hash"],
        help="Hash utilities (string, file, dir, compare, verify)."
    )
    hash_subparsers = parser_hash.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # hash-lab string
    parser_hash_str = hash_subparsers.add_parser("string", help="Hash a string.")
    parser_hash_str.add_argument("text", nargs="?", help="Input text.")
    parser_hash_str.add_argument("--algo", default="sha256", help="Algorithm (default: sha256).")

    # hash-lab file
    parser_hash_file = hash_subparsers.add_parser("file", help="Hash a file.")
    parser_hash_file.add_argument("path", help="File path.")
    parser_hash_file.add_argument("--algo", default="sha256", help="Algorithm (default: sha256).")

    # hash-lab dir
    parser_hash_dir = hash_subparsers.add_parser("dir", help="Hash a directory.")
    parser_hash_dir.add_argument("path", help="Directory path.")
    parser_hash_dir.add_argument("--algo", default="sha256", help="Algorithm (default: sha256).")
    parser_hash_dir.add_argument("--recursive", "-r", action="store_true", help="Recursive hash.")

    # hash-lab compare
    parser_hash_cmp = hash_subparsers.add_parser("compare", help="Compare two files.")
    parser_hash_cmp.add_argument("file1", help="First file.")
    parser_hash_cmp.add_argument("file2", help="Second file.")
    parser_hash_cmp.add_argument("--algo", default="sha256", help="Algorithm (default: sha256).")

    # hash-lab verify
    parser_hash_ver = hash_subparsers.add_parser("verify", help="Verify checksums.")
    parser_hash_ver.add_argument("checksum_file", help="Checksum file path.")
    parser_hash_ver.add_argument("--algo", default="sha256", help="Algorithm (default: sha256).")
    parser_hash_ver.add_argument("--root", help="Root directory for files (default: checksum file dir).")

    # --- New 'random-lab' command ---
    parser_random = subparsers.add_parser(
        "random-lab",
        aliases=["rand", "random"],
        help="Random data generator (int, float, string, choice, pick, shuffle, uuid, coin, dice)."
    )
    random_subparsers = parser_random.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # random-lab int
    parser_random_int = random_subparsers.add_parser("int", help="Random integers.")
    parser_random_int.add_argument("min", type=int, help="Minimum value.")
    parser_random_int.add_argument("max", type=int, help="Maximum value.")
    parser_random_int.add_argument("--count", "-c", type=int, default=1, help="Number of items.")

    # random-lab float
    parser_random_float = random_subparsers.add_parser("float", help="Random floats.")
    parser_random_float.add_argument("min", type=float, help="Minimum value.")
    parser_random_float.add_argument("max", type=float, help="Maximum value.")
    parser_random_float.add_argument("--count", "-c", type=int, default=1, help="Number of items.")

    # random-lab string
    parser_random_str = random_subparsers.add_parser("string", help="Random strings.")
    parser_random_str.add_argument("length", type=int, help="String length.")
    parser_random_str.add_argument("charset", nargs="?", default="alnum", help="Charset (alpha, numeric, alnum, hex, special, all) or custom string.")
    parser_random_str.add_argument("--count", "-c", type=int, default=1, help="Number of items.")

    # random-lab choice
    parser_random_choice = random_subparsers.add_parser("choice", help="Random choice from list.")
    parser_random_choice.add_argument("items", nargs="+", help="Items to choose from.")
    parser_random_choice.add_argument("--count", "-c", type=int, default=1, help="Number of items.")

    # random-lab pick
    parser_random_pick = random_subparsers.add_parser("pick", help="Pick random lines from file.")
    parser_random_pick.add_argument("--file", required=True, help="Input file.")
    parser_random_pick.add_argument("--count", "-c", type=int, default=1, help="Number of lines.")
    parser_random_pick.add_argument("--unique", "-u", action="store_true", help="Pick unique lines (no replacement).")

    # random-lab shuffle
    parser_random_shuffle = random_subparsers.add_parser("shuffle", help="Shuffle lines from file.")
    parser_random_shuffle.add_argument("--file", help="Input file (default: stdin).")

    # random-lab uuid
    parser_random_uuid = random_subparsers.add_parser("uuid", help="Generate UUIDs.")
    parser_random_uuid.add_argument("--version", "-v", type=int, default=4, choices=[1, 4], help="UUID version.")
    parser_random_uuid.add_argument("--count", "-c", type=int, default=1, help="Number of items.")

    # random-lab coin
    parser_random_coin = random_subparsers.add_parser("coin", help="Flip a coin.")
    parser_random_coin.add_argument("--count", "-c", type=int, default=1, help="Number of flips.")

    # random-lab dice
    parser_random_dice = random_subparsers.add_parser("dice", help="Roll a dice.")
    parser_random_dice.add_argument("--sides", "-s", type=int, default=6, help="Number of sides.")
    parser_random_dice.add_argument("--count", "-c", type=int, default=1, help="Number of rolls.")

    # --- New 'browser-lab' command ---
    parser_browser = subparsers.add_parser(
        "browser-lab",
        aliases=["browser", "web"],
        help="Browser automation utilities (screenshot, pdf, text, html, evaluate, inspect)."
    )
    browser_subparsers = parser_browser.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # browser-lab screenshot
    parser_browser_screenshot = browser_subparsers.add_parser("screenshot", help="Take a screenshot.")
    parser_browser_screenshot.add_argument("url", help="URL to visit.")
    parser_browser_screenshot.add_argument("output", help="Output file path (.png).")
    parser_browser_screenshot.add_argument("--viewport", "-v", action="store_true", help="Capture viewport only (default: full page).")

    # browser-lab pdf
    parser_browser_pdf = browser_subparsers.add_parser("pdf", help="Save page as PDF.")
    parser_browser_pdf.add_argument("url", help="URL to visit.")
    parser_browser_pdf.add_argument("output", help="Output file path (.pdf).")

    # browser-lab text
    parser_browser_text = browser_subparsers.add_parser("text", help="Extract text content.")
    parser_browser_text.add_argument("url", help="URL to visit.")
    parser_browser_text.add_argument("--output", "-o", help="Output file path (optional).")

    # browser-lab html
    parser_browser_html = browser_subparsers.add_parser("html", help="Extract HTML content.")
    parser_browser_html.add_argument("url", help="URL to visit.")
    parser_browser_html.add_argument("--output", "-o", help="Output file path (optional).")

    # browser-lab evaluate
    parser_browser_eval = browser_subparsers.add_parser("evaluate", help="Evaluate JavaScript.")
    parser_browser_eval.add_argument("url", help="URL to visit.")
    parser_browser_eval.add_argument("script", help="JavaScript to execute.")

    # browser-lab inspect
    parser_browser_inspect = browser_subparsers.add_parser("inspect", help="Inspect page metadata.")
    parser_browser_inspect.add_argument("url", help="URL to visit.")

    # --- New 'npm-lab' command ---
    parser_npm = subparsers.add_parser(
        "npm-lab",
        aliases=["npm"],
        help="NPM Registry utilities (info, versions, deps, tags, search)."
    )
    npm_subparsers = parser_npm.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # npm-lab info
    parser_npm_info = npm_subparsers.add_parser("info", help="Get package metadata.")
    parser_npm_info.add_argument("package", help="Package name.")

    # npm-lab versions
    parser_npm_versions = npm_subparsers.add_parser("versions", help="List versions.")
    parser_npm_versions.add_argument("package", help="Package name.")
    parser_npm_versions.add_argument("--limit", type=int, default=15, help="Limit number of versions.")

    # npm-lab deps
    parser_npm_deps = npm_subparsers.add_parser("deps", help="List dependencies.")
    parser_npm_deps.add_argument("package", help="Package name.")
    parser_npm_deps.add_argument("--version", help="Specific version (optional).")

    # npm-lab tags
    parser_npm_tags = npm_subparsers.add_parser("tags", help="Show dist-tags.")
    parser_npm_tags.add_argument("package", help="Package name.")

    # npm-lab search
    parser_npm_search = npm_subparsers.add_parser("search", help="Search for packages.")
    parser_npm_search.add_argument("query", help="Search query.")
    parser_npm_search.add_argument("--limit", type=int, default=10, help="Limit results.")

    # --- New 'pypi-lab' command ---
    parser_pypi = subparsers.add_parser(
        "pypi-lab",
        aliases=["pypi"],
        help="PyPI Registry utilities (info, releases, deps, files, download)."
    )
    pypi_subparsers = parser_pypi.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # pypi-lab info
    parser_pypi_info = pypi_subparsers.add_parser("info", help="Get package metadata.")
    parser_pypi_info.add_argument("package", help="Package name.")

    # pypi-lab releases
    parser_pypi_releases = pypi_subparsers.add_parser("releases", help="List releases.")
    parser_pypi_releases.add_argument("package", help="Package name.")

    # pypi-lab deps
    parser_pypi_deps = pypi_subparsers.add_parser("deps", help="List dependencies.")
    parser_pypi_deps.add_argument("package", help="Package name.")
    parser_pypi_deps.add_argument("--version", help="Specific version (optional).")

    # pypi-lab files
    parser_pypi_files = pypi_subparsers.add_parser("files", help="List files.")
    parser_pypi_files.add_argument("package", help="Package name.")
    parser_pypi_files.add_argument("--version", help="Specific version (optional).")

    # pypi-lab download
    parser_pypi_download = pypi_subparsers.add_parser("download", help="Download package files.")
    parser_pypi_download.add_argument("package", help="Package name.")
    parser_pypi_download.add_argument("--version", help="Specific version (optional).")
    parser_pypi_download.add_argument("--dest", help="Destination directory (default: current).")

    # --- New 'docker-lab' command ---
    parser_docker = subparsers.add_parser(
        "docker-lab",
        aliases=["docker", "container"],
        help="Docker utilities (ps, images, start, stop, restart, rm, rmi, prune, logs, inspect, stats)."
    )
    docker_subparsers = parser_docker.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # docker-lab ps
    parser_docker_ps = docker_subparsers.add_parser("ps", aliases=["list"], help="List containers.")

    # docker-lab images
    parser_docker_images = docker_subparsers.add_parser("images", help="List images.")

    # docker-lab start
    parser_docker_start = docker_subparsers.add_parser("start", help="Start a container.")
    parser_docker_start.add_argument("container", help="Container ID or name.")

    # docker-lab stop
    parser_docker_stop = docker_subparsers.add_parser("stop", help="Stop a container.")
    parser_docker_stop.add_argument("container", help="Container ID or name.")

    # docker-lab restart
    parser_docker_restart = docker_subparsers.add_parser("restart", help="Restart a container.")
    parser_docker_restart.add_argument("container", help="Container ID or name.")

    # docker-lab rm
    parser_docker_rm = docker_subparsers.add_parser("rm", help="Remove a container.")
    parser_docker_rm.add_argument("container", help="Container ID or name.")
    parser_docker_rm.add_argument("--force", "-f", action="store_true", help="Force removal.")

    # docker-lab rmi
    parser_docker_rmi = docker_subparsers.add_parser("rmi", help="Remove an image.")
    parser_docker_rmi.add_argument("image", help="Image ID or name.")
    parser_docker_rmi.add_argument("--force", "-f", action="store_true", help="Force removal.")

    # docker-lab prune
    parser_docker_prune = docker_subparsers.add_parser("prune", help="Prune stopped containers/unused images.")
    parser_docker_prune.add_argument("--what", choices=["containers", "images", "all"], default="all", help="What to prune.")
    parser_docker_prune.add_argument("--force", "-f", action="store_true", help="Skip confirmation.")

    # docker-lab logs
    parser_docker_logs = docker_subparsers.add_parser("logs", help="Get container logs.")
    parser_docker_logs.add_argument("container", help="Container ID or name.")
    parser_docker_logs.add_argument("--tail", type=int, default=100, help="Number of lines.")

    # docker-lab inspect
    parser_docker_inspect = docker_subparsers.add_parser("inspect", help="Inspect container.")
    parser_docker_inspect.add_argument("container", help="Container ID or name.")

    # docker-lab stats
    parser_docker_stats = docker_subparsers.add_parser("stats", help="Get container stats.")
    parser_docker_stats.add_argument("container", help="Container ID or name.")

    # --- New 'compose-lab' command ---
    parser_compose = subparsers.add_parser(
        "compose-lab",
        aliases=["compose"],
        help="Docker Compose utilities (up, down, ps, logs, stop, start, restart, build, pull, exec)."
    )
    compose_subparsers = parser_compose.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # compose-lab up
    parser_compose_up = compose_subparsers.add_parser("up", help="Start services.")
    parser_compose_up.add_argument("-d", "--detach", action="store_true", help="Detached mode.")
    parser_compose_up.add_argument("--build", action="store_true", help="Build images before starting.")
    parser_compose_up.add_argument("services", nargs="*", help="Services to start.")

    # compose-lab down
    parser_compose_down = compose_subparsers.add_parser("down", help="Stop and remove resources.")
    parser_compose_down.add_argument("-v", "--volumes", action="store_true", help="Remove volumes.")
    parser_compose_down.add_argument("--remove-orphans", action="store_true", help="Remove orphans.")

    # compose-lab ps
    parser_compose_ps = compose_subparsers.add_parser("ps", aliases=["list"], help="List containers.")
    parser_compose_ps.add_argument("-a", "--all", action="store_true", help="Show all.")

    # compose-lab logs
    parser_compose_logs = compose_subparsers.add_parser("logs", help="View logs.")
    parser_compose_logs.add_argument("services", nargs="*", help="Services.")
    parser_compose_logs.add_argument("-f", "--follow", action="store_true", help="Follow logs.")
    parser_compose_logs.add_argument("--tail", type=int, default=100, help="Number of lines.")

    # compose-lab stop
    parser_compose_stop = compose_subparsers.add_parser("stop", help="Stop services.")
    parser_compose_stop.add_argument("services", nargs="*", help="Services.")

    # compose-lab start
    parser_compose_start = compose_subparsers.add_parser("start", help="Start services.")
    parser_compose_start.add_argument("services", nargs="*", help="Services.")

    # compose-lab restart
    parser_compose_restart = compose_subparsers.add_parser("restart", help="Restart services.")
    parser_compose_restart.add_argument("services", nargs="*", help="Services.")

    # compose-lab build
    parser_compose_build = compose_subparsers.add_parser("build", help="Build services.")
    parser_compose_build.add_argument("services", nargs="*", help="Services.")
    parser_compose_build.add_argument("--no-cache", action="store_true", help="Do not use cache.")

    # compose-lab pull
    parser_compose_pull = compose_subparsers.add_parser("pull", help="Pull images.")
    parser_compose_pull.add_argument("services", nargs="*", help="Services.")

    # compose-lab exec
    parser_compose_exec = compose_subparsers.add_parser("exec", help="Execute command.")
    parser_compose_exec.add_argument("service", help="Service name.")
    parser_compose_exec.add_argument("command_args", nargs=argparse.REMAINDER, help="Command to execute.")

    # --- New 'k8s-lab' command ---
    parser_k8s = subparsers.add_parser(
        "k8s-lab",
        aliases=["k8s", "kube"],
        help="Kubernetes utilities (pods, ns, deploy, svc, ctx, logs, describe, apply, delete)."
    )
    k8s_subparsers = parser_k8s.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # k8s-lab pods
    parser_k8s_pods = k8s_subparsers.add_parser("pods", help="List pods.")
    parser_k8s_pods.add_argument("--namespace", "-n", help="Namespace (default: all namespaces if not specified or current).")

    # k8s-lab ns
    parser_k8s_ns = k8s_subparsers.add_parser("ns", help="List namespaces.")

    # k8s-lab deploy
    parser_k8s_deploy = k8s_subparsers.add_parser("deploy", help="List deployments.")
    parser_k8s_deploy.add_argument("--namespace", "-n", help="Namespace.")

    # k8s-lab svc
    parser_k8s_svc = k8s_subparsers.add_parser("svc", help="List services.")
    parser_k8s_svc.add_argument("--namespace", "-n", help="Namespace.")

    # k8s-lab ctx
    parser_k8s_ctx = k8s_subparsers.add_parser("ctx", help="List or switch context.")
    parser_k8s_ctx.add_argument("use_context", nargs="?", help="Switch to this context.")

    # k8s-lab logs
    parser_k8s_logs = k8s_subparsers.add_parser("logs", help="Get pod logs.")
    parser_k8s_logs.add_argument("pod", help="Pod name.")
    parser_k8s_logs.add_argument("--namespace", "-n", help="Namespace.")
    parser_k8s_logs.add_argument("--tail", type=int, default=100, help="Number of lines.")

    # k8s-lab describe
    parser_k8s_describe = k8s_subparsers.add_parser("describe", help="Describe resource.")
    parser_k8s_describe.add_argument("resource_type", help="Resource type (e.g., pod, deploy).")
    parser_k8s_describe.add_argument("name", help="Resource name.")
    parser_k8s_describe.add_argument("--namespace", "-n", help="Namespace.")

    # k8s-lab apply
    parser_k8s_apply = k8s_subparsers.add_parser("apply", help="Apply configuration.")
    parser_k8s_apply.add_argument("file", help="File path.")

    # k8s-lab delete
    parser_k8s_delete = k8s_subparsers.add_parser("delete", help="Delete resource.")
    parser_k8s_delete.add_argument("resource_type", help="Resource type.")
    parser_k8s_delete.add_argument("name", help="Resource name.")
    parser_k8s_delete.add_argument("--namespace", "-n", help="Namespace.")

    # --- New 'diff-lab' command ---
    parser_diff_lab = subparsers.add_parser(
        "diff-lab",
        help="Smart comparison for various file formats (JSON, YAML, Image, Text)."
    )
    parser_diff_lab.add_argument("file1", help="First file.")
    parser_diff_lab.add_argument("file2", help="Second file.")
    parser_diff_lab.add_argument("--type", choices=["json", "yaml", "image", "text"], help="Force comparison type.")
    parser_diff_lab.add_argument("--output", help="Output path (for image diffs).")

    # --- New 'redis-lab' command ---
    parser_redis = subparsers.add_parser(
        "redis-lab",
        aliases=["redis", "cache"],
        help="Redis utilities (connect, get, set, del, keys, flush, info)."
    )
    parser_redis.add_argument("--url", help="Redis URL (default: redis://localhost:6379/0)")
    redis_subparsers = parser_redis.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # redis-lab connect
    redis_subparsers.add_parser("connect", help="Test connection.")

    # redis-lab get
    parser_redis_get = redis_subparsers.add_parser("get", help="Get a value.")
    parser_redis_get.add_argument("key", help="Key to get.")

    # redis-lab set
    parser_redis_set = redis_subparsers.add_parser("set", help="Set a value.")
    parser_redis_set.add_argument("key", help="Key to set.")
    parser_redis_set.add_argument("value", help="Value to set.")
    parser_redis_set.add_argument("--ex", type=int, help="Expiry in seconds.")

    # redis-lab del
    parser_redis_del = redis_subparsers.add_parser("del", help="Delete a key.")
    parser_redis_del.add_argument("key", help="Key to delete.")

    # redis-lab keys
    parser_redis_keys = redis_subparsers.add_parser("keys", help="List keys.")
    parser_redis_keys.add_argument("pattern", default="*", nargs="?", help="Pattern (default: *).")

    # redis-lab flush
    parser_redis_flush = redis_subparsers.add_parser("flush", help="Flush database.")
    parser_redis_flush.add_argument("--force", "-f", action="store_true", help="Skip confirmation.")

    # redis-lab info
    redis_subparsers.add_parser("info", help="Get server info.")

    # --- New 'kafka-lab' command ---
    parser_kafka = subparsers.add_parser(
        "kafka-lab",
        aliases=["kafka"],
        help="Kafka utilities (list, consume, produce, create, delete, describe)."
    )
    parser_kafka.add_argument("--bootstrap", default="localhost:9092", help="Bootstrap servers (default: localhost:9092).")
    kafka_subparsers = parser_kafka.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # kafka-lab list
    kafka_subparsers.add_parser("list", help="List topics.")

    # kafka-lab describe
    parser_kafka_describe = kafka_subparsers.add_parser("describe", help="Describe a topic.")
    parser_kafka_describe.add_argument("topic", help="Topic name.")

    # kafka-lab create
    parser_kafka_create = kafka_subparsers.add_parser("create", help="Create a topic.")
    parser_kafka_create.add_argument("topic", help="Topic name.")
    parser_kafka_create.add_argument("--partitions", type=int, default=1, help="Number of partitions.")
    parser_kafka_create.add_argument("--replication", type=int, default=1, help="Replication factor.")

    # kafka-lab delete
    parser_kafka_delete = kafka_subparsers.add_parser("delete", help="Delete a topic.")
    parser_kafka_delete.add_argument("topic", help="Topic name.")

    # kafka-lab produce
    parser_kafka_produce = kafka_subparsers.add_parser("produce", help="Produce a message.")
    parser_kafka_produce.add_argument("topic", help="Topic name.")
    parser_kafka_produce.add_argument("value", nargs="?", help="Message value (optional, reads from stdin if missing).")
    parser_kafka_produce.add_argument("--key", help="Message key.")

    # kafka-lab consume
    parser_kafka_consume = kafka_subparsers.add_parser("consume", help="Consume messages.")
    parser_kafka_consume.add_argument("topic", help="Topic name.")
    parser_kafka_consume.add_argument("--group", help="Consumer group ID.")
    parser_kafka_consume.add_argument("--from-beginning", action="store_true", help="Start from earliest offset.")
    parser_kafka_consume.add_argument("--limit", type=int, default=0, help="Max messages to consume.")
    parser_kafka_consume.add_argument("--follow", "-f", action="store_true", help="Keep consuming (follow).")

    # --- New 'github-lab' command ---
    parser_github = subparsers.add_parser(
        "github-lab",
        aliases=["github", "gh"],
        help="GitHub utilities (user, repo, search, gists, tree, raw)."
    )
    github_subparsers = parser_github.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # github-lab user
    parser_gh_user = github_subparsers.add_parser("user", help="Get user info.")
    parser_gh_user.add_argument("username", help="GitHub username.")

    # github-lab repo
    parser_gh_repo = github_subparsers.add_parser("repo", help="Get repo info.")
    parser_gh_repo.add_argument("repo", help="Owner/Repo (e.g. google/guava).")

    # github-lab search
    parser_gh_search = github_subparsers.add_parser("search", help="Search repositories.")
    parser_gh_search.add_argument("query", help="Search query.")
    parser_gh_search.add_argument("--limit", type=int, default=10, help="Max results.")

    # github-lab gists
    parser_gh_gists = github_subparsers.add_parser("gists", help="List user gists.")
    parser_gh_gists.add_argument("username", help="GitHub username.")
    parser_gh_gists.add_argument("--limit", type=int, default=10, help="Max results.")

    # github-lab tree
    parser_gh_tree = github_subparsers.add_parser("tree", help="View file tree.")
    parser_gh_tree.add_argument("repo", help="Owner/Repo.")
    parser_gh_tree.add_argument("path", nargs="?", default="", help="Path inside repo.")

    # github-lab raw
    parser_gh_raw = github_subparsers.add_parser("raw", help="Get raw file content.")
    parser_gh_raw.add_argument("repo", help="Owner/Repo.")
    parser_gh_raw.add_argument("path", help="Path to file.")

    # --- New 'email-lab' command ---
    parser_email = subparsers.add_parser(
        "email-lab",
        aliases=["email", "mail", "smtp"],
        help="Email utilities (server, send, list, show, clear)."
    )
    email_subparsers = parser_email.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # email-lab server
    parser_email_server = email_subparsers.add_parser("server", aliases=["serve"], help="Start SMTP server.")
    parser_email_server.add_argument("--port", type=int, default=1025, help="Port to listen on (default: 1025).")

    # email-lab send
    parser_email_send = email_subparsers.add_parser("send", help="Send a test email.")
    parser_email_send.add_argument("--to", required=True, nargs="+", help="Recipient(s).")
    parser_email_send.add_argument("--subject", required=True, help="Subject.")
    parser_email_send.add_argument("--body", required=True, help="Body content.")
    parser_email_send.add_argument("--from", dest="sender", default="test@example.com", help="Sender address.")
    parser_email_send.add_argument("--host", default="127.0.0.1", help="SMTP Host (default: 127.0.0.1).")
    parser_email_send.add_argument("--port", type=int, default=1025, help="SMTP Port (default: 1025).")

    # email-lab list
    parser_email_list = email_subparsers.add_parser("list", help="List captured emails.")
    parser_email_list.add_argument("--limit", type=int, default=10, help="Number of emails to show.")

    # email-lab show
    parser_email_show = email_subparsers.add_parser("show", help="Show email details.")
    parser_email_show.add_argument("id", help="Email ID.")

    # email-lab clear
    email_subparsers.add_parser("clear", help="Clear email history.")

    # --- New 'sock-lab' command ---
    parser_sock = subparsers.add_parser(
        "sock-lab",
        aliases=["sock", "nc", "netcat"],
        help="Raw socket tool (client/server)."
    )
    sock_subparsers = parser_sock.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # sock-lab connect
    parser_sock_connect = sock_subparsers.add_parser("connect", help="Connect to a server.")
    parser_sock_connect.add_argument("host", help="Host to connect to.")
    parser_sock_connect.add_argument("port", type=int, help="Port to connect to.")

    # sock-lab listen
    parser_sock_listen = sock_subparsers.add_parser("listen", help="Listen for connections.")
    parser_sock_listen.add_argument("port", type=int, help="Port to listen on.")
    parser_sock_listen.add_argument("--host", default="0.0.0.0", help="Interface to bind (default: 0.0.0.0).")  # nosec

    # --- New 'ssh-lab' command ---
    parser_ssh = subparsers.add_parser(
        "ssh-lab",
        aliases=["ssh"],
        help="SSH utilities (keygen, list, fingerprint, config)."
    )
    ssh_subparsers = parser_ssh.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # ssh-lab list
    ssh_subparsers.add_parser("list", help="List SSH keys.")

    # ssh-lab keygen
    parser_ssh_keygen = ssh_subparsers.add_parser("keygen", help="Generate a new SSH key.")
    parser_ssh_keygen.add_argument("filename", help="Filename for the key (relative to ~/.ssh).")
    parser_ssh_keygen.add_argument("--type", "-t", default="ed25519", help="Key type (default: ed25519).")
    parser_ssh_keygen.add_argument("--bits", "-b", type=int, default=4096, help="Bits (for RSA).")
    parser_ssh_keygen.add_argument("--comment", "-C", default="", help="Key comment.")

    # ssh-lab fingerprint
    parser_ssh_fingerprint = ssh_subparsers.add_parser("fingerprint", help="Get key fingerprint.")
    parser_ssh_fingerprint.add_argument("filename", help="Filename of the key.")

    # ssh-lab config
    parser_ssh_config = ssh_subparsers.add_parser("config", help="Manage SSH config.")
    ssh_config_subparsers = parser_ssh_config.add_subparsers(
        dest="sub_action",
        required=True,
        help="Config action."
    )
    # ssh-lab config list
    ssh_config_subparsers.add_parser("list", help="List defined hosts.")
    # ssh-lab config add
    parser_ssh_config_add = ssh_config_subparsers.add_parser("add", help="Add a new host.")
    parser_ssh_config_add.add_argument("--host", required=True, help="Host alias.")
    parser_ssh_config_add.add_argument("--hostname", required=True, help="Real hostname/IP.")
    parser_ssh_config_add.add_argument("--user", required=True, help="Username.")
    parser_ssh_config_add.add_argument("--identity", help="Identity file path.")

    # --- New 'tmux-lab' command ---
    parser_tmux = subparsers.add_parser(
        "tmux-lab",
        aliases=["tmux"],
        help="Tmux utilities (list, new, kill, attach, send, capture, windows, window)."
    )
    tmux_subparsers = parser_tmux.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # tmux-lab list
    tmux_subparsers.add_parser("list", help="List active sessions.")

    # tmux-lab new
    parser_tmux_new = tmux_subparsers.add_parser("new", help="Create a new session.")
    parser_tmux_new.add_argument("name", help="Session name.")
    parser_tmux_new.add_argument("command_str", nargs="?", help="Command to run.")

    # tmux-lab kill
    parser_tmux_kill = tmux_subparsers.add_parser("kill", help="Kill a session.")
    parser_tmux_kill.add_argument("target", help="Target session.")

    # tmux-lab attach
    parser_tmux_attach = tmux_subparsers.add_parser("attach", help="Attach to a session.")
    parser_tmux_attach.add_argument("target", help="Target session.")

    # tmux-lab send
    parser_tmux_send = tmux_subparsers.add_parser("send", help="Send keys to a session/pane.")
    parser_tmux_send.add_argument("target", help="Target session/pane.")
    parser_tmux_send.add_argument("keys", help="Keys to send.")

    # tmux-lab capture
    parser_tmux_capture = tmux_subparsers.add_parser("capture", help="Capture pane output.")
    parser_tmux_capture.add_argument("target", help="Target session/pane.")
    parser_tmux_capture.add_argument("--lines", type=int, help="Number of lines to capture.")

    # tmux-lab windows
    parser_tmux_windows = tmux_subparsers.add_parser("windows", help="List windows in a session.")
    parser_tmux_windows.add_argument("target", help="Target session.")

    # tmux-lab window
    parser_tmux_window = tmux_subparsers.add_parser("window", help="Create a new window.")
    parser_tmux_window.add_argument("target", help="Target session.")
    parser_tmux_window.add_argument("--name", "-n", help="Window name.")
    parser_tmux_window.add_argument("command_str", nargs="?", help="Command to run.")

    # --- New 'terraform-lab' command ---
    parser_tf = subparsers.add_parser(
        "terraform-lab",
        aliases=["tf", "terraform"],
        help="Terraform utilities (init, plan, apply, destroy, validate, fmt, output, show)."
    )
    tf_subparsers = parser_tf.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # tf init
    parser_tf_init = tf_subparsers.add_parser("init", help="Initialize configuration.")
    parser_tf_init.add_argument("--upgrade", action="store_true", help="Upgrade modules/plugins.")

    # tf plan
    parser_tf_plan = tf_subparsers.add_parser("plan", help="Generate execution plan.")
    parser_tf_plan.add_argument("--out", help="Output path for the plan file.")

    # tf apply
    parser_tf_apply = tf_subparsers.add_parser("apply", help="Apply changes.")
    parser_tf_apply.add_argument("plan_file", nargs="?", help="Plan file to apply.")
    parser_tf_apply.add_argument("--auto-approve", action="store_true", help="Skip interactive approval.")

    # tf destroy
    parser_tf_destroy = tf_subparsers.add_parser("destroy", help="Destroy infrastructure.")
    parser_tf_destroy.add_argument("--auto-approve", action="store_true", help="Skip interactive approval.")

    # tf validate
    tf_subparsers.add_parser("validate", help="Validate configuration.")

    # tf fmt
    parser_tf_fmt = tf_subparsers.add_parser("fmt", help="Format configuration.")
    parser_tf_fmt.add_argument("--check", action="store_true", help="Check if formatted.")
    parser_tf_fmt.add_argument("--recursive", action="store_true", help="Recursive.")

    # tf output
    parser_tf_output = tf_subparsers.add_parser("output", help="Read outputs.")
    parser_tf_output.add_argument("--json", action="store_true", help="JSON output.")

    # tf show
    parser_tf_show = tf_subparsers.add_parser("show", help="Show state or plan.")
    parser_tf_show.add_argument("plan_file", nargs="?", help="Plan file to show.")
    parser_tf_show.add_argument("--json", action="store_true", help="JSON output.")

    # --- New 'dns-lab' command ---
    parser_dns = subparsers.add_parser(
        "dns-lab",
        aliases=["dns"],
        help="DNS utilities (lookup, propagation)."
    )
    dns_subparsers = parser_dns.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # dns-lab lookup
    parser_dns_lookup = dns_subparsers.add_parser("lookup", help="Perform a DNS lookup.")
    parser_dns_lookup.add_argument("domain", help="Domain to lookup.")
    parser_dns_lookup.add_argument("--type", "-t", default="A", help="Record type (A, AAAA, MX, TXT, etc.).")
    parser_dns_lookup.add_argument("--server", "-s", help="Specific nameserver to query.")

    # dns-lab propagation
    parser_dns_prop = dns_subparsers.add_parser("propagation", help="Check DNS propagation.")
    parser_dns_prop.add_argument("domain", help="Domain to check.")
    parser_dns_prop.add_argument("--type", "-t", default="A", help="Record type.")

    # --- New 'whois-lab' command ---
    parser_whois = subparsers.add_parser(
        "whois-lab",
        aliases=["whois"],
        help="Whois utilities (lookup, check)."
    )
    whois_subparsers = parser_whois.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # whois-lab lookup
    parser_whois_lookup = whois_subparsers.add_parser("lookup", help="Perform a WHOIS lookup.")
    parser_whois_lookup.add_argument("domain", help="Domain to lookup.")
    parser_whois_lookup.add_argument("--server", "-s", help="Specific WHOIS server to query.")

    # whois-lab check
    parser_whois_check = whois_subparsers.add_parser("check", help="Check domain availability.")
    parser_whois_check.add_argument("domain", help="Domain to check.")
    parser_whois_check.add_argument("--verbose", "-v", action="store_true", help="Show raw output.")

    # --- New 's3-lab' command ---
    parser_s3 = subparsers.add_parser(
        "s3-lab",
        aliases=["s3"],
        help="S3 utilities (ls, mb, rb, cp, rm, presign)."
    )
    parser_s3.add_argument("--endpoint-url", help="Override endpoint URL (e.g. for MinIO).")
    parser_s3.add_argument("--profile", help="AWS profile name.")
    parser_s3.add_argument("--region", help="AWS region name.")

    s3_subparsers = parser_s3.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # s3 ls
    parser_s3_ls = s3_subparsers.add_parser("ls", help="List buckets or objects.")
    parser_s3_ls.add_argument("bucket", nargs="?", help="Bucket name.")
    parser_s3_ls.add_argument("--prefix", help="Filter by prefix.")

    # s3 mb
    parser_s3_mb = s3_subparsers.add_parser("mb", help="Make bucket.")
    parser_s3_mb.add_argument("bucket", help="Bucket name.")
    parser_s3_mb.add_argument("--region", help="Region constraint.")

    # s3 rb
    parser_s3_rb = s3_subparsers.add_parser("rb", help="Remove bucket.")
    parser_s3_rb.add_argument("bucket", help="Bucket name.")

    # s3 cp
    parser_s3_cp = s3_subparsers.add_parser("cp", help="Copy file.")
    parser_s3_cp.add_argument("src", help="Source path (local or s3://...).")
    parser_s3_cp.add_argument("dest", help="Destination path (local or s3://...).")

    # s3 rm
    parser_s3_rm = s3_subparsers.add_parser("rm", help="Remove object.")
    parser_s3_rm.add_argument("bucket", help="Bucket name.")
    parser_s3_rm.add_argument("key", help="Object key.")

    # s3 presign
    parser_s3_presign = s3_subparsers.add_parser("presign", help="Generate presigned URL.")
    parser_s3_presign.add_argument("bucket", help="Bucket name.")
    parser_s3_presign.add_argument("key", help="Object key.")
    parser_s3_presign.add_argument("--expires-in", type=int, default=3600, help="Expiration in seconds.")

    # --- New 'graphql-lab' command ---
    parser_gql = subparsers.add_parser(
        "graphql-lab",
        aliases=["gql"],
        help="GraphQL utilities (query, schema)."
    )
    parser_gql.add_argument("url", help="GraphQL Endpoint URL.")
    parser_gql.add_argument("--header", "-H", action="append", help="HTTP Header (Key:Value).")

    gql_subparsers = parser_gql.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # gql query
    parser_gql_query = gql_subparsers.add_parser("query", help="Execute a GraphQL query.")
    parser_gql_query.add_argument("query", help="Query string or file path.")
    parser_gql_query.add_argument("--variables", "-v", help="Variables (JSON string or file path).")
    parser_gql_query.add_argument("--verbose", action="store_true", help="Verbose output.")

    # gql schema
    parser_gql_schema = gql_subparsers.add_parser("schema", help="Introspect schema.")
    parser_gql_schema.add_argument("--format", "-f", choices=["sdl", "json"], default="sdl", help="Output format.")

    # --- New 'helm-lab' command ---
    parser_helm = subparsers.add_parser(
        "helm-lab",
        aliases=["helm"],
        help="Helm utilities (ls, install, uninstall, status, repo)."
    )
    helm_subparsers = parser_helm.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # helm ls
    parser_helm_ls = helm_subparsers.add_parser("ls", aliases=["list"], help="List releases.")
    parser_helm_ls.add_argument("--all", action="store_true", help="Show all namespaces.")
    parser_helm_ls.add_argument("--namespace", "-n", help="Namespace scope.")

    # helm install
    parser_helm_install = helm_subparsers.add_parser("install", help="Install a chart.")
    parser_helm_install.add_argument("name", help="Release name.")
    parser_helm_install.add_argument("chart", help="Chart reference.")
    parser_helm_install.add_argument("--namespace", "-n", help="Namespace scope.")
    parser_helm_install.add_argument("--values", "-f", help="Values file.")
    parser_helm_install.add_argument("--set", action="append", help="Set values (can specify multiple).")

    # helm uninstall
    parser_helm_uninstall = helm_subparsers.add_parser("uninstall", aliases=["delete"], help="Uninstall a release.")
    parser_helm_uninstall.add_argument("name", help="Release name.")
    parser_helm_uninstall.add_argument("--namespace", "-n", help="Namespace scope.")

    # helm status
    parser_helm_status = helm_subparsers.add_parser("status", help="Get release status.")
    parser_helm_status.add_argument("name", help="Release name.")
    parser_helm_status.add_argument("--namespace", "-n", help="Namespace scope.")

    # helm repo
    parser_helm_repo = helm_subparsers.add_parser("repo", help="Manage repos.")
    helm_repo_subparsers = parser_helm_repo.add_subparsers(dest="subaction", required=True)

    # helm repo add
    parser_helm_repo_add = helm_repo_subparsers.add_parser("add", help="Add a repo.")
    parser_helm_repo_add.add_argument("name", help="Repo name.")
    parser_helm_repo_add.add_argument("url", help="Repo URL.")

    # helm repo update
    helm_repo_subparsers.add_parser("update", help="Update repos.")

    # helm repo list
    helm_repo_subparsers.add_parser("list", help="List repos.")

    # --- New 'notebook-lab' command ---
    parser_nb = subparsers.add_parser(
        "notebook-lab",
        aliases=["nb"],
        help="Jupyter Notebook utilities (list, inspect, clean, convert, audit)."
    )
    nb_subparsers = parser_nb.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # nb list
    nb_subparsers.add_parser("list", help="List notebooks.")

    # nb inspect
    parser_nb_inspect = nb_subparsers.add_parser("inspect", help="Inspect notebook metadata.")
    parser_nb_inspect.add_argument("file", help="Notebook file path.")

    # nb clean
    parser_nb_clean = nb_subparsers.add_parser("clean", help="Clean output and execution counts.")
    parser_nb_clean.add_argument("file", help="Notebook file path.")
    parser_nb_clean.add_argument("--dry-run", action="store_true", help="Don't modify file.")

    # nb convert
    parser_nb_convert = nb_subparsers.add_parser("convert", help="Convert to Python script.")
    parser_nb_convert.add_argument("file", help="Notebook file path.")

    # nb audit
    parser_nb_audit = nb_subparsers.add_parser("audit", help="Audit notebook for issues.")
    parser_nb_audit.add_argument("file", help="Notebook file path.")

    # --- New 'grpc-lab' command ---
    parser_grpc = subparsers.add_parser(
        "grpc-lab",
        aliases=["grpc"],
        help="gRPC utilities (list, describe, call)."
    )
    parser_grpc.add_argument("--host", required=True, help="gRPC host:port.")
    parser_grpc.add_argument("--plaintext", action="store_true", help="Use plaintext connection.")
    parser_grpc.add_argument("--authority", help="Value of :authority pseudo-header.")

    grpc_subparsers = parser_grpc.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # grpc list
    parser_grpc_list = grpc_subparsers.add_parser("list", help="List services or methods.")
    parser_grpc_list.add_argument("service", nargs="?", help="Service name (optional).")

    # grpc describe
    parser_grpc_describe = grpc_subparsers.add_parser("describe", help="Describe a symbol.")
    parser_grpc_describe.add_argument("symbol", help="Symbol to describe.")

    # grpc call
    parser_grpc_call = grpc_subparsers.add_parser("call", help="Call a method.")
    parser_grpc_call.add_argument("method", help="Method to call.")
    parser_grpc_call.add_argument("--data", "-d", help="JSON data.")

    # --- New 'monitor-lab' command ---
    parser_mon = subparsers.add_parser(
        "monitor-lab",
        aliases=["monitor", "mon"],
        help="System monitoring utilities (stats, procs, kill, watch)."
    )
    mon_subparsers = parser_mon.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # mon stats
    mon_subparsers.add_parser("stats", help="Show system statistics.")

    # mon procs
    parser_mon_procs = mon_subparsers.add_parser("procs", help="List processes.")
    parser_mon_procs.add_argument("--sort", choices=["cpu", "memory", "pid", "name"], default="cpu", help="Sort by.")
    parser_mon_procs.add_argument("--limit", "-n", type=int, default=20, help="Limit number of processes.")
    parser_mon_procs.add_argument("--filter", "-f", help="Filter by name.")

    # mon kill
    parser_mon_kill = mon_subparsers.add_parser("kill", help="Kill a process.")
    parser_mon_kill.add_argument("--pid", type=int, help="PID to kill.")
    parser_mon_kill.add_argument("--filter", "-f", help="Kill processes matching name (interactive).")

    # mon watch
    parser_mon_watch = mon_subparsers.add_parser("watch", help="Watch stats and processes.")
    parser_mon_watch.add_argument("--sort", choices=["cpu", "memory", "pid", "name"], default="cpu", help="Sort processes by.")
    parser_mon_watch.add_argument("--limit", "-n", type=int, default=20, help="Limit number of processes.")
    parser_mon_watch.add_argument("--filter", "-f", help="Filter processes by name.")

    # --- New 'metrics-lab' command ---
    parser_metrics = subparsers.add_parser(
        "metrics-lab",
        aliases=["metrics"],
        help="Prometheus metrics utilities (scrape, lint, serve)."
    )
    metrics_subparsers = parser_metrics.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # metrics scrape
    parser_metrics_scrape = metrics_subparsers.add_parser("scrape", help="Scrape metrics from a URL.")
    parser_metrics_scrape.add_argument("url", help="URL to scrape.")
    parser_metrics_scrape.add_argument("--filter", "-f", help="Filter metrics by name.")

    # metrics lint
    parser_metrics_lint = metrics_subparsers.add_parser("lint", help="Lint metrics from a URL.")
    parser_metrics_lint.add_argument("url", help="URL to lint.")

    # metrics serve
    parser_metrics_serve = metrics_subparsers.add_parser("serve", help="Serve system metrics.")
    parser_metrics_serve.add_argument("--port", "-p", type=int, default=8000, help="Port to listen on.")

    # --- New 'trace-lab' command ---
    parser_trace = subparsers.add_parser(
        "trace-lab",
        aliases=["trace"],
        help="System call tracer with AI analysis."
    )
    trace_subparsers = parser_trace.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # trace run
    parser_trace_run = trace_subparsers.add_parser("run", help="Run a command under trace.")
    parser_trace_run.add_argument("--output", "-o", help="Output trace file (default: trace.log).")
    parser_trace_run.add_argument("--explain", action="store_true", help="Ask AI to explain the trace immediately.")
    parser_trace_run.add_argument("command_args", nargs=argparse.REMAINDER, help="Command to trace (e.g. ls -la).")

    # trace analyze
    parser_trace_analyze = trace_subparsers.add_parser("analyze", help="Analyze an existing trace file.")
    parser_trace_analyze.add_argument("file", help="Path to trace file.")
    parser_trace_analyze.add_argument("--json", action="store_true", help="Output as JSON.")

    # trace explain
    parser_trace_explain = trace_subparsers.add_parser("explain", help="Ask AI to explain an existing trace.")
    parser_trace_explain.add_argument("file", help="Path to trace file.")

    # --- New 'notify-lab' command ---
    parser_notify = subparsers.add_parser(
        "notify-lab",
        aliases=["notify"],
        help="Send notifications to various channels."
    )
    parser_notify.add_argument("message", nargs="?", help="Message to send (or via stdin).")
    parser_notify.add_argument("--title", help="Notification title.")
    parser_notify.add_argument("--to", action="append", choices=["desktop", "slack", "discord", "console", "all"], help="Target channels (default: desktop).")
    parser_notify.add_argument("--slack-url", help="Override Slack Webhook URL.")
    parser_notify.add_argument("--discord-url", help="Override Discord Webhook URL.")

    # --- New 'fuzz-lab' command ---
    parser_fuzz = subparsers.add_parser(
        "fuzz-lab",
        aliases=["fuzz"],
        help="Fuzzing utilities (cli, function)."
    )
    fuzz_subparsers = parser_fuzz.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # fuzz cli
    parser_fuzz_cli = fuzz_subparsers.add_parser("cli", help="Fuzz a CLI command.")
    parser_fuzz_cli.add_argument("target", help="Command to fuzz (e.g. 'python3 app.py').")
    parser_fuzz_cli.add_argument("--count", "-c", type=int, default=100, help="Number of iterations.")
    parser_fuzz_cli.add_argument("--timeout", "-t", type=int, default=5, help="Timeout per iteration (seconds).")

    # fuzz function
    parser_fuzz_func = fuzz_subparsers.add_parser("function", aliases=["func"], help="Fuzz a Python function.")
    parser_fuzz_func.add_argument("target", help="Function target (e.g. 'shared/utils.py:format_date').")
    parser_fuzz_func.add_argument("--count", "-c", type=int, default=100, help="Number of iterations.")

    # --- New 'static-lab' command ---
    parser_static = subparsers.add_parser(
        "static-lab",
        aliases=["static", "serve-static"],
        help="Advanced static file server with testing capabilities."
    )
    parser_static.add_argument("--port", "-p", type=int, default=8000, help="Port to listen on.")
    parser_static.add_argument("--dir", "-d", default=".", help="Directory to serve.")
    parser_static.add_argument("--cors", action="store_true", help="Enable CORS.")
    parser_static.add_argument("--delay", type=float, default=0, help="Artificial latency in seconds.")
    parser_static.add_argument("--error-rate", type=float, default=0, help="Probability of returning 500 errors (0.0-1.0).")
    parser_static.add_argument("--auth", help="Basic Auth credentials (user:pass).")
    parser_static.add_argument("--upload", help="Directory to allow file uploads to.")
    parser_static.add_argument("--spa", action="store_true", help="Enable SPA mode (rewrite 404 to index.html).")
    parser_static.add_argument("--ssl", action="store_true", help="Enable HTTPS (self-signed).")

    # --- New 'contract-lab' command ---
    parser_contract = subparsers.add_parser(
        "contract-lab",
        aliases=["contract"],
        help="Contract testing and verification."
    )
    contract_subparsers = parser_contract.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # contract verify
    parser_contract_verify = contract_subparsers.add_parser("verify", help="Verify a running service against an OpenAPI spec.")
    parser_contract_verify.add_argument("--spec", required=True, help="Path to OpenAPI specification (YAML/JSON).")
    parser_contract_verify.add_argument("--url", required=True, help="Target URL of the running service.")

    # --- New 'ansible-lab' command ---
    parser_ansible = subparsers.add_parser(
        "ansible-lab",
        aliases=["ansible"],
        help="Ansible utilities (playbook, lint, inventory, doc, init)."
    )
    ansible_subparsers = parser_ansible.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # ansible playbook
    parser_ansible_playbook = ansible_subparsers.add_parser("playbook", help="Run an Ansible playbook.")
    parser_ansible_playbook.add_argument("playbook", help="Path to the playbook file.")
    parser_ansible_playbook.add_argument("--inventory", "-i", help="Path to inventory file.")
    parser_ansible_playbook.add_argument("--check", action="store_true", help="Run in check mode (dry run).")
    parser_ansible_playbook.add_argument("--diff", action="store_true", help="Show differences.")
    parser_ansible_playbook.add_argument("--limit", "-l", help="Limit to specific hosts.")
    parser_ansible_playbook.add_argument("--extra-vars", "-e", help="Set additional variables (key=value).")

    # ansible lint
    parser_ansible_lint = ansible_subparsers.add_parser("lint", help="Lint Ansible files.")
    parser_ansible_lint.add_argument("path", nargs="?", default=".", help="Path to lint (default: current directory).")

    # ansible inventory
    parser_ansible_inv = ansible_subparsers.add_parser("inventory", help="List inventory.")
    parser_ansible_inv.add_argument("--inventory", "-i", help="Path to inventory file.")

    # ansible doc
    parser_ansible_doc = ansible_subparsers.add_parser("doc", help="Show documentation for a module.")
    parser_ansible_doc.add_argument("module", help="Module name (e.g., yum, copy).")

    # ansible init
    parser_ansible_init = ansible_subparsers.add_parser("init", help="Scaffold a new Ansible project.")
    parser_ansible_init.add_argument("name", nargs="?", help="Project name (creates a directory).")

    # --- New 'hex-lab' command ---
    parser_hex = subparsers.add_parser(
        "hex-lab",
        aliases=["hex"],
        help="Interactive Hex Editor TUI."
    )
    # The TUI usually takes over, but we can accept a file argument to open immediately
    parser_hex.add_argument("file", nargs="?", help="Path to file to open in Hex Editor.")

    # --- New 'speed-lab' command ---
    parser_speed = subparsers.add_parser(
        "speed-lab",
        aliases=["speed"],
        help="System performance benchmarks (internet, disk, network)."
    )
    speed_subparsers = parser_speed.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # speed internet
    parser_speed_net = speed_subparsers.add_parser("internet", aliases=["net"], help="Measure internet download speed.")
    parser_speed_net.add_argument("--timeout", type=int, default=30, help="Timeout in seconds.")

    # speed disk
    parser_speed_disk = speed_subparsers.add_parser("disk", aliases=["io"], help="Measure disk I/O speed.")
    parser_speed_disk.add_argument("--size", type=int, default=100, help="Size in MB (default: 100).")

    # speed local
    parser_speed_local = speed_subparsers.add_parser("local", aliases=["lan"], help="Measure local network throughput.")
    parser_speed_local.add_argument("--server", action="store_true", help="Run in server mode.")
    parser_speed_local.add_argument("--host", help="Host to bind/connect to. Defaults to 0.0.0.0 for server.")
    parser_speed_local.add_argument("--port", type=int, default=5201, help="Port (default: 5201).")
    parser_speed_local.add_argument("--duration", type=int, default=10, help="Test duration in seconds (client mode only).")

    # speed cpu
    parser_speed_cpu = speed_subparsers.add_parser("cpu", help="Benchmark CPU performance (calculate primes).")
    parser_speed_cpu.add_argument("--limit", type=int, default=20000, help="Upper limit for prime calculation (default: 20000).")

    # speed memory
    parser_speed_mem = speed_subparsers.add_parser("memory", aliases=["mem"], help="Benchmark RAM speed (write/read).")
    parser_speed_mem.add_argument("--size", type=int, default=100, help="Size in MB (default: 100).")

    # --- New 'load-lab' command ---
    parser_load = subparsers.add_parser(
        "load-lab",
        aliases=["load"],
        help="HTTP load testing tool."
    )
    parser_load.add_argument("--url", required=True, help="Target URL.")
    parser_load.add_argument("--users", "-u", type=int, default=1, help="Number of concurrent users.")
    parser_load.add_argument("--duration", "-d", type=int, default=10, help="Duration of test in seconds.")
    parser_load.add_argument("--method", "-m", default="GET", help="HTTP Method (GET, POST, etc).")
    parser_load.add_argument("--body", help="Request body.")
    parser_load.add_argument("--headers", help="Request headers (Key:Value,Key2:Value2).")

    # --- New 'ast-lab' command ---
    parser_ast = subparsers.add_parser(
        "ast-lab",
        aliases=["ast"],
        help="Inspect Python AST."
    )
    ast_subparsers = parser_ast.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # ast parse
    parser_ast_parse = ast_subparsers.add_parser("parse", help="Dump AST for code.")
    parser_ast_parse.add_argument("--code", help="Python code string.")
    parser_ast_parse.add_argument("--file", help="Python file path.")

    # ast check
    parser_ast_check = ast_subparsers.add_parser("check", help="Check syntax.")
    parser_ast_check.add_argument("--code", help="Python code string.")
    parser_ast_check.add_argument("--file", help="Python file path.")

    # --- New 'otp-lab' command ---
    parser_otp = subparsers.add_parser(
        "otp-lab",
        aliases=["otp", "totp", "mfa"],
        help="Generate and verify One-Time Passwords (TOTP/HOTP)."
    )
    otp_subparsers = parser_otp.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # otp generate
    parser_otp_gen = otp_subparsers.add_parser("generate", help="Generate a new random Base32 secret.")
    parser_otp_gen.add_argument("--length", type=int, default=16, help="Length of secret (default: 16).")

    # otp code
    parser_otp_code = otp_subparsers.add_parser("code", help="Generate current TOTP code.")
    parser_otp_code.add_argument("secret", help="Base32 secret key.")
    parser_otp_code.add_argument("--interval", type=int, default=30, help="Time interval (default: 30).")
    parser_otp_code.add_argument("--digits", type=int, default=6, help="Number of digits (default: 6).")

    # otp verify
    parser_otp_verify = otp_subparsers.add_parser("verify", help="Verify a TOTP code.")
    parser_otp_verify.add_argument("secret", help="Base32 secret key.")
    parser_otp_verify.add_argument("code", help="Code to verify.")
    parser_otp_verify.add_argument("--window", type=int, default=1, help="Window of intervals to check (default: 1).")

    # otp url
    parser_otp_url = otp_subparsers.add_parser("url", help="Generate otpauth URL.")
    parser_otp_url.add_argument("secret", help="Base32 secret key.")
    parser_otp_url.add_argument("--label", required=True, help="Account label (e.g. user@example.com).")
    parser_otp_url.add_argument("--issuer", help="Issuer name (e.g. MyApp).")

    # --- New 'cheatsheet-lab' command ---
    parser_cheat = subparsers.add_parser(
        "cheatsheet-lab",
        aliases=["cheatsheet", "cheat"],
        help="Developer cheat sheets."
    )
    parser_cheat.add_argument("topic", nargs="?", help="Topic to view.")
    parser_cheat.add_argument("--search", help="Search for topics.")

    # --- New 'calendar-lab' command ---
    parser_cal = subparsers.add_parser(
        "calendar-lab",
        aliases=["calendar", "cal"],
        help="Project Calendar."
    )
    parser_cal.add_argument("--year", type=int, help="Year (default: current).")
    parser_cal.add_argument("--month", type=int, help="Month (1-12) (default: current).")

    # --- New 'finance-lab' command ---
    parser_fin = subparsers.add_parser(
        "finance-lab",
        aliases=["finance", "fin"],
        help="Financial calculators (loan, compound, npv, roi, break-even, inflation)."
    )
    fin_subparsers = parser_fin.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # loan
    parser_fin_loan = fin_subparsers.add_parser("loan", help="Calculate loan payments.")
    parser_fin_loan.add_argument("--principal", type=float, help="Loan amount.")
    parser_fin_loan.add_argument("--rate", type=float, help="Annual interest rate (%).")
    parser_fin_loan.add_argument("--term", type=int, help="Loan term in years.")

    # compound
    parser_fin_compound = fin_subparsers.add_parser("compound", help="Calculate compound interest.")
    parser_fin_compound.add_argument("--principal", type=float, help="Principal amount.")
    parser_fin_compound.add_argument("--rate", type=float, help="Annual interest rate (%).")
    parser_fin_compound.add_argument("--time", type=int, help="Time in years.")
    parser_fin_compound.add_argument("--frequency", type=int, default=1, help="Compounding frequency per year (default: 1).")

    # npv
    parser_fin_npv = fin_subparsers.add_parser("npv", help="Calculate Net Present Value.")
    parser_fin_npv.add_argument("--rate", type=float, help="Discount rate (%).")
    parser_fin_npv.add_argument("--flows", help="Comma-separated cash flows (e.g., -1000,200,300).")

    # roi
    parser_fin_roi = fin_subparsers.add_parser("roi", help="Calculate Return on Investment.")
    parser_fin_roi.add_argument("--initial", type=float, help="Initial investment.")
    parser_fin_roi.add_argument("--final", type=float, help="Final value.")

    # break-even
    parser_fin_be = fin_subparsers.add_parser("break-even", help="Calculate Break-Even Point.")
    parser_fin_be.add_argument("--fixed", type=float, help="Fixed costs.")
    parser_fin_be.add_argument("--variable", type=float, help="Variable cost per unit.")
    parser_fin_be.add_argument("--price", type=float, help="Price per unit.")

    # inflation
    parser_fin_inf = fin_subparsers.add_parser("inflation", help="Calculate inflation effect.")
    parser_fin_inf.add_argument("--value", type=float, help="Initial value.")
    parser_fin_inf.add_argument("--rate", type=float, help="Inflation rate (%).")
    parser_fin_inf.add_argument("--years", type=int, help="Number of years.")

    # --- New 'runner-lab' command ---
    parser_runner = subparsers.add_parser(
        "runner-lab",
        aliases=["runner"],
        help="Task Runner (Makefile, package.json, etc)."
    )
    runner_subparsers = parser_runner.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # runner list
    parser_runner_list = runner_subparsers.add_parser("list", help="List available tasks.")

    # runner run
    parser_runner_run = runner_subparsers.add_parser("run", help="Run a task.")
    parser_runner_run.add_argument("task_name", help="Name of the task to run.")

    # --- New 'gitignore-lab' command ---
    parser_gi = subparsers.add_parser(
        "gitignore-lab",
        aliases=["gitignore", "gi"],
        help="Generate and check .gitignore files."
    )
    gi_subparsers = parser_gi.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # gi list
    parser_gi_list = gi_subparsers.add_parser("list", help="List available templates.")

    # gi generate
    parser_gi_gen = gi_subparsers.add_parser("generate", help="Generate .gitignore content.")
    parser_gi_gen.add_argument("--templates", required=True, help="Comma-separated list of templates.")

    # gi check
    parser_gi_check = gi_subparsers.add_parser("check", help="Check if a file is ignored.")
    parser_gi_check.add_argument("path", help="Path to file to check.")

    # gi append
    parser_gi_append = gi_subparsers.add_parser("append", help="Append templates to .gitignore.")
    parser_gi_append.add_argument("--templates", required=True, help="Comma-separated list of templates.")

    # --- New 'permissions-lab' command ---
    parser_perm = subparsers.add_parser(
        "permissions-lab",
        aliases=["permissions", "perm", "chmod"],
        help="Manage and calculate Unix permissions."
    )
    perm_subparsers = parser_perm.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # perm check
    parser_perm_check = perm_subparsers.add_parser("check", help="Check permissions of a file.")
    parser_perm_check.add_argument("file", help="Path to file.")

    # perm calc
    parser_perm_calc = perm_subparsers.add_parser("calc", help="Calculate permissions (octal <-> symbolic).")
    parser_perm_calc.add_argument("value", help="Octal (755) or Symbolic (rwxr-xr-x) string.")

    # perm set
    parser_perm_set = perm_subparsers.add_parser("set", help="Set permissions of a file.")
    parser_perm_set.add_argument("value", help="Octal string (e.g. 755).")
    parser_perm_set.add_argument("file", help="Path to file.")

    # perm explain
    parser_perm_explain = perm_subparsers.add_parser("explain", help="Explain permission string.")
    parser_perm_explain.add_argument("value", help="Octal (755) or Symbolic (rwxr-xr-x) string.")

    # --- New 'ollama-lab' command ---
    parser_ollama = subparsers.add_parser(
        "ollama-lab",
        aliases=["ollama", "ol"],
        help="Manage local Ollama models."
    )
    ollama_subparsers = parser_ollama.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # ollama list
    parser_ollama_list = ollama_subparsers.add_parser("list", help="List installed models.")

    # ollama pull
    parser_ollama_pull = ollama_subparsers.add_parser("pull", help="Pull a model.")
    parser_ollama_pull.add_argument("name", help="Model name.")

    # ollama delete
    parser_ollama_delete = ollama_subparsers.add_parser("delete", help="Delete a model.")
    parser_ollama_delete.add_argument("name", help="Model name.")

    # ollama show
    parser_ollama_show = ollama_subparsers.add_parser("show", help="Show model info.")
    parser_ollama_show.add_argument("name", help="Model name.")

    # ollama chat
    parser_ollama_chat = ollama_subparsers.add_parser("chat", help="Chat with a model.")
    parser_ollama_chat.add_argument("name", help="Model name.")
    parser_ollama_chat.add_argument("message", help="Message to send.")

    # --- New 'mqtt-lab' command ---
    parser_mqtt = subparsers.add_parser(
        "mqtt-lab",
        aliases=["mqtt", "mq"],
        help="MQTT Client (Publish, Subscribe, Check)."
    )
    # Global MQTT args
    parser_mqtt.add_argument("--host", default="localhost", help="MQTT Broker Host.")
    parser_mqtt.add_argument("--port", type=int, default=1883, help="MQTT Broker Port.")
    parser_mqtt.add_argument("--username", help="Username.")
    parser_mqtt.add_argument("--password", help="Password.")

    mqtt_subparsers = parser_mqtt.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # mqtt check
    parser_mqtt_check = mqtt_subparsers.add_parser("check", help="Check connection to broker.")

    # mqtt pub
    parser_mqtt_pub = mqtt_subparsers.add_parser("pub", help="Publish a message.")
    parser_mqtt_pub.add_argument("--topic", "-t", required=True, help="Topic to publish to.")
    parser_mqtt_pub.add_argument("--message", "-m", required=True, help="Message payload.")
    parser_mqtt_pub.add_argument("--qos", type=int, default=0, choices=[0, 1, 2], help="Quality of Service.")
    parser_mqtt_pub.add_argument("--retain", action="store_true", help="Retain message.")

    # mqtt sub
    parser_mqtt_sub = mqtt_subparsers.add_parser("sub", help="Subscribe to a topic.")
    parser_mqtt_sub.add_argument("--topic", "-t", required=True, help="Topic to subscribe to.")
    parser_mqtt_sub.add_argument("--qos", type=int, default=0, choices=[0, 1, 2], help="Quality of Service.")

    # --- New 'path-lab' command ---
    parser_path = subparsers.add_parser(
        "path-lab",
        aliases=["path"],
        help="Path manipulation and analysis."
    )
    path_subparsers = parser_path.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # path analyze
    parser_path_analyze = path_subparsers.add_parser("analyze", help="Analyze a path.")
    parser_path_analyze.add_argument("path", help="Path to analyze.")

    # path relative
    parser_path_rel = path_subparsers.add_parser("relative", help="Calculate relative path.")
    parser_path_rel.add_argument("target", help="Target path.")
    parser_path_rel.add_argument("start", help="Start path.")

    # path join
    parser_path_join = path_subparsers.add_parser("join", help="Join path components.")
    parser_path_join.add_argument("base", help="Base path.")
    parser_path_join.add_argument("parts", nargs="+", help="Path components.")

    # path glob
    parser_path_glob = path_subparsers.add_parser("glob", help="Glob pattern.")
    parser_path_glob.add_argument("root", help="Root directory.")
    parser_path_glob.add_argument("pattern", help="Glob pattern.")
    parser_path_glob.add_argument("--recursive", "-r", action="store_true", help="Recursive glob.")

    # --- New 'systemd-lab' command ---
    parser_systemd = subparsers.add_parser(
        "systemd-lab",
        aliases=["systemd", "service"],
        help="Manage systemd units (generate, list, status)."
    )
    systemd_subparsers = parser_systemd.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # systemd generate
    parser_systemd_gen = systemd_subparsers.add_parser("generate", help="Generate a .service file.")
    parser_systemd_gen.add_argument("--name", required=True, help="Service name.")
    parser_systemd_gen.add_argument("--cmd", required=True, help="Command to run.")
    parser_systemd_gen.add_argument("--user", default="root", help="User to run as.")
    parser_systemd_gen.add_argument("--workdir", help="Working directory.")
    parser_systemd_gen.add_argument("--description", help="Service description.")
    parser_systemd_gen.add_argument("--env", help="Environment variables (key=value,key=value).")
    parser_systemd_gen.add_argument("--restart", default="always", help="Restart policy.")
    parser_systemd_gen.add_argument("--type", default="simple", help="Service type.")
    parser_systemd_gen.add_argument("--output", help="Output file path.")

    # systemd list
    parser_systemd_list = systemd_subparsers.add_parser("list", help="List active units.")
    parser_systemd_list.add_argument("pattern", nargs="?", help="Pattern to match.")

    # systemd status
    parser_systemd_status = systemd_subparsers.add_parser("status", help="Get service status.")
    parser_systemd_status.add_argument("name", help="Service name.")

    # systemd logs
    parser_systemd_logs = systemd_subparsers.add_parser("logs", help="Get service logs.")
    parser_systemd_logs.add_argument("name", help="Service name.")
    parser_systemd_logs.add_argument("--lines", type=int, default=50, help="Number of lines.")

    # systemd control
    for action in ["start", "stop", "restart", "enable", "disable"]:
        parser_systemd_ctrl = systemd_subparsers.add_parser(action, help=f"{action.capitalize()} a service.")
        parser_systemd_ctrl.add_argument("name", help="Service name.")

    # --- New 'ascii-lab' command ---
    parser_ascii = subparsers.add_parser(
        "ascii-lab",
        aliases=["ascii"],
        help="ASCII Art Generator (Image, GIF)."
    )
    ascii_subparsers = parser_ascii.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # ascii image
    parser_ascii_img = ascii_subparsers.add_parser("image", help="Convert image to ASCII.")
    parser_ascii_img.add_argument("--file", "-f", required=True, help="Input image file.")
    parser_ascii_img.add_argument("--width", type=int, default=100, help="Output width.")
    parser_ascii_img.add_argument("--charset", default="standard", choices=["standard", "simple", "blocks", "binary", "matrix", "numbers"], help="Charset to use.")
    parser_ascii_img.add_argument("--inverse", action="store_true", help="Inverse brightness.")

    # ascii play
    parser_ascii_play = ascii_subparsers.add_parser("play", help="Play GIF as ASCII animation.")
    parser_ascii_play.add_argument("--file", "-f", required=True, help="Input GIF file.")
    parser_ascii_play.add_argument("--width", type=int, default=100, help="Output width.")
    parser_ascii_play.add_argument("--charset", default="standard", choices=["standard", "simple", "blocks", "binary", "matrix", "numbers"], help="Charset to use.")
    parser_ascii_play.add_argument("--inverse", action="store_true", help="Inverse brightness.")
    parser_ascii_play.add_argument("--fps", type=float, help="Override FPS.")

    # --- New 'weather-lab' command ---
    parser_weather = subparsers.add_parser(
        "weather-lab",
        aliases=["weather", "w"],
        help="Weather Information (Current, Forecast)."
    )
    weather_subparsers = parser_weather.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # weather current
    parser_weather_curr = weather_subparsers.add_parser("current", help="Get current weather.")
    parser_weather_curr.add_argument("--city", help="City name (or empty for auto).")
    parser_weather_curr.add_argument("--units", default="metric", choices=["metric", "imperial"], help="Units (metric/imperial).")

    # weather forecast
    parser_weather_fore = weather_subparsers.add_parser("forecast", help="Get weather forecast.")
    parser_weather_fore.add_argument("--city", help="City name (or empty for auto).")
    parser_weather_fore.add_argument("--units", default="metric", choices=["metric", "imperial"], help="Units (metric/imperial).")

    # --- New 'pattern-lab' command ---
    parser_pattern = subparsers.add_parser(
        "pattern-lab",
        aliases=["pattern", "design"],
        help="Design Pattern Generator."
    )
    pattern_subparsers = parser_pattern.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # pattern list
    pattern_subparsers.add_parser("list", help="List available patterns.")

    # pattern show
    parser_pattern_show = pattern_subparsers.add_parser("show", help="Show pattern code.")
    parser_pattern_show.add_argument("--pattern", "-p", required=True, help="Pattern name.")
    parser_pattern_show.add_argument("--lang", "-l", required=True, help="Language.")

    # pattern generate
    parser_pattern_gen = pattern_subparsers.add_parser("generate", help="Generate pattern file.")
    parser_pattern_gen.add_argument("--pattern", "-p", required=True, help="Pattern name.")
    parser_pattern_gen.add_argument("--lang", "-l", required=True, help="Language.")
    parser_pattern_gen.add_argument("--output", "-o", required=True, help="Output file path.")

    # --- New 'http-server-lab' command ---
    parser_http_server = subparsers.add_parser(
        "http-server-lab",
        aliases=["httpd", "server"],
        help="HTTP Server (Static, Echo, Upload)."
    )
    http_server_subparsers = parser_http_server.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # httpd serve (static)
    parser_http_serve = http_server_subparsers.add_parser("serve", aliases=["static"], help="Serve static files.")
    parser_http_serve.add_argument("--dir", default=".", help="Directory to serve.")
    parser_http_serve.add_argument("--port", type=int, default=8000, help="Port to listen on.")
    parser_http_serve.add_argument("--cors", action="store_true", help="Enable CORS.")

    # httpd echo
    parser_http_echo = http_server_subparsers.add_parser("echo", help="Start echo server.")
    parser_http_echo.add_argument("--port", type=int, default=8080, help="Port to listen on.")

    # httpd upload
    parser_http_upload = http_server_subparsers.add_parser("upload", help="Start upload server.")
    parser_http_upload.add_argument("--dir", default="uploads", help="Upload directory.")
    parser_http_upload.add_argument("--port", type=int, default=8081, help="Port to listen on.")

    # --- New 'bandwidth-lab' command ---
    parser_bw = subparsers.add_parser(
        "bandwidth-lab",
        aliases=["bandwidth", "bw"],
        help="Bandwidth Monitor (List, Monitor)."
    )
    bw_subparsers = parser_bw.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # bw list
    bw_subparsers.add_parser("list", help="List network interfaces and total usage.")

    # bw monitor
    parser_bw_mon = bw_subparsers.add_parser("monitor", help="Monitor bandwidth usage in real-time.")
    parser_bw_mon.add_argument("--interface", "-i", help="Comma-separated list of interfaces to monitor.")
    parser_bw_mon.add_argument("--interval", type=float, default=1.0, help="Update interval in seconds.")

    # --- New 'typing-lab' command ---
    parser_typing = subparsers.add_parser(
        "typing-lab",
        aliases=["type"],
        help="Interactive Code Typing Tutor."
    )

    # --- New 'sound-lab' command ---
    parser_sound = subparsers.add_parser(
        "sound-lab",
        aliases=["sound", "audio"],
        help="Sound Generation (Tone, Noise, DTMF, Morse)."
    )
    sound_subparsers = parser_sound.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # sound tone
    parser_sound_tone = sound_subparsers.add_parser("tone", help="Generate a simple tone.")
    parser_sound_tone.add_argument("--freq", type=float, default=440.0, help="Frequency in Hz.")
    parser_sound_tone.add_argument("--duration", type=float, default=1.0, help="Duration in seconds.")
    parser_sound_tone.add_argument("--wave", default="sine", choices=["sine", "square", "triangle", "sawtooth"], help="Waveform type.")
    parser_sound_tone.add_argument("--output", default="tone.wav", help="Output file path.")

    # sound noise
    parser_sound_noise = sound_subparsers.add_parser("noise", help="Generate noise.")
    parser_sound_noise.add_argument("--type", default="white", choices=["white"], help="Noise type.")
    parser_sound_noise.add_argument("--duration", type=float, default=1.0, help="Duration in seconds.")
    parser_sound_noise.add_argument("--output", default="noise.wav", help="Output file path.")

    # sound dtmf
    parser_sound_dtmf = sound_subparsers.add_parser("dtmf", help="Generate DTMF tones.")
    parser_sound_dtmf.add_argument("sequence", help="Sequence of digits/chars to generate.")
    parser_sound_dtmf.add_argument("--output", default="dtmf.wav", help="Output file path.")

    # sound morse
    parser_sound_morse = sound_subparsers.add_parser("morse", help="Generate Morse code.")
    parser_sound_morse.add_argument("text", help="Text to convert to Morse.")
    parser_sound_morse.add_argument("--wpm", type=int, default=20, help="Words per minute.")
    parser_sound_morse.add_argument("--freq", type=float, default=600.0, help="Tone frequency.")
    parser_sound_morse.add_argument("--output", default="morse.wav", help="Output file path.")

    # sound tui
    sound_subparsers.add_parser("tui", help="Launch interactive TUI.")

    # --- New 'maze-lab' command ---
    parser_maze = subparsers.add_parser(
        "maze-lab",
        aliases=["maze"],
        help="Maze Generator and Solver."
    )
    maze_subparsers = parser_maze.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # maze generate
    parser_maze_gen = maze_subparsers.add_parser("generate", help="Generate a maze.")
    parser_maze_gen.add_argument("--width", type=int, default=21, help="Width (odd number).")
    parser_maze_gen.add_argument("--height", type=int, default=21, help="Height (odd number).")
    parser_maze_gen.add_argument("--algo", default="dfs", choices=["dfs", "prim"], help="Generation algorithm.")
    parser_maze_gen.add_argument("--solve", action="store_true", help="Solve the generated maze immediately.")

    # --- New 'license-lab' command ---
    parser_lic = subparsers.add_parser(
        "license-lab",
        aliases=["lic", "license"],
        help="License Management (Generate, Check, Explain)."
    )
    lic_subparsers = parser_lic.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # lic list
    lic_subparsers.add_parser("list", help="List available license templates.")

    # lic explain
    parser_lic_explain = lic_subparsers.add_parser("explain", help="Explain a license.")
    parser_lic_explain.add_argument("type", help="License type (e.g. mit, apache-2.0).")

    # lic generate
    parser_lic_gen = lic_subparsers.add_parser("generate", help="Generate a LICENSE file.")
    parser_lic_gen.add_argument("--type", "-t", required=True, help="License type.")
    parser_lic_gen.add_argument("--holder", required=True, help="Copyright holder name.")
    parser_lic_gen.add_argument("--year", help="Year (default: current).")
    parser_lic_gen.add_argument("--output", "-o", help="Output path (default: LICENSE).")
    parser_lic_gen.add_argument("--force", "-f", action="store_true", help="Overwrite existing file.")

    # lic check (dependency check)
    parser_lic_check = lic_subparsers.add_parser("check", help="Check dependency licenses.")
    parser_lic_check.add_argument("--allow", help="Comma-separated list of allowed licenses.")
    parser_lic_check.add_argument("--deny", help="Comma-separated list of denied licenses.")

    # --- New 'rfc-lab' command ---
    parser_rfc = subparsers.add_parser(
        "rfc-lab",
        aliases=["rfc"],
        help="RFC Search and Viewer."
    )
    rfc_subparsers = parser_rfc.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # rfc search
    parser_rfc_search = rfc_subparsers.add_parser("search", help="Search RFCs.")
    parser_rfc_search.add_argument("query", help="Search query.")

    # rfc read
    parser_rfc_read = rfc_subparsers.add_parser("read", help="Read an RFC.")
    parser_rfc_read.add_argument("number", help="RFC Number (e.g. 7231).")

    # rfc update
    rfc_subparsers.add_parser("update", help="Update RFC Index.")

    # --- New 'productivity-lab' command ---
    parser_prod = subparsers.add_parser(
        "productivity-lab",
        aliases=["prod", "focus"],
        help="Productivity Tracking (Focus Timer, Distraction Logger)."
    )
    prod_subparsers = parser_prod.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # prod start
    parser_prod_start = prod_subparsers.add_parser("start", help="Start a focus session.")
    parser_prod_start.add_argument("type", choices=["work", "break"], help="Session type.")
    parser_prod_start.add_argument("--task", "-t", help="Task ID or description.")

    # prod stop
    prod_subparsers.add_parser("stop", help="Stop the current session.")

    # prod status
    prod_subparsers.add_parser("status", help="Show current session status.")

    # prod stats
    prod_subparsers.add_parser("stats", help="Show today's statistics.")

    # prod log
    parser_prod_log = prod_subparsers.add_parser("log", help="Log a distraction.")
    parser_prod_log.add_argument("message", help="Distraction description.")

    # prod history
    prod_subparsers.add_parser("history", help="Show session history.")

    # --- New 'rename-lab' command ---
    parser_rename = subparsers.add_parser(
        "rename-lab",
        aliases=["rename"],
        help="Batch Rename Utility (Regex, Transform, Sequence)."
    )
    # rename pattern
    # We make pattern optional if we use --search/--replace
    parser_rename.add_argument("pattern", nargs="?", default="*", help="Glob pattern to find files (default: *).")

    parser_rename.add_argument("--root", help="Root directory (default: current).")
    parser_rename.add_argument("--recursive", "-r", action="store_true", help="Recursive search.")

    parser_rename.add_argument("--search", "-s", help="Regex pattern to search for.")
    parser_rename.add_argument("--replace", "-R", help="Replacement string (can use groups like \\1).")
    parser_rename.add_argument("--transform", "-t", choices=["upper", "lower", "title", "camel", "snake", "kebab", "dot", "path", "constant"], help="Apply text transformation.")

    parser_rename.add_argument("--dry-run", action="store_true", default=True, help="Simulate rename (default).")
    parser_rename.add_argument("--no-dry-run", dest="dry_run", action="store_false", help="Execute rename.")
    parser_rename.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt.")
    parser_rename.add_argument("--tui", action="store_true", help="Launch interactive TUI.")

    # --- New 'find-lab' command ---
    parser_find = subparsers.add_parser(
        "find-lab",
        aliases=["find", "locate"],
        help="Advanced File Finder (Name, Size, Time, Type)."
    )
    parser_find.add_argument("name", nargs="?", help="Glob pattern for filename.")
    parser_find.add_argument("--root", help="Root directory (default: current).")
    parser_find.add_argument("--regex", "-r", help="Regex pattern for filename/path.")
    parser_find.add_argument("--size", "-s", help="Size filter (e.g. '>1M', '<10k').")
    parser_find.add_argument("--time", "-t", help="Time filter (e.g. '>1d' (older), '<1h' (newer)).")
    parser_find.add_argument("--type", choices=["f", "d", "l"], help="File type (f=file, d=dir, l=link).")
    parser_find.add_argument("--ext", "-e", help="Extensions (comma-separated, e.g. 'py,txt').")
    parser_find.add_argument("--delete", action="store_true", help="Delete found files (interactive unless --yes).")
    parser_find.add_argument("--yes", "-y", action="store_true", help="Skip confirmation.")
    parser_find.add_argument("--tui", action="store_true", help="Launch interactive TUI.")

    # --- New 'diagram-lab' command ---
    parser_diagram = subparsers.add_parser(
        "diagram-lab",
        aliases=["diagram", "draw"],
        help="Interactive ASCII Diagram Editor."
    )
    # Default action is TUI for now, but we can support others later
    parser_diagram.add_argument("action", nargs="?", choices=["tui", "demo"], default="tui", help="Action to perform.")

    # --- New 'pipe-lab' command ---
    parser_pipe = subparsers.add_parser(
        "pipe-lab",
        aliases=["pipe", "stream"],
        help="Chainable Text/Data Pipeline."
    )
    parser_pipe.add_argument("input", nargs="?", help="Input string or file path (optional).")
    parser_pipe.add_argument("--do", "-d", action="append", help="Operation to perform (e.g. 'upper', 'json-parse', 'grep foo').")

    # --- New 'dict-lab' command ---
    parser_dict = subparsers.add_parser(
        "dict-lab",
        aliases=["dict", "define", "synonym", "antonym", "thesaurus"],
        help="Dictionary and Thesaurus Utility."
    )
    # If using aliases like 'define word', the 'action' might be implicit or we need to handle it.
    # But argparse aliases map the command name.
    # So 'main.py define foo' -> command='define', args=['foo']
    # We need to handle this mapping in the logic or setup arguments carefully.

    # Actually, aliases in add_parser mainly work if we use that name.
    # But we want 'define' to be the action if called as 'dict-lab define'.

    parser_dict.add_argument("word", help="Word to lookup.")
    parser_dict.add_argument("action", nargs="?", choices=["define", "synonym", "antonym"], default="define", help="Action to perform (default: define).")

    # --- New 'emoji-lab' command ---
    parser_emoji = subparsers.add_parser(
        "emoji-lab",
        aliases=["emoji", "emoj"],
        help="Emoji Search and Discovery Tool."
    )
    parser_emoji.add_argument("action", choices=["search", "list", "random"], help="Action to perform.")
    parser_emoji.add_argument("query", nargs="?", help="Search query (for 'search').")
    parser_emoji.add_argument("--limit", "-l", type=int, default=50, help="Limit results (for 'list').")

    # --- Plugin Registration ---
    try:
        # Attempt to resolve project_dir from argv early for plugin loading
        # This is a best-effort check to support project-specific plugins before full parsing
        plugin_project_dir = Path(".")
        # Simple parsing of argv to find project dir
        args_to_check = argv if argv is not None else sys.argv
        if "-p" in args_to_check:
            try:
                idx = args_to_check.index("-p") + 1
                if idx < len(args_to_check):
                    plugin_project_dir = Path(args_to_check[idx])
            except ValueError:
                pass
        if "--project-dir" in args_to_check:
            try:
                idx = args_to_check.index("--project-dir") + 1
                if idx < len(args_to_check):
                    plugin_project_dir = Path(args_to_check[idx])
            except ValueError:
                pass

        plugin_manager = PluginManager(plugin_project_dir)
        plugin_manager.load_plugins()
        plugin_manager.register_cli(subparsers)
    except Exception as e:
        # Don't crash arg parsing if plugins fail
        print(f"Warning: Failed to load plugins: {e}", file=sys.stderr)

    if argcomplete:
        argcomplete.autocomplete(parser)

    return parser.parse_args(argv)


def run_profile(args):
    """Manages configuration profiles."""
    config_dir = Path(platformdirs.user_config_dir("combined-autonomous-coding"))
    config_path = config_dir / "agent_config.yaml"
    config_dir.mkdir(parents=True, exist_ok=True)

    try:
        if config_path.exists():
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f) or {}
        else:
            config_data = {}
    except (IOError, yaml.YAMLError) as e:
        print(f"❌ Error reading configuration file: {e}", file=sys.stderr)
        sys.exit(1)

    # Ensure the 'profiles' key exists
    if 'profiles' not in config_data or not isinstance(config_data.get('profiles'), dict):
        config_data['profiles'] = {}

    action = args.action
    profile_name = args.profile_name

    # --- LIST action ---
    if action == "list":
        print("--- Available Profiles ---")
        profiles = config_data.get('profiles', {})
        if not profiles:
            print("No profiles found.")
        else:
            for name in profiles.keys():
                print(f"  - {name}")
        sys.exit(0)

    # --- SHOW action ---
    elif action == "show":
        if not profile_name:
            print("❌ Error: 'show' action requires a profile name.", file=sys.stderr)
            sys.exit(1)

        profile_data = config_data.get('profiles', {}).get(profile_name)
        if not profile_data:
            print(f"❌ Error: Profile '{profile_name}' not found.", file=sys.stderr)
            sys.exit(1)

        print(f"--- Configuration for Profile: {profile_name} ---")
        print(yaml.dump(profile_data, indent=2, sort_keys=True))
        sys.exit(0)

    # --- DELETE action ---
    elif action == "delete":
        if not profile_name:
            print("❌ Error: 'delete' action requires a profile name.", file=sys.stderr)
            sys.exit(1)

        if profile_name not in config_data.get('profiles', {}):
            print(f"❌ Error: Profile '{profile_name}' not found.", file=sys.stderr)
            sys.exit(1)

        if not args.yes:
            confirm = input(f"Are you sure you want to delete the profile '{profile_name}'? [y/N]: ").strip().lower()
            if confirm != 'y':
                print("Aborted.")
                sys.exit(0)

        del config_data['profiles'][profile_name]

        try:
            with open(config_path, 'w') as f:
                yaml.dump(config_data, f, indent=2, sort_keys=True)
            os.chmod(config_path, 0o600)
            print(f"✅ Profile '{profile_name}' deleted successfully.")
        except (IOError, yaml.YAMLError) as e:
            print(f"❌ Error writing configuration file: {e}", file=sys.stderr)
            sys.exit(1)
        sys.exit(0)

    # --- CREATE action ---
    elif action == "create":
        if not profile_name:
            print("❌ Error: 'create' action requires a profile name.", file=sys.stderr)
            sys.exit(1)

        if profile_name in config_data.get('profiles', {}):
            print(f"❌ Error: Profile '{profile_name}' already exists.", file=sys.stderr)
            sys.exit(1)

        print(f"--- Creating New Profile: {profile_name} ---")
        print("Please provide the settings for this profile. Press Enter to skip a setting.")

        # Re-use the interactive input logic from run_configure
        def get_input(prompt, default_value=None):
            if default_value:
                prompt_text = f"{prompt} [{default_value}]: "
            else:
                prompt_text = f"{prompt}: "
            user_input = input(prompt_text).strip()
            return user_input or default_value

        new_profile_data = {}

        # Core settings
        new_profile_data['model'] = get_input("Model name (e.g., gemini-1.5-pro-latest)")
        new_profile_data['agent'] = get_input("Default agent (gemini, cursor, etc.)")

        # Jira
        print("\n--- Jira Integration (optional) ---")
        jira_url = get_input("Jira URL")
        if jira_url:
            new_profile_data['jira'] = {
                'url': jira_url,
                'email': get_input("Jira Email"),
                'token': get_input("Jira API Token"),
            }

        # Clean up empty values
        new_profile_data = {k: v for k, v in new_profile_data.items() if v}

        config_data['profiles'][profile_name] = new_profile_data

        try:
            with open(config_path, 'w') as f:
                yaml.dump(config_data, f, indent=2, sort_keys=True)
            os.chmod(config_path, 0o600)
            print(f"\n✅ Profile '{profile_name}' created successfully.")
        except (IOError, yaml.YAMLError) as e:
            print(f"\n❌ Error writing configuration file: {e}", file=sys.stderr)
            sys.exit(1)
        sys.exit(0)


def run_watch(args):
    """Watches for file changes and runs a command."""
    project_dir = args.project_dir.resolve()
    command_to_run = args.watch_command

    if Observer is None:
        print("Error: watchdog library not found. Please install it with 'pip install watchdog'", file=sys.stderr)
        sys.exit(1)

    print(f"--- Watching for file changes in: {project_dir} ---")
    print(f"--- Press Ctrl+C to stop ---")

    event_handler = CommandEventHandler(command_to_run, project_dir)
    observer = Observer()
    observer.schedule(event_handler, project_dir, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    sys.exit(0)


async def run_feature(args):
    """Runs a guided workflow for creating a feature branch, committing, pushing, and creating a PR."""
    project_dir = args.project_dir.resolve()
    print("--- Guided Feature Workflow ---")
    print("This will walk you through: branch -> commit -> push -> pr.")

    # --- Pre-flight checks ---
    git_path = shutil.which("git")
    if not git_path or not (project_dir / ".git").is_dir():
        print("❌ Error: Not a git repository. Cannot start feature workflow.", file=sys.stderr)
        sys.exit(1)

    try:
        # --- Step 1: Create Branch ---
        print("\n--- [1/4] Create Branch ---")
        branch_name = input("Enter the new branch name: ").strip()
        if not branch_name:
            print("Branch name cannot be empty. Aborting.")
            sys.exit(1)

        branch_args = argparse.Namespace(
            action="create",
            branch_name=branch_name,
            project_dir=project_dir,
            keep_branch=False # Not used in create
        )
        try:
            run_branch(branch_args)
        except SystemExit as e:
            if e.code != 0:
                print("❌ Branch creation failed. Aborting workflow.", file=sys.stderr)
                sys.exit(1)

        # --- Step 2: Commit ---
        print("\n--- [2/4] Commit Changes ---")
        print("This will stage and commit all current changes.")
        commit_message = input("Enter the commit message: ").strip()
        if not commit_message:
            print("Commit message cannot be empty. Aborting.")
            sys.exit(1)

        # Note: interactive commit message generation is not enabled here as we ask for it above.
        commit_args = argparse.Namespace(
            message=commit_message,
            run_tests=False, # For simplicity, don't run tests in this guided flow
            project_dir=project_dir,
            generate=False # Disable generation in guided flow
        )
        try:
            await run_commit(commit_args)
        except SystemExit as e:
            if e.code != 0:
                print("❌ Commit failed. Aborting workflow.", file=sys.stderr)
                # We should checkout the original branch or offer to. For now, we just exit.
                sys.exit(1)

        # --- Step 3: Push ---
        print("\n--- [3/4] Push to Remote ---")
        confirm_push = input(f"Push the branch '{branch_name}' to the remote repository? [Y/n]: ").strip().lower()
        if confirm_push not in ['y', '']:
            print("Push skipped. Aborting workflow.")
            sys.exit(0)

        push_args = argparse.Namespace(project_dir=project_dir)
        try:
            run_push(push_args)
        except SystemExit as e:
            if e.code != 0:
                print("❌ Push failed. Aborting workflow.", file=sys.stderr)
                sys.exit(1)

        # --- Step 4: Create Pull Request ---
        print("\n--- [4/4] Create Pull Request ---")
        confirm_pr = input("Create a pull request on GitHub? [Y/n]: ").strip().lower()
        if confirm_pr not in ['y', '']:
            print("Pull request creation skipped.")
            print("\n✅ Workflow complete up to push.")
            sys.exit(0)

        pr_title = input(f"PR Title [{commit_message}]: ").strip() or commit_message
        pr_body = input("PR Body (optional): ").strip()
        base_branch = input("Base branch [main]: ").strip() or "main"

        pr_args = argparse.Namespace(
            action="create",
            title=pr_title,
            body=pr_body,
            base=base_branch,
            project_dir=project_dir,
            profile=getattr(args, 'profile', None)
        )

        # We need to call _pr_create directly to avoid its sys.exit() and to pass config
        file_config = load_config_from_file(profile=getattr(args, 'profile', None))
        config = argparse.Namespace(
            github_token=os.environ.get("GITHUB_TOKEN") or file_config.get("github_token"),
            github_host=file_config.get("github_host")
        )

        try:
            _pr_create(pr_args, config)
        except SystemExit as e:
            if e.code != 0:
                print("❌ Pull request creation failed.", file=sys.stderr)
                sys.exit(1)

        print("\n🎉 Feature workflow completed successfully!")
        sys.exit(0)

    except (KeyboardInterrupt, EOFError):
        print("\n\nWorkflow aborted by user.")
        sys.exit(1)


def run_review(args):
    """Runs an interactive QA review of the agent's work."""
    project_dir = args.project_dir.resolve()
    print("--- Interactive QA Review ---")
    print(f"Project Directory: {project_dir}")

    completed_file = project_dir / "COMPLETED"
    qa_passed_file = project_dir / "QA_PASSED"

    # 1. Check if there is work to review
    if not completed_file.exists():
        print("✅ No agent work is currently marked as 'COMPLETED'. Nothing to review.")
        sys.exit(0)

    if qa_passed_file.exists():
        print("✅ Agent work has already been reviewed and passed QA. Ready for manager sign-off.")
        sys.exit(0)

    print("\n[1/3] Work is marked as COMPLETED. Proceeding with review...")

    # 2. Run tests automatically
    print("\n[2/3] Running project tests...")
    test_args = argparse.Namespace(project_dir=project_dir, test_args=[])
    try:
        # We call the test function but catch SystemExit to check the result
        run_test(test_args)
    except SystemExit as e:
        if e.code != 0:
            print("\n❌ Tests failed. The agent's work is not ready for review.", file=sys.stderr)
            print("Aborting review. The agent will be notified of the test failure on its next run.", file=sys.stderr)
            # The 'COMPLETED' file is left so the agent knows it failed this step.
            sys.exit(1)

    print("✅ Tests passed successfully.")

    # 3. Show diff and ask for user approval
    print("\n[3/3] Displaying changes for review...")

    # Use existing diff logic
    try:
        diff_args = argparse.Namespace(target=None, project_dir=project_dir)
        run_diff(diff_args)
    except SystemExit:
        # run_diff will exit, which is fine. If there are no changes, it prints a message.
        pass
    except Exception as e:
        print(f"Warning: Could not display diff. {e}", file=sys.stderr)


    print("\n--- Decision ---")
    print("Do you approve these changes?")
    try:
        confirm = input("Approve and advance to manager review? [y/N]: ").strip().lower()
        if confirm == 'y':
            print("\n✅ Approved. Creating QA_PASSED file for manager review.")
            qa_passed_file.touch()
            # Optionally write a small summary
            qa_summary = f"Human QA passed at {datetime.now().isoformat()}"
            (project_dir / "qa_summary.txt").write_text(qa_summary)
            print("Workflow advanced. The Manager agent can now perform final sign-off.")
            sys.exit(0)
        else:
            print("\n❌ Rejected. Removing COMPLETED file to signal the agent to continue work.")
            completed_file.unlink()
            print("The agent will now re-evaluate the project on its next run.")
            sys.exit(0)
    except (KeyboardInterrupt, EOFError):
        print("\nReview aborted. No changes made to workflow state.")
        sys.exit(1)


async def run_generate_tests(args):
    """Generates tests for a specific file."""
    from shared.test_generator import TestGenerator

    project_dir = args.project_dir.resolve()
    target_file = Path(args.file).resolve()

    output_file = Path(args.output).resolve() if args.output else None

    generator = TestGenerator(project_dir)
    success = await generator.generate_tests(
        target_file=target_file,
        output_file=output_file,
        framework=args.framework,
        agent_type=args.agent,
        model=args.model
    )
    sys.exit(0 if success else 1)


async def run_refactor(args):
    """Refactors a file based on an instruction."""
    from shared.refactor import RefactorManager

    project_dir = args.project_dir.resolve()
    target_file = Path(args.file)
    if not target_file.is_absolute():
        target_file = project_dir / target_file

    if not target_file.exists():
        print(f"❌ Error: File '{target_file}' not found.", file=sys.stderr)
        sys.exit(1)

    manager = RefactorManager(project_dir)
    print(f"--- Refactoring {target_file.name} ---")
    print(f"Instruction: {args.instruction}")

    try:
        result = await manager.refactor_file(
            target_file=target_file,
            instruction=args.instruction,
            agent_type=args.agent,
            model=args.model
        )
    except Exception as e:
        print(f"❌ Error during refactoring: {e}", file=sys.stderr)
        sys.exit(1)

    if not result["changed"]:
        print("✅ No changes were deemed necessary by the agent.")
        sys.exit(0)

    print("\n--- Proposed Changes ---")
    print(result["diff"])

    if args.diff_only:
        sys.exit(0)

    if not args.yes:
        confirm = input("\nDo you want to apply these changes? [y/N]: ").strip().lower()
        if confirm != 'y':
            print("Aborted.")
            sys.exit(0)

    manager.apply_changes(target_file, result["new_content"])
    print(f"\n✅ Successfully updated {target_file.name}")
    sys.exit(0)


async def run_polish(args):
    """Polishes code by proactively refactoring based on metrics."""
    project_dir = args.project_dir.resolve()

    success = await run_polish_logic(
        project_dir=project_dir,
        agent_type=args.agent,
        model=args.model,
        threshold=args.threshold,
        limit=args.limit,
        yes=args.yes
    )
    sys.exit(0 if success else 1)


async def run_resolve(args):
    """Resolves a TODO item using AI."""
    from shared.resolve import run_resolve_logic

    project_dir = args.project_dir.resolve()

    success = await run_resolve_logic(
        project_dir=project_dir,
        agent_type=args.agent,
        model=args.model,
        interactive=args.interactive,
        yes=args.yes
    )
    sys.exit(0 if success else 1)


async def run_logic_lab(args):
    """Runs the Logic Lab (Truth Table Generator)."""
    from shared.logic_lab import LogicLabManager

    manager = LogicLabManager()

    if args.action == "table":
        if not args.expression:
            print("Error: --expression is required.", file=sys.stderr)
            sys.exit(1)

        result = manager.generate_truth_table(args.expression)
        if result.get("error"):
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)

        # Print table
        variables = result["variables"]
        headers = variables + ["Result"]

        # Determine column widths
        widths = [max(len(h), 5) for h in headers]

        # Header
        header_str = " | ".join(f"{h:<{w}}" for h, w in zip(headers, widths))
        print(header_str)
        print("-" * len(header_str))

        for row in result["rows"]:
            cells = []
            for var in variables:
                val = "T" if row["values"][var] else "F"
                cells.append(val)
            res = "TRUE" if row["result"] else "FALSE"
            cells.append(res)

            print(" | ".join(f"{c:<{w}}" for c, w in zip(cells, widths)))

    sys.exit(0)


async def run_regex(args):
    """Runs the Regex Lab."""
    from shared.regex_lab import RegexLabManager
    import re

    project_dir = args.project_dir.resolve()
    manager = RegexLabManager()

    if args.action == "match":
        if not args.pattern:
            print("Error: --pattern is required for 'match' action.", file=sys.stderr)
            sys.exit(1)
        if args.text is None:
             print("Error: --text is required for 'match' action.", file=sys.stderr)
             sys.exit(1)

        flags = 0
        if args.flags:
            if 'i' in args.flags: flags |= re.IGNORECASE
            if 'm' in args.flags: flags |= re.MULTILINE
            if 's' in args.flags: flags |= re.DOTALL

        result = manager.match_regex(args.pattern, args.text, flags)

        if result["success"]:
            print(f"✅ Found {result['count']} matches.")
            for m in result["matches"]:
                print(f"  Match {m['index']}: {m['full_match']!r} at {m['span']}")
                if m['groups']:
                     print(f"    Groups: {m['groups']}")
                if m['group_dict']:
                     print(f"    Named Groups: {m['group_dict']}")
        else:
            print(f"❌ Regex Error: {result['error']}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "explain":
        if not args.pattern:
            print("Error: --pattern is required for 'explain' action.", file=sys.stderr)
            sys.exit(1)

        print(f"Asking {args.agent} to explain pattern: {args.pattern}...")
        success = await manager.explain_regex(
            pattern=args.pattern,
            project_dir=project_dir,
            agent_type=args.agent,
            model=args.model
        )
        sys.exit(0 if success else 1)

    elif args.action == "generate":
        if not args.text: # reusing --text for description
             print("Error: --text (description) is required for 'generate' action.", file=sys.stderr)
             sys.exit(1)

        print(f"Asking {args.agent} to generate regex...")
        success = await manager.generate_regex(
            description=args.text,
            project_dir=project_dir,
            agent_type=args.agent,
            model=args.model
        )
        sys.exit(0 if success else 1)

    elif args.action == "game":
        from shared.regex_lab import run_regex_game_cli
        await run_regex_game_cli(
            project_dir=project_dir,
            agent_type=args.agent,
            model=args.model
        )
        sys.exit(0)

    sys.exit(0)


async def run_cron_lab(args):
    """Runs the Cron Lab."""
    from shared.cron_lab import CronLabManager

    project_dir = args.project_dir.resolve()
    manager = CronLabManager()

    if args.action == "next":
        if not args.expression:
            print("Error: --expression is required for 'next' action.", file=sys.stderr)
            sys.exit(1)

        result = manager.get_next_occurrences(args.expression, args.count)

        if result["success"]:
            print(f"✅ Next {args.count} occurrences for '{args.expression}':")
            for occ in result["occurrences"]:
                print(f"  - {occ}")
        else:
            print(f"❌ Cron Error: {result['error']}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "explain":
        if not args.expression:
            print("Error: --expression is required for 'explain' action.", file=sys.stderr)
            sys.exit(1)

        print(f"Asking {args.agent} to explain cron expression: {args.expression}...")
        success = await manager.explain_expression(
            expression=args.expression,
            project_dir=project_dir,
            agent_type=args.agent,
            model=args.model
        )
        sys.exit(0 if success else 1)

    elif args.action == "generate":
        if not args.description:
             print("Error: --description is required for 'generate' action.", file=sys.stderr)
             sys.exit(1)

        print(f"Asking {args.agent} to generate cron expression...")
        success = await manager.generate_expression(
            description=args.description,
            project_dir=project_dir,
            agent_type=args.agent,
            model=args.model
        )
        sys.exit(0 if success else 1)

    sys.exit(0)


def run_sentinel(args):
    """Runs the Sentinel auto-fix watcher."""
    project_dir = args.project_dir.resolve()
    checks = [c.strip() for c in args.checks.split(",")] if args.checks else None

    sentinel = Sentinel(
        project_dir=project_dir,
        checks=checks,
        auto_fix=args.auto_fix,
        agent_type=args.agent,
        model=args.model
    )
    sentinel.start()


async def run_resolve_conflicts(args):
    """Resolves merge conflicts using AI."""
    from shared.conflict_resolver import ConflictResolver

    project_dir = args.project_dir.resolve()
    resolver = ConflictResolver(project_dir)

    # Identify files
    files_to_resolve = []
    if args.files:
        files_to_resolve = [project_dir / f for f in args.files]
    elif args.all:
        print("Scanning for conflicted files...")
        files_to_resolve = resolver.find_conflicted_files()
    else:
        print("Error: Please specify files to resolve or use --all.")
        sys.exit(1)

    if not files_to_resolve:
        print("✅ No conflicted files found.")
        sys.exit(0)

    print(f"Found {len(files_to_resolve)} file(s) with conflicts.")

    for file_path in files_to_resolve:
        print(f"\n--- Resolving: {file_path.name} ---")
        try:
            result = await resolver.resolve_file(
                target_file=file_path,
                agent_type=args.agent,
                model=args.model
            )

            if result["resolved"]:
                print("✅ Resolution successful.")
                if args.diff:
                     import difflib
                     diff = difflib.unified_diff(
                        result["original_content"].splitlines(),
                        result["resolved_content"].splitlines(),
                        fromfile=f"a/{file_path.name}",
                        tofile=f"b/{file_path.name}",
                        lineterm=""
                     )
                     print("\n".join(diff))

                if not args.yes:
                     confirm = input("Apply changes? [y/N]: ").strip().lower()
                     if confirm != 'y':
                         print("Skipped.")
                         continue

                resolver.apply_resolution(file_path, result["resolved_content"])
                print(f"Saved changes to {file_path.name}")
            else:
                print(f"❌ Failed to resolve {file_path.name}: {result.get('message', 'Unknown error')}")

        except Exception as e:
            print(f"❌ Error processing {file_path.name}: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()

    sys.exit(0)


async def run_openapi(args):
    """Generates an OpenAPI specification."""
    from shared.openapi import OpenAPIGenerator

    project_dir = args.project_dir.resolve()
    output_path = Path(args.output).resolve()

    generator = OpenAPIGenerator(project_dir)
    success = await generator.generate(
        output_path=output_path,
        agent_type=args.agent,
        model=args.model
    )
    sys.exit(0 if success else 1)


async def run_docstring(args):
    """Manages Python docstrings."""
    from shared.docstring import DocstringManager

    project_dir = args.project_dir.resolve()
    manager = DocstringManager(project_dir)

    print(f"--- Docstring Manager in: {project_dir} ---")

    if args.action == "check":
        print("Scanning for missing docstrings...")
        items = manager.scan()
        if not items:
            print("✅ No missing docstrings found.")
            sys.exit(0)

        print(f"Found {len(items)} missing docstrings:")
        # Group by file
        items_by_file = {}
        for item in items:
            p = str(item["file"].relative_to(project_dir))
            if p not in items_by_file:
                items_by_file[p] = []
            items_by_file[p].append(item)

        for p in sorted(items_by_file.keys()):
            print(f"\n📄 {p}")
            for item in items_by_file[p]:
                print(f"  - Line {item['lineno']}: {item['type']} '{item['name']}'")

        print(f"\nTotal: {len(items)} missing.")
        sys.exit(1) # Exit 1 to indicate issues found (like lint)

    elif args.action == "generate":
        print("Scanning for missing docstrings...")
        items = manager.scan()
        if not items:
            print("✅ No missing docstrings found.")
            sys.exit(0)

        print(f"Found {len(items)} items to document.")
        if not args.yes:
            confirm = input("Do you want to generate and apply docstrings for these items? [y/N]: ").strip().lower()
            if confirm != 'y':
                print("Aborted.")
                sys.exit(0)

        print("\nStarting generation (this may take a while)...")
        count = await manager.generate_and_apply(
            items,
            agent_type=args.agent,
            model=args.model
        )
        print(f"\n✅ Successfully generated and applied {count} docstrings.")
        sys.exit(0)


def run_security(args):
    """Runs security checks on the project."""
    project_dir = args.project_dir.resolve()
    auditor = SecurityAuditor(project_dir)

    # --- Feature: Ignore Add ---
    if args.ignore_add:
        auditor.add_ignore_pattern(args.ignore_add)
        sys.exit(0)

    # --- Feature: Fix ---
    if args.fix:
        print(f"--- Running Security Fix in: {project_dir} ---")
        # If scan_type is not 'all' or 'deps', warn user
        if args.scan_type not in ["all", "deps"]:
            print("Warning: --fix currently only supports dependency vulnerabilities. Ensure --scan-type includes 'deps'.")

        print("Scanning for vulnerabilities...")
        findings = auditor.run_all(scan_type=args.scan_type, severity=args.severity)

        if not findings:
            print("✅ No vulnerabilities found to fix.")
            sys.exit(0)

        from shared.security_fix import SecurityRemediator
        remediator = SecurityRemediator(project_dir)
        results = remediator.run_remediation(findings, dry_run=args.dry_run, yes=args.yes)

        # Print summary
        print("\n--- Remediation Summary ---")
        print(f"Fixed: {len(results['fixed'])}")
        print(f"Failed: {len(results['failed'])}")
        print(f"Skipped: {len(results['skipped'])}")
        sys.exit(0 if not results['failed'] else 1)

    # --- Feature: Install Hook ---
    if args.install_hook:
        print("--- Installing Security Pre-commit Hook ---")
        from shared.config_loader import get_config_path, ensure_config_exists

        # 1. Resolve Config
        config_path = get_config_path()
        if not config_path:
            ensure_config_exists()
            config_path = get_config_path() # Should exist now

        if not config_path:
            print("❌ Error: Could not resolve configuration path.", file=sys.stderr)
            sys.exit(1)

        try:
            with open(config_path, "r") as f:
                config_data = yaml.safe_load(f) or {}

            # 2. Update Hooks Configuration
            if "git_hooks" not in config_data:
                config_data["git_hooks"] = {}
            if "pre-commit" not in config_data["git_hooks"]:
                config_data["git_hooks"]["pre-commit"] = []

            # The command we want to run
            # We use HIGH severity to block only critical leaks
            cmd = "security --scan-type secrets --severity HIGH"

            if cmd not in config_data["git_hooks"]["pre-commit"]:
                config_data["git_hooks"]["pre-commit"].append(cmd)

                # Save config
                with open(config_path, "w") as f:
                    yaml.dump(config_data, f, sort_keys=False, indent=2)
                print(f"✅ Added security check to configuration in {config_path}")
            else:
                print("ℹ️  Security check already configured in agent_config.yaml")

            # 3. Install Hooks
            # We pass the loaded config directly to install_hooks logic
            # But install_hooks takes (project_dir, hooks_config, ...)
            # So we pass the git_hooks section
            success = install_hooks(project_dir, config_data["git_hooks"])
            if success:
                print("✅ Security hook installed successfully.")
            else:
                print("❌ Failed to install security hook.", file=sys.stderr)
                sys.exit(1)

        except Exception as e:
            print(f"❌ Error configuring hook: {e}", file=sys.stderr)
            sys.exit(1)

        sys.exit(0)

    print(f"--- Running Security Audit in: {project_dir} ---")
    print(f"Scan Type: {args.scan_type}")
    print(f"Severity Threshold: {args.severity}")

    findings = auditor.run_all(scan_type=args.scan_type, severity=args.severity)

    if args.scan_history:
        print(f"Scanning git history (depth: {args.depth})...")
        history_findings = auditor.scan_git_history(depth=args.depth)
        findings.extend(history_findings)

    if args.output:
        output_path = Path(args.output)
        try:
            with open(output_path, 'w') as f:
                json.dump(findings, f, indent=2)
            print(f"\n✅ Report saved to {output_path}")
        except IOError as e:
            print(f"\n❌ Error saving report: {e}", file=sys.stderr)

    if not findings:
        print("\n✅ No security issues found.")
        sys.exit(0)

    print(f"\n⚠️  Found {len(findings)} security issue(s):")

    # Sort findings by severity (HIGH > MEDIUM > LOW > UNKNOWN)
    severity_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "UNKNOWN": 3}
    findings.sort(key=lambda x: severity_order.get(str(x.get("severity", "UNKNOWN")).upper(), 3))

    for i, finding in enumerate(findings):
        sev = str(finding.get('severity', 'UNKNOWN')).upper()
        ftype = finding.get('type', 'generic').upper()
        desc = finding.get('description', 'No description')
        file_path = finding.get('file', 'N/A')
        line = finding.get('line', 0)

        # Color coding
        sev_color = ""
        if sev == "HIGH":
            sev_color = "\033[91m" # Red
        elif sev == "MEDIUM":
            sev_color = "\033[93m" # Yellow
        elif sev == "LOW":
            sev_color = "\033[94m" # Blue
        reset = "\033[0m"

        print(f"\n[{i+1}] {sev_color}{sev}{reset} [{ftype}] {desc}")
        print(f"    File: {file_path}:{line}")
        if finding.get('commit'):
            print(f"    Commit: {finding['commit']} ({finding.get('author', 'unknown')}, {finding.get('date', 'unknown')})")
        if finding.get('snippet'):
            print(f"    Snippet: {finding['snippet'].strip()}")

    # Exit with error if high severity issues found
    if any(str(f.get('severity')).upper() == "HIGH" for f in findings):
        sys.exit(1)

    sys.exit(0)


def run_verify(args):
    """Runs verification checks (lint, type, security, tests)."""
    checks = args.check.split(",") if args.check else None
    success = run_verify_logic(
        project_dir=args.project_dir,
        checks=checks,
        fix=args.fix,
        output_format=args.output
    )
    sys.exit(0 if success else 1)


def run_cicd(args):
    """Generates CI/CD configuration files."""
    from shared.cicd import CICDGenerator

    project_dir = args.project_dir.resolve()
    print(f"--- Generating CI/CD configuration for: {project_dir} ---")

    generator = CICDGenerator(project_dir)
    project_type = generator.detect_project_type()

    if project_type == "unknown":
        print("❌ Error: Could not detect project type (Python, Node, Go).")
        sys.exit(1)

    print(f"Detected project type: {project_type}")
    print(f"Target platform: {args.platform}")

    generated_files = generator.generate(args.platform)

    if args.dry_run:
        print("\n[Dry Run] The following files would be generated:\n")
        for filename, content in generated_files.items():
            print(f"--- {filename} ---")
            print(content)
            print("-" * 20 + "\n")
        sys.exit(0)

    for filename, content in generated_files.items():
        file_path = project_dir / filename
        if file_path.exists() and not args.force:
            print(f"⚠️  Skipping {filename} (already exists). Use --force to overwrite.")
            continue

        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
            print(f"✅ Generated {filename}")
        except IOError as e:
            print(f"❌ Error writing {filename}: {e}", file=sys.stderr)

    sys.exit(0)


def run_dockerize(args):
    """Generates Docker configuration files for the project."""
    project_dir = args.project_dir.resolve()
    print(f"--- Dockerizing project in: {project_dir} ---")

    dockerizer = Dockerizer(project_dir)
    project_type = dockerizer.detect_project_type()

    if project_type == "unknown":
        print("❌ Error: Could not detect project type (Python, Node, Go).")
        print("   Ensure you have a requirements.txt, package.json, or go.mod file.")
        sys.exit(1)

    print(f"Detected project type: {project_type}")

    # Files to generate
    files_to_generate = {
        "Dockerfile": dockerizer.generate_dockerfile(project_type),
        "docker-compose.yml": dockerizer.generate_docker_compose(project_type),
        ".dockerignore": dockerizer.generate_dockerignore(project_type)
    }

    generated_files = []

    if args.dry_run:
        print("\n[Dry Run] The following files would be generated:\n")
        for filename, content in files_to_generate.items():
            print(f"--- {filename} ---")
            print(content)
            print("-" * 20 + "\n")
        sys.exit(0)

    for filename, content in files_to_generate.items():
        file_path = project_dir / filename
        if file_path.exists() and not args.force:
            print(f"⚠️  Skipping {filename} (already exists). Use --force to overwrite.")
            continue

        try:
            file_path.write_text(content)
            generated_files.append(filename)
            print(f"✅ Generated {filename}")
        except IOError as e:
            print(f"❌ Error writing {filename}: {e}", file=sys.stderr)

    if generated_files:
        print(f"\n🎉 Successfully dockerized! You can now run:")
        print(f"  docker-compose up --build")
    else:
        print("\nNo files were generated (they might already exist).")

    sys.exit(0)


def run_env(args):
    """Manages environment variables."""
    from shared.env_manager import EnvManager

    project_dir = args.project_dir.resolve()
    manager = EnvManager(project_dir)
    print(f"--- Environment Manager in: {project_dir} ---")

    if args.action == "init":
        success, msg = manager.init()
        if success:
            print(f"✅ {msg}")
        else:
            print(f"ℹ️  {msg}")

    elif args.action == "check":
        is_valid, missing_env, missing_example = manager.check()
        if is_valid:
            print("✅ .env and .env.example are in sync.")
        else:
            print("⚠️  Issues found:")
            if missing_env:
                print(f"  Missing in .env: {', '.join(missing_env)}")
            if missing_example:
                print(f"  Missing in .env.example: {', '.join(missing_example)}")
            sys.exit(1)

    elif args.action == "sync":
        print("Syncing .env and .env.example...")
        success, msg = manager.sync(interactive=args.interactive)
        print(f"✅ {msg}")

    elif args.action == "generate":
        secret = manager.generate_secret(args.key, length=args.length)
        print(f"✅ Generated secret for '{args.key}'.")
        print(f"  Value: {secret}")

    sys.exit(0)


def run_setup(args):
    """Detects the project type and installs dependencies."""
    project_dir = args.project_dir.resolve()
    print(f"--- Setting up project in: {project_dir} ---")

    command_base = []

    # 1. Node.js Project (check for lockfiles first)
    if (project_dir / "pnpm-lock.yaml").exists() and shutil.which("pnpm"):
        print("Detected pnpm project.")
        command_base = ["pnpm", "install"]
    elif (project_dir / "yarn.lock").exists() and shutil.which("yarn"):
        print("Detected yarn project.")
        command_base = ["yarn", "install"]
    elif (project_dir / "package-lock.json").exists() and shutil.which("npm"):
        print("Detected npm project.")
        command_base = ["npm", "install"]
    elif (project_dir / "package.json").exists():
        if shutil.which("pnpm"):
            print("Detected Node.js project. Using pnpm.")
            command_base = ["pnpm", "install"]
        elif shutil.which("yarn"):
            print("Detected Node.js project. Using yarn.")
            command_base = ["yarn", "install"]
        elif shutil.which("npm"):
            print("Detected Node.js project. Using npm.")
            command_base = ["npm", "install"]

    # 2. Python Project
    elif (project_dir / "requirements.txt").exists():
        print("Detected Python project.")
        command_base = [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
        # Also install dev requirements if they exist
        if (project_dir / "requirements-dev.txt").exists():
            print("Found requirements-dev.txt, installing dev dependencies...")
            dev_command = [sys.executable, "-m", "pip", "install", "-r", "requirements-dev.txt"]
            try:
                # Run this command first
                result = subprocess.run(dev_command, cwd=project_dir)
                if result.returncode != 0:
                     print(f"❌ Error installing dev dependencies. Aborting further setup.", file=sys.stderr)
                     sys.exit(result.returncode)
            except Exception as e:
                print(f"❌ An unexpected error occurred while installing dev dependencies: {e}", file=sys.stderr)
                sys.exit(1)


    # 3. Go Project
    elif (project_dir / "go.mod").exists():
        print("Detected Go project.")
        command_base = ["go", "mod", "tidy"]

    # --- Command Execution ---
    if not command_base:
        print("❌ Error: Could not detect a recognizable project type for setup.", file=sys.stderr)
        print("  Please ensure the project has a `package.json`, `requirements.txt`, or `go.mod` file.", file=sys.stderr)
        sys.exit(1)

    print(f"Executing command: {' '.join(command_base)}")
    try:
        result = subprocess.run(command_base, cwd=project_dir)
        if result.returncode == 0:
            print("✅ Setup complete.")
        else:
            print(f"❌ Setup command failed with exit code {result.returncode}.", file=sys.stderr)
        sys.exit(result.returncode)

    except FileNotFoundError:
        print(f"❌ Error: Command '{command_base[0]}' not found. Is it installed and in your PATH?", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nSetup process interrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"❌ An unexpected error occurred during setup: {e}", file=sys.stderr)
        sys.exit(1)


def run_scaffold(args):
    """Scaffolds a new project from a template."""
    from shared.scaffold import ScaffoldManager

    project_dir = args.project_dir.resolve()
    # If name is provided, append it to project_dir
    if args.name:
        project_dir = project_dir / args.name

    manager = ScaffoldManager(project_dir)

    if args.action == "list":
        templates = manager.list_templates()
        print("--- Available Templates ---")
        for name, desc in templates.items():
            print(f"  {name:<15} : {desc}")
        sys.exit(0)

    elif args.action == "create":
        success = manager.scaffold(args.template, force=args.force)
        sys.exit(0 if success else 1)


async def run_interact(args):
    """Starts an interactive session to guide the user through common commands."""
    import inspect
    project_dir = args.project_dir.resolve()
    print("--- Interactive Session ---")
    print(f"Project Directory: {project_dir}")
    print("Type a number to select a command, or 'q' to quit.")

    # A map of menu items to the function and args they will call
    menu_items = {
        "1": {"text": "Show project status", "func": run_status, "args": {"project_dir": project_dir}},
        "2": {"text": "Run tests", "func": run_test, "args": {"project_dir": project_dir, "test_args": []}},
        "3": {"text": "Run linter", "func": run_lint, "args": {"project_dir": project_dir, "fix": False, "lint_args": []}},
        "4": {"text": "Format code", "func": run_format, "args": {"project_dir": project_dir, "check": False, "format_args": []}},
        "5": {"text": "Commit changes", "func": run_commit}, # Special handling
        "6": {"text": "Suggest next step", "func": run_suggest, "args": {"project_dir": project_dir}},
    }

    while True:
        print("\n--- Main Menu ---")
        for key, value in menu_items.items():
            print(f"  [{key}] {value['text']}")
        print("  [q] Quit")

        try:
            choice = input("> ").strip().lower()
            if choice == 'q':
                print("Exiting interactive session.")
                break

            if choice in menu_items:
                item = menu_items[choice]
                print(f"\n--- Running: {item['text']} ---")
                try:
                    # Special handling for commit as it requires a message
                    if item["func"] == run_commit:
                        message = input("Enter commit message: ").strip()
                        if message:
                            # Construct the args namespace for the command
                            commit_args = argparse.Namespace(
                                message=message,
                                run_tests=False,
                                project_dir=project_dir,
                                generate=False
                            )
                            await run_commit(commit_args)
                        else:
                            print("Commit message cannot be empty. Aborting.")
                    else:
                        # Construct the args namespace for the command
                        command_args = argparse.Namespace(**item["args"])
                        if inspect.iscoroutinefunction(item["func"]):
                            await item["func"](command_args)
                        else:
                            item["func"](command_args)
                except SystemExit as e:
                    if e.code != 0:
                        print(f"--- Command finished with an error (exit code: {e.code}) ---", file=sys.stderr)
                    else:
                        print(f"--- Command finished successfully ---")
                except Exception as e:
                    print(f"An unexpected error occurred: {e}", file=sys.stderr)
            else:
                print("Invalid choice, please try again.")

        except (KeyboardInterrupt, EOFError):
            print("\nExiting interactive session.")
            break
    sys.exit(0)


def run_push(args):
    """Handles the git push command with safety checks."""
    import shutil
    import subprocess

    project_dir = args.project_dir.resolve()
    print(f"--- Pushing feature branch in: {project_dir} ---")

    # --- Pre-flight checks ---
    git_path = shutil.which("git")
    if not git_path:
        print("❌ Error: 'git' command not found. Please ensure Git is installed and in your PATH.", file=sys.stderr)
        sys.exit(1)

    git_dir = project_dir / ".git"
    if not git_dir.exists() or not git_dir.is_dir():
        print("❌ Error: Not a git repository. Cannot push.", file=sys.stderr)
        sys.exit(1)

    try:
        # Check for uncommitted changes
        status_result = subprocess.run(
            [git_path, "-C", str(project_dir), "status", "--porcelain"],
            capture_output=True, text=True, check=True
        )
        if status_result.stdout.strip():
            print("❌ Error: You have uncommitted changes. Please commit or stash them before pushing.", file=sys.stderr)
            sys.exit(1)

        # 1. Get the current branch name
        from shared.git import get_current_branch
        branch_name = get_current_branch(project_dir)

        if not branch_name:
            print("❌ Error: Could not determine the current branch name.", file=sys.stderr)
            sys.exit(1)

        print(f"Current branch is '{branch_name}'.")

        # 2. Safety check for restricted branches
        restricted_branches = ["main", "master"]
        if branch_name.lower() in restricted_branches:
            print(f"❌ Error: Pushing directly to the protected branch '{branch_name}' is not allowed.", file=sys.stderr)
            print("Please create a feature branch to push your changes.", file=sys.stderr)
            sys.exit(1)

        # 3. Execute the push command
        print(f"Pushing branch '{branch_name}' to remote 'origin'...")
        push_cmd = [git_path, "-C", str(project_dir), "push", "-u", "origin", branch_name]

        # We stream the output directly to the user's console
        push_result = subprocess.run(push_cmd, text=True)

        if push_result.returncode == 0:
            print("\n✅ Push successful.")
            sys.exit(0)
        else:
            print(f"\n❌ Git push command failed with exit code {push_result.returncode}.", file=sys.stderr)
            # Git's own error messages will be printed to stderr by subprocess.run
            sys.exit(push_result.returncode)

    except subprocess.CalledProcessError as e:
        stderr = e.stderr.strip() if e.stderr else str(e)
        print(f"❌ An error occurred: {stderr}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)


def run_pull(args):
    """Handles the git pull command with safety checks."""
    import shutil
    import subprocess

    project_dir = args.project_dir.resolve()
    print(f"--- Pulling latest changes in: {project_dir} ---")

    # --- Pre-flight checks ---
    git_path = shutil.which("git")
    if not git_path:
        print("❌ Error: 'git' command not found. Please ensure Git is installed and in your PATH.", file=sys.stderr)
        sys.exit(1)

    git_dir = project_dir / ".git"
    if not git_dir.exists() or not git_dir.is_dir():
        print("❌ Error: Not a git repository. Cannot pull.", file=sys.stderr)
        sys.exit(1)

    try:
        # Check for uncommitted changes
        status_result = subprocess.run(
            [git_path, "-C", str(project_dir), "status", "--porcelain"],
            capture_output=True, text=True, check=True
        )
        if status_result.stdout.strip():
            print("❌ Error: You have uncommitted changes. Please commit or stash them before pulling.", file=sys.stderr)
            sys.exit(1)

        # Execute the pull command
        print(f"Pulling latest changes...")
        pull_cmd = [git_path, "-C", str(project_dir), "pull"]

        # We stream the output directly to the user's console
        pull_result = subprocess.run(pull_cmd, text=True)

        if pull_result.returncode == 0:
            print("\n✅ Pull successful.")
            sys.exit(0)
        else:
            print(f"\n❌ Git pull command failed with exit code {pull_result.returncode}.", file=sys.stderr)
            # Git's own error messages will be printed to stderr by subprocess.run
            sys.exit(pull_result.returncode)

    except subprocess.CalledProcessError as e:
        stderr = e.stderr.strip() if e.stderr else str(e)
        print(f"❌ An error occurred: {stderr}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)


def run_patch(args):
    """Applies a patch from a file or stdin."""
    import subprocess
    import sys
    import shutil

    project_dir = args.project_dir.resolve()

    git_path = shutil.which("git")
    if not git_path:
        print("❌ Error: 'git' command not found. Please ensure Git is installed and in your PATH.", file=sys.stderr)
        sys.exit(1)

    git_dir = project_dir / ".git"
    if not git_dir.exists() or not git_dir.is_dir():
        print("❌ Error: Not a git repository. Cannot apply patch.", file=sys.stderr)
        sys.exit(1)

    cmd = [git_path, "-C", str(project_dir), "apply"]
    if args.reverse:
        cmd.append("--reverse")

    patch_content = None
    if args.patch_file:
        print(f"--- Applying patch from file: {args.patch_file} ---")
        patch_path = Path(args.patch_file)
        if not patch_path.is_file():
            print(f"❌ Error: Patch file not found at '{patch_path}'", file=sys.stderr)
            sys.exit(1)
        try:
            patch_content = patch_path.read_text()
        except IOError as e:
            print(f"❌ Error reading patch file: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("--- Applying patch from stdin ---")
        try:
            patch_content = sys.stdin.read()
        except Exception as e:
            print(f"❌ Error reading from stdin: {e}", file=sys.stderr)
            sys.exit(1)

    if not patch_content:
        print("❌ Error: No patch content provided.", file=sys.stderr)
        sys.exit(1)

    try:
        result = subprocess.run(
            cmd,
            input=patch_content,
            text=True,
            capture_output=True
        )
        if result.returncode != 0:
            print("❌ Error applying patch:", file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            sys.exit(1)

        print("✅ Patch applied successfully.")
        sys.exit(0)

    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        stderr = getattr(e, 'stderr', str(e))
        print(f"❌ An error occurred during patch process: {stderr}", file=sys.stderr)
        sys.exit(1)


def _pr_create(args, config):
    """Helper function to create a pull request."""
    import shutil
    import subprocess
    import requests
    from shared.git import get_current_branch
    from shared.github_client import GitHubClient

    project_dir = args.project_dir.resolve()
    print(f"--- Creating Pull Request in: {project_dir} ---")

    # --- Pre-flight checks ---
    git_path = shutil.which("git")
    if not git_path or not (project_dir / ".git").is_dir():
        print("❌ Error: Not a git repository.", file=sys.stderr)
        sys.exit(1)

    if not config.github_token:
        print("❌ Error: GitHub token not found. Please set GITHUB_TOKEN environment variable or run 'configure' to set 'github_token'.", file=sys.stderr)
        sys.exit(1)

    try:
        # 1. Get current branch
        current_branch = get_current_branch(project_dir)
        if not current_branch or current_branch in ["main", "master"]:
            print("❌ Error: You must be on a feature branch to create a pull request.", file=sys.stderr)
            sys.exit(1)
        print(f"  - On branch: {current_branch}")

        # 2. Check if the branch is pushed to remote
        result = subprocess.run(
            [git_path, "-C", str(project_dir), "ls-remote", "--exit-code", "--heads", "origin", current_branch],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print("❌ Error: Your branch has not been pushed to the remote repository.", file=sys.stderr)
            print("  Please run 'push' first.", file=sys.stderr)
            sys.exit(1)

        # 3. Create GitHub client and PR
        client = GitHubClient(token=config.github_token, host=config.github_host or "github.com")
        print("  - Creating pull request...")
        pr_data = client.create_pull_request(
            project_dir=project_dir,
            title=args.title,
            body=args.body,
            head_branch=current_branch,
            base_branch=args.base
        )

        print("\n✅ Pull request created successfully!")
        print(f"   URL: {pr_data['html_url']}")

    except (subprocess.CalledProcessError, ValueError, requests.exceptions.RequestException) as e:
        print(f"❌ An error occurred: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)

    sys.exit(0)

def _pr_list(args, config):
    """Lists open pull requests."""
    from shared.github_client import GitHubClient
    if not config.github_token:
        print("❌ Error: GitHub token not found.", file=sys.stderr)
        sys.exit(1)

    client = GitHubClient(token=config.github_token, host=config.github_host or "github.com")
    try:
        prs = client.list_pull_requests(args.project_dir)
        if not prs:
            print("No open pull requests found.")
            sys.exit(0)

        print(f"--- Open Pull Requests ---")
        for pr in prs:
            print(f"#{pr['number']} {pr['title']} (by {pr['user']['login']})")
            print(f"  URL: {pr['html_url']}")
    except Exception as e:
        print(f"❌ Error listing PRs: {e}", file=sys.stderr)
        sys.exit(1)

def _pr_show(args, config):
    """Shows details of a pull request."""
    from shared.github_client import GitHubClient
    if not config.github_token:
        print("❌ Error: GitHub token not found.", file=sys.stderr)
        sys.exit(1)

    client = GitHubClient(token=config.github_token, host=config.github_host or "github.com")
    try:
        pr = client.get_pull_request(args.project_dir, args.number)
        print(f"--- PR #{pr['number']}: {pr['title']} ---")
        print(f"State: {pr['state']}")
        print(f"User: {pr['user']['login']}")
        print(f"URL: {pr['html_url']}")
        print(f"\n{pr['body']}")
    except Exception as e:
        print(f"❌ Error fetching PR: {e}", file=sys.stderr)
        sys.exit(1)

def _pr_merge(args, config):
    """Merges a pull request."""
    from shared.github_client import GitHubClient
    if not config.github_token:
        print("❌ Error: GitHub token not found.", file=sys.stderr)
        sys.exit(1)

    if not args.yes:
        confirm = input(f"Are you sure you want to merge PR #{args.number}? [y/N]: ").strip().lower()
        if confirm != 'y':
            print("Aborted.")
            sys.exit(0)

    client = GitHubClient(token=config.github_token, host=config.github_host or "github.com")
    try:
        res = client.merge_pull_request(args.project_dir, args.number)
        if res.get("merged"):
            print(f"✅ PR #{args.number} merged successfully.")
        else:
            print(f"❌ Failed to merge PR #{args.number}. Message: {res.get('message')}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Error merging PR: {e}", file=sys.stderr)
        sys.exit(1)

def _pr_close(args, config):
    """Closes a pull request."""
    from shared.github_client import GitHubClient
    if not config.github_token:
        print("❌ Error: GitHub token not found.", file=sys.stderr)
        sys.exit(1)

    if not args.yes:
        confirm = input(f"Are you sure you want to close PR #{args.number}? [y/N]: ").strip().lower()
        if confirm != 'y':
            print("Aborted.")
            sys.exit(0)

    client = GitHubClient(token=config.github_token, host=config.github_host or "github.com")
    try:
        res = client.close_pull_request(args.project_dir, args.number)
        print(f"✅ PR #{args.number} closed successfully.")
    except Exception as e:
        print(f"❌ Error closing PR: {e}", file=sys.stderr)
        sys.exit(1)

def run_pr(args):
    """Handles GitHub pull requests."""
    file_config = load_config_from_file(profile=getattr(args, 'profile', None))
    config = argparse.Namespace(
        github_token=os.environ.get("GITHUB_TOKEN") or file_config.get("github_token"),
        github_host=file_config.get("github_host")
    )

    if args.action == "create":
        _pr_create(args, config)
    elif args.action == "list":
        _pr_list(args, config)
    elif args.action == "show":
        _pr_show(args, config)
    elif args.action == "merge":
        _pr_merge(args, config)
    elif args.action == "close":
        _pr_close(args, config)
    else:
        print(f"Unknown pr action: {args.action}", file=sys.stderr)
        sys.exit(1)


async def run_i18n(args):
    """Manages Internationalization (translation, verification)."""
    # Setup logging
    logger, _ = setup_logger(name="i18n_logger", log_file=None, verbose=args.verbose, console_output=True)

    success = await run_i18n_logic(
        action=args.action,
        project_dir=args.project_dir,
        source=args.source,
        langs=args.langs,
        agent_type=args.agent,
        model=args.model
    )
    sys.exit(0 if success else 1)


def run_dataset(args):
    """Generates a fine-tuning dataset from agent history."""
    from shared.dataset import DatasetGenerator

    project_dir = args.project_dir.resolve()
    generator = DatasetGenerator(project_dir)

    # Output defaults to project root if not absolute
    output_file = Path(args.output)
    if not output_file.is_absolute():
        output_file = project_dir / output_file

    if args.action == "generate":
        generator.generate(
            output_file=output_file,
            run_id=args.run_id,
            all_runs=args.all
        )
    sys.exit(0)


def run_snippets(args):
    """Manages code snippets."""
    from shared.snippets import SnippetManager

    project_dir = args.project_dir.resolve()
    manager = SnippetManager(project_dir)

    if args.action == "list":
        snippets = manager.list_snippets()
        if not snippets:
            print("No snippets found.")
        else:
            print("--- Snippets ---")
            for s in snippets:
                print(f"  - {s}")

    elif args.action == "show":
        if not args.name:
            print("Error: Name required.", file=sys.stderr)
            sys.exit(1)
        content = manager.get_snippet(args.name)
        if content is None:
            print(f"Snippet '{args.name}' not found.", file=sys.stderr)
            sys.exit(1)
        print(content)

    elif args.action == "add":
        if not args.name or not args.file:
            print("Error: Name and File required.", file=sys.stderr)
            sys.exit(1)

        source_path = Path(args.file)
        if not source_path.exists():
            print(f"Error: File '{args.file}' not found.", file=sys.stderr)
            sys.exit(1)

        content = source_path.read_text(encoding="utf-8", errors="replace")
        manager.create_snippet(args.name, content)
        print(f"✅ Snippet '{args.name}' created from {args.file}")

    elif args.action == "create":
        if not args.name:
            print("Error: Name required.", file=sys.stderr)
            sys.exit(1)

        print(f"Enter content for snippet '{args.name}' (Press Ctrl+D to finish):")
        try:
            content = sys.stdin.read()
            manager.create_snippet(args.name, content)
            print(f"\n✅ Snippet '{args.name}' created.")
        except KeyboardInterrupt:
            print("\nAborted.")
            sys.exit(1)

    elif args.action == "apply":
        if not args.name or not args.target:
            print("Error: Name and Target file required.", file=sys.stderr)
            sys.exit(1)

        target_path = Path(args.target)
        if manager.apply_snippet(args.name, target_path, mode=args.mode):
            print(f"✅ Snippet '{args.name}' applied to {args.target}")
        else:
            print(f"Error: Snippet '{args.name}' not found.", file=sys.stderr)
            sys.exit(1)

    elif args.action == "delete":
        if not args.name:
            print("Error: Name required.", file=sys.stderr)
            sys.exit(1)

        if manager.delete_snippet(args.name):
            print(f"✅ Snippet '{args.name}' deleted.")
        else:
            print(f"Snippet '{args.name}' not found.", file=sys.stderr)
            sys.exit(1)

    sys.exit(0)


def run_frontend(args):
    """Runs frontend verification tools."""
    from shared.frontend import FrontendVerifier

    project_dir = args.project_dir.resolve()
    verifier = FrontendVerifier(project_dir)

    if args.action == "snapshot":
        if not args.url or not args.name:
            print("Error: --url and --name required for snapshot.")
            sys.exit(1)
        path = verifier.capture_snapshot(args.url, args.name, is_baseline=args.baseline)
        if path:
            print(f"✅ Snapshot saved: {path}")
        else:
            print("❌ Snapshot failed.")
            sys.exit(1)

    elif args.action == "verify":
        if not args.url or not args.name:
             print("Error: --url and --name required for verify.")
             sys.exit(1)

        # First capture current
        print(f"Capturing current state of {args.url}...")
        current_path = verifier.capture_snapshot(args.url, args.name, is_baseline=False)
        if not current_path:
            print("❌ Capture failed.")
            sys.exit(1)

        # Then verify
        result = verifier.verify(args.name)
        if result["success"]:
            if result["match"]:
                print(f"✅ Verification Passed! (Score: {result['diff_score']:.4f})")
            else:
                print(f"❌ Verification Failed. (Score: {result['diff_score']:.4f})")
                print(f"   Diff saved to: {result['diff_path']}")
                sys.exit(1)
        else:
            print(f"Error: {result.get('error')}")
            sys.exit(1)

    elif args.action == "list":
        baselines = verifier.list_baselines()
        if baselines:
            print("--- Frontend Baselines ---")
            for b in baselines:
                print(f"  - {b}")
        else:
            print("No baselines found.")

    elif args.action == "approve":
        if not args.name:
            print("Error: --name required.")
            sys.exit(1)
        if verifier.approve_current(args.name):
            print(f"✅ Approved. Current snapshot is now the baseline for '{args.name}'.")
        else:
            print(f"❌ Failed to approve (no current snapshot found).")
            sys.exit(1)

    sys.exit(0)


def run_mock(args):
    """Manages mock data tools (generate, serve)."""
    if args.action == "serve":
        from shared.mock_server import run_mock_server
        run_mock_server(
            project_dir=args.project_dir,
            port=args.port,
            agent_type=args.agent,
            model=args.model
        )
        sys.exit(0)

    elif args.action == "generate":
        from shared.mock_data import MockDataGenerator

        schema_path = Path(args.schema)
        if not schema_path.exists():
            print(f"❌ Error: Schema file '{schema_path}' not found.", file=sys.stderr)
            sys.exit(1)

        try:
            with open(schema_path, 'r') as f:
                schema = json.load(f)
        except Exception as e:
            print(f"❌ Error parsing schema file: {e}", file=sys.stderr)
            sys.exit(1)

        try:
            generator = MockDataGenerator(schema)
            data = generator.generate(count=args.count)
            output_content = generator.export(data, format=args.format, table_name=args.table_name)
        except Exception as e:
             print(f"❌ Error generating data: {e}", file=sys.stderr)
             sys.exit(1)

        if args.output:
            try:
                with open(args.output, 'w') as f:
                    f.write(output_content)
                print(f"✅ Mock data generated to {args.output}")
            except Exception as e:
                 print(f"❌ Error writing output file: {e}", file=sys.stderr)
                 sys.exit(1)
        else:
            print(output_content)
        sys.exit(0)


async def run_commit(args):
    """Handles the git commit command with safety checks."""
    import shutil
    import subprocess

    project_dir = args.project_dir.resolve()
    commit_message = args.message

    # --- Pre-flight checks ---
    git_path = shutil.which("git")
    if not git_path:
        print("❌ Error: 'git' command not found. Please ensure Git is installed and in your PATH.", file=sys.stderr)
        sys.exit(1)

    git_dir = project_dir / ".git"
    if not git_dir.exists() or not git_dir.is_dir():
        print("❌ Error: Not a git repository. Cannot commit.", file=sys.stderr)
        sys.exit(1)

    # --- Run tests if requested ---
    if args.run_tests:
        print("--- Running tests before commit ---")
        test_args = argparse.Namespace(project_dir=project_dir, test_args=[])
        try:
            run_test(test_args)
        except SystemExit as e:
            if e.code != 0:
                print("\n❌ Tests failed. Commit aborted.", file=sys.stderr)
                sys.exit(1)
        print("✅ Tests passed. Proceeding with commit.")

    # --- Stage all changes ---
    print("--- Staging all changes ---")
    try:
        subprocess.run([git_path, "-C", str(project_dir), "add", "-A"], check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error staging files: {e.stderr}", file=sys.stderr)
        sys.exit(1)

    # --- Check if there's anything to commit ---
    check_staged_result = subprocess.run([git_path, "-C", str(project_dir), "diff", "--cached", "--quiet"], capture_output=True)
    if check_staged_result.returncode == 0:
        print("✅ No changes staged for commit.")
        sys.exit(0)

    # --- AI Commit Message Generation ---
    if args.generate and not commit_message:
        print("--- Generating Commit Message with AI ---")
        commit_message = await generate_commit_message_logic(
            project_dir,
            agent_type=args.agent if hasattr(args, 'agent') else "gemini",
            model=args.model if hasattr(args, 'model') else None
        )
        if not commit_message:
            print("❌ Failed to generate commit message.")
            if args.yes:
                sys.exit(1)
        else:
            print("\n--- Generated Commit Message ---")
            print(commit_message)
            print("------------------------------")
            if not args.yes:
                confirm = input("Use this message? [Y/n]: ").strip().lower()
                if confirm not in ['y', '']:
                    print("Aborted. Falling back to interactive mode.")
                    commit_message = None # Fallback

    # --- Interactive Commit Message Generation ---
    if not commit_message:
        try:
            print("--- Interactive Commit ---")
            print("Please provide the details for your commit message.")

            commit_type = input("Commit type (e.g., feat, fix, chore, docs): ").strip()
            while not commit_type:
                print("Commit type cannot be empty.")
                commit_type = input("Commit type: ").strip()

            scope = input("Scope (optional, e.g., cli, agent): ").strip()
            short_description = input("Short description (max 72 chars): ").strip()
            while not short_description:
                print("Short description cannot be empty.")
                short_description = input("Short description: ").strip()

            body = input("Body (optional, press Enter to skip): ").strip()
            is_breaking_change = input("Is this a breaking change? [y/N]: ").strip().lower() == 'y'
            breaking_change_description = ""
            if is_breaking_change:
                breaking_change_description = input("Describe the breaking change: ").strip()

            # Assemble the commit message
            header = f"{commit_type}"
            if scope:
                header += f"({scope})"
            header += f": {short_description}"

            commit_message = header
            if body:
                commit_message += f"\n\n{body}"
            if breaking_change_description:
                commit_message += f"\n\nBREAKING CHANGE: {breaking_change_description}"

            print("\n--- Generated Commit Message ---")
            print(commit_message)
            print("------------------------------")
            confirm = input("Confirm commit? [Y/n]: ").strip().lower()
            if confirm not in ['y', '']:
                print("Commit aborted.")
                sys.exit(0)

        except (KeyboardInterrupt, EOFError):
            print("\nCommit aborted by user.")
            sys.exit(1)

    # --- Create the commit ---
    print(f"--- Creating commit ---")
    try:
        commit_cmd = [git_path, "-C", str(project_dir), "commit", "-m", commit_message]
        commit_result = subprocess.run(commit_cmd, check=True, capture_output=True, text=True)
        print(commit_result.stdout.strip())
        print("\n✅ Commit created successfully.")
        sys.exit(0)
    except subprocess.CalledProcessError as e:
        print(f"❌ Git commit command failed:", file=sys.stderr)
        print(e.stdout, file=sys.stderr)
        print(e.stderr, file=sys.stderr)
        sys.exit(e.returncode)


def _worktree_merge(args, git_path, project_dir, worktrees_base_dir):
    """Helper function to merge a worktree branch back into the main branch."""
    import subprocess

    if not args.worktree_name:
        print("❌ Error: 'merge' action requires a worktree name.", file=sys.stderr)
        sys.exit(1)

    worktree_name = args.worktree_name
    manager = WorktreeManager(project_dir)

    worktrees = manager.list_worktrees()
    target = next((w for w in worktrees if w.get("name") == worktree_name), None)
    if not target:
        print(f"❌ Error: Worktree '{worktree_name}' not found.", file=sys.stderr)
        sys.exit(1)

    branch_ref = target.get("branch", "")
    branch_name = branch_ref.replace("refs/heads/", "")

    print(f"--- Merging worktree: {worktree_name} ---")
    print(f"  - Found worktree branch: {branch_name}")

    # Checkout main branch
    main_branch = "main"
    print(f"  - Checking out '{main_branch}' branch in main repository...")
    try:
        subprocess.run(
            [git_path, "-C", str(project_dir), "checkout", main_branch],
            check=True, capture_output=True, text=True
        )
    except subprocess.CalledProcessError as e:
        if "did not match any file(s) known to git" in e.stderr:
             main_branch = "master" # Fallback to master
             print(f"  - '{main_branch}' not found, trying 'master'...")
             try:
                 subprocess.run(
                     [git_path, "-C", str(project_dir), "checkout", main_branch],
                     check=True, capture_output=True, text=True
                 )
             except subprocess.CalledProcessError as e2:
                 stderr = e2.stderr.strip()
                 print(f"❌ Error checking out '{main_branch}': {stderr}", file=sys.stderr)
                 sys.exit(1)
        else:
             stderr = e.stderr.strip()
             print(f"❌ Error checking out '{main_branch}': {stderr}", file=sys.stderr)
             sys.exit(1)

    print(f"  - Merging branch '{branch_name}' into '{main_branch}'...")
    try:
        output = manager.merge(worktree_name)
        print("  - Merge successful.")
        print("\n--- Merge Output ---")
        print(output.strip())
        print("--------------------")
    except Exception as e:
        print(f"❌ Error merging branch: {e}", file=sys.stderr)
        sys.exit(1)

    # 4. Optionally clean up the worktree and branch
    if args.clean:
        print("\n--- Cleaning up worktree and branch ---")
        if not args.yes:
            confirm = input(f"This will remove the worktree '{worktree_name}' and delete the branch '{branch_name}'. Are you sure? [y/N]: ").strip().lower()
            if confirm != 'y':
                print("Cleanup aborted. Worktree and branch preserved.")
                print("\n✅ Merge complete.")
                sys.exit(0)

        # Remove worktree
        try:
            print(f"  - Removing worktree '{worktree_name}'...")
            manager.remove(worktree_name)
            print(f"  - Successfully removed worktree.")
        except Exception as e:
            print(f"❌ Error removing worktree: {e}", file=sys.stderr)

        # Delete branch
        try:
            print(f"  - Deleting branch '{branch_name}'...")
            subprocess.run(
                [git_path, "-C", str(project_dir), "branch", "-d", branch_name],
                check=True, capture_output=True, text=True
            )
            print(f"  - Successfully deleted branch.")
        except subprocess.CalledProcessError as e:
            stderr = e.stderr.strip()
            print(f"❌ Error deleting branch: {stderr}", file=sys.stderr)
            sys.exit(1)

        print("\n✅ Merge and cleanup complete.")
    else:
        print("\n✅ Merge complete. Worktree and branch preserved.")

    sys.exit(0)


def _worktree_diff(args, git_path, worktrees_base_dir):
    """Helper function to show a diff of the worktree against the main repo's HEAD."""
    if not args.worktree_name:
        print("❌ Error: 'diff' action requires a worktree name.", file=sys.stderr)
        sys.exit(1)

    project_dir = args.project_dir.resolve()
    manager = WorktreeManager(project_dir)

    worktree_name = args.worktree_name
    path = manager.worktrees_dir / worktree_name
    if not path.is_dir():
        print(f"❌ Error: Worktree '{worktree_name}' not found at '{path}'.", file=sys.stderr)
        sys.exit(1)

    print(f"--- Diff for worktree: {worktree_name} (compared to main repo HEAD) ---")

    diff_output = manager.diff(worktree_name)
    if diff_output.startswith("Error"):
        print(f"❌ {diff_output}", file=sys.stderr)
        sys.exit(1)

    if not diff_output.strip():
        print("✅ No changes detected. Worktree is in sync with HEAD.")
    else:
        print(diff_output)

    sys.exit(0)


def _worktree_show_logic(args, git_path, project_dir, worktrees_base_dir):
    """Helper function to show a comprehensive dashboard for a worktree."""
    import json

    if not args.worktree_name:
        print("❌ Error: 'show' action requires a worktree name.", file=sys.stderr)
        return False

    worktree_name = args.worktree_name
    manager = WorktreeManager(project_dir)
    worktree_path = (worktrees_base_dir / worktree_name).resolve()

    if not worktree_path.is_dir():
        print(f"❌ Error: Worktree '{worktree_name}' not found at '{worktree_path}'.", file=sys.stderr)
        return False

    print(f"--- Dashboard for Worktree: {worktree_name} ---")

    # 1. Get Core Information
    branch_name = "N/A"
    worktrees = manager.list_worktrees()
    target = next((w for w in worktrees if w.get("name") == worktree_name), None)
    if target:
        branch_ref = target.get("branch", "")
        branch_name = branch_ref.replace("refs/heads/", "")

    print(f"  Path:   {worktree_path}")
    print(f"  Branch: {branch_name}")

    # 2. Get Sprint Task Context
    sprint_plan_path = project_dir / "sprint_plan.json"
    if sprint_plan_path.exists():
        try:
            with open(sprint_plan_path, 'r') as f:
                plan = json.load(f)
            tasks = plan.get("tasks", [])
            # Assuming worktree name is sprint-task-<id>
            if "sprint-task-" in worktree_name:
                task_id = worktree_name.split("sprint-task-")[-1]
                task = next((t for t in tasks if t.get("id") == task_id), None)
                if task:
                    print("\n--- Sprint Task Info ---")
                    print(f"  Title: {task.get('title', 'N/A')}")
                    print(f"  Description: {task.get('description', 'N/A')}")
        except (json.JSONDecodeError, IOError) as e:
            print(f"❌ Warning: Could not read or parse sprint_plan.json: {e}", file=sys.stderr)

    # 3. Get Git Status
    print("\n--- Git Status ---")
    status = manager.get_status(worktree_name)
    if status.strip():
        print("  Uncommitted changes:")
        for line in status.strip().split('\n'):
            print(f"    {line}")
    else:
        print("  ✅ Worktree is clean (no uncommitted changes).")

    # 4. Get Diff Summary
    print("\n--- Diff Summary (vs HEAD) ---")
    try:
        # Use private method for flexibility to get stat
        res = manager._run_git(["diff", "--stat", "HEAD"], cwd=worktree_path)
        if not res.stdout.strip():
            print("  ✅ No differences with HEAD.")
        else:
            for line in res.stdout.strip().split('\n'):
                print(f"  {line.strip()}")
    except Exception as e:
        print(f"❌ Error getting diff: {e}")

    return True


def _worktree_show(args, git_path, project_dir, worktrees_base_dir):
    """Entry point for the 'show' command that calls the logic and exits."""
    success = _worktree_show_logic(args, git_path, project_dir, worktrees_base_dir)
    sys.exit(0 if success else 1)


def _worktree_manage(args, git_path, project_dir, worktrees_base_dir):
    """Helper function for interactive worktree management."""
    manager = WorktreeManager(project_dir)

    # 1. Get the list of worktrees
    worktrees = manager.list_worktrees()
    if not worktrees:
        print("No active agent worktrees found to manage.")
        sys.exit(0)

    # 2. Prompt user to select a worktree
    print("--- Interactive Worktree Management ---")
    print("Please select a worktree to manage:")
    for i, wt in enumerate(worktrees):
        branch = wt.get('branch', 'detached HEAD').split('/')[-1]
        print(f"  [{i+1}] {wt['name']} (branch: {branch})")

    selected_worktree = None
    while True:
        try:
            selection = input(f"Enter number (1-{len(worktrees)}), or press Enter to cancel: ").strip()
            if not selection:
                print("Aborted.")
                sys.exit(0)
            choice_index = int(selection) - 1
            if 0 <= choice_index < len(worktrees):
                selected_worktree = worktrees[choice_index]['name']
                break
            else:
                print("Invalid selection. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")
        except (EOFError, KeyboardInterrupt):
            print("\nAborted.")
            sys.exit(0)

    print(f"\nManaging worktree: {selected_worktree}")

    # 3. Display menu and get action
    actions = ["show", "diff", "merge", "revert", "clean"]
    while True:
        print("\nAvailable actions:")
        for i, action in enumerate(actions):
            print(f"  [{i+1}] {action.capitalize()}")

        try:
            action_selection = input(f"Select an action (1-{len(actions)}), or press Enter to exit: ").strip()
            if not action_selection:
                print("Exiting.")
                sys.exit(0)
            action_index = int(action_selection) - 1
            if 0 <= action_index < len(actions):
                selected_action = actions[action_index]
                break
            else:
                print("Invalid selection. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            sys.exit(0)

    # 4. Execute the action
    mock_args = argparse.Namespace(
        worktree_name=selected_worktree,
        project_dir=project_dir,
        yes=False,
        force=False,
        clean=False,
    )

    print(f"\n--- Executing '{selected_action.upper()}' on '{selected_worktree}' ---")

    if selected_action == "show":
        status = manager.get_status(selected_worktree)
        if status.strip():
            print("Uncommitted changes:")
            for line in status.strip().split('\n'):
                print(f"  {line}")
        else:
            print("✅ Worktree is clean.")

    elif selected_action == "diff":
        _worktree_diff(mock_args, git_path, worktrees_base_dir)

    elif selected_action == "merge":
        print("For merge, you can choose to clean up the worktree afterwards.")
        clean_choice = input("Clean up worktree and branch after successful merge? [y/N]: ").strip().lower()
        mock_args.clean = (clean_choice == 'y')
        _worktree_merge(mock_args, git_path, project_dir, worktrees_base_dir)

    elif selected_action == "revert":
        status = manager.get_status(selected_worktree)
        if not status.strip():
            print("✅ No uncommitted changes to revert.")
        else:
            print("\nUncommitted changes (will be discarded):")
            for line in status.strip().split('\n'):
                print(f"  {line}")

            confirm = input("\nAre you sure you want to discard ALL uncommitted changes in this worktree? [y/N]: ").strip().lower()
            if confirm == 'y':
                 print("\nReverting changes...")
                 try:
                     manager.revert(selected_worktree)
                     print("✅ Revert complete. Worktree is now clean.")
                 except Exception as e:
                     print(f"❌ Error during revert: {e}", file=sys.stderr)
            else:
                print("Aborted.")

    elif selected_action == "clean":
        print("This will remove the worktree. This can be forced if there are uncommitted changes.")
        force_choice = input("Force removal even with uncommitted changes? [y/N]: ").strip().lower()
        mock_args.force = (force_choice == 'y')
        confirm = input(f"Are you sure you want to remove the worktree '{selected_worktree}'? [y/N]: ").strip().lower()
        if confirm == 'y':
            try:
                manager.remove(selected_worktree, force=mock_args.force)
                print(f"✅ Removed worktree: {selected_worktree}")
            except Exception as e:
                 print(f"❌ Error removing worktree '{selected_worktree}': {e}", file=sys.stderr)
        else:
            print("Aborted.")

    sys.exit(0)


def run_sanitize(args):
    """Sanitizes PII from files or text."""
    from shared.sanitizer import Sanitizer

    sanitizer = Sanitizer()

    if args.action == "text":
        if not args.text:
            print("Error: --text is required.")
            sys.exit(1)
        result = sanitizer.sanitize_text(args.text)
        print(result)

    elif args.action == "file":
        if not args.file:
            print("Error: --file is required.")
            sys.exit(1)

        path = Path(args.file)
        out_path = Path(args.output) if args.output else None

        changed, msg = sanitizer.sanitize_file(path, out_path, dry_run=args.dry_run)

        if changed:
            if args.dry_run:
                print(f"⚠️  {msg}")
            else:
                print(f"✅ {msg}")
        else:
            print(f"✅ {msg}")

    elif args.action == "check":
        if args.text:
            detected = sanitizer.check_text(args.text)
            if detected:
                print(f"⚠️  PII Detected: {', '.join(detected)}")
                sys.exit(1)
            else:
                print("✅ No PII detected.")
        elif args.file:
            path = Path(args.file)
            if not path.exists():
                print(f"Error: {path} not found.")
                sys.exit(1)
            content = path.read_text(encoding="utf-8", errors="ignore")
            detected = sanitizer.check_text(content)
            if detected:
                print(f"⚠️  PII Detected in {path.name}: {', '.join(detected)}")
                sys.exit(1)
            else:
                print(f"✅ No PII detected in {path.name}.")
        else:
            print("Error: --text or --file required for check.")
            sys.exit(1)

    sys.exit(0)


def run_worktrees(args):
    """Manages agent-created git worktrees."""
    project_dir = args.project_dir.resolve()
    worktrees_base_dir = project_dir / "worktrees"

    # Pre-flight checks are somewhat handled by WorktreeManager or shared.git, but keeping for safety.
    git_path = shutil.which("git")
    if not git_path:
        print("❌ Error: 'git' command not found.", file=sys.stderr)
        sys.exit(1)

    if not (project_dir / ".git").exists():
        print("❌ Error: Not a git repository. Cannot manage worktrees.", file=sys.stderr)
        sys.exit(1)

    manager = WorktreeManager(project_dir)

    # --- Action: create ---
    if args.action == "create":
        if not args.worktree_name:
            print("❌ Error: 'create' action requires a worktree name.", file=sys.stderr)
            sys.exit(1)

        # If branch is not specified, it defaults to the worktree name
        branch_name = args.branch if args.branch else args.worktree_name

        print(f"--- Creating new worktree: {args.worktree_name} ---")
        print(f"  Branch:    {branch_name}")

        try:
            manager.create(args.worktree_name, branch=branch_name)
            print(f"\n✅ Successfully created worktree '{args.worktree_name}' on branch '{branch_name}'.")
        except Exception as e:
            print(f"❌ Error creating worktree: {e}", file=sys.stderr)
            sys.exit(1)
        sys.exit(0)

    # --- Action: list ---
    elif args.action == "list":
        print(f"--- Listing Agent Worktrees in: {worktrees_base_dir} ---")
        worktrees = manager.list_worktrees()

        if not worktrees:
            print("No active agent worktrees found.")
            sys.exit(0)

        for wt in worktrees:
            branch = wt.get('branch', 'detached HEAD').split('/')[-1]
            print(f"  - {wt['name']} (branch: {branch})")
        sys.exit(0)

    # --- Action: show ---
    elif args.action == "show":
        _worktree_show(args, None, project_dir, worktrees_base_dir)

    # --- Action: revert ---
    elif args.action == "revert":
        if not args.worktree_name:
            print("❌ Error: 'revert' action requires a worktree name.", file=sys.stderr)
            sys.exit(1)

        print(f"--- Reverting uncommitted changes in worktree: {args.worktree_name} ---")
        status = manager.get_status(args.worktree_name)
        if not status.strip():
            print("✅ No uncommitted changes to revert.")
            sys.exit(0)

        print("\nUncommitted changes (will be discarded):")
        for line in status.strip().split('\n'):
            print(f"  {line}")

        if not args.yes:
            confirm = input("\nAre you sure you want to discard ALL uncommitted changes in this worktree? [y/N]: ").strip().lower()
            if confirm != 'y':
                print("Aborted.")
                sys.exit(0)

        print("\nReverting changes...")
        try:
            manager.revert(args.worktree_name)
            print("✅ Revert complete. Worktree is now clean.")
        except Exception as e:
            print(f"❌ Error during revert: {e}", file=sys.stderr)
            sys.exit(1)
        sys.exit(0)

    # --- Action: merge ---
    elif args.action == "merge":
        _worktree_merge(args, git_path, project_dir, worktrees_base_dir)

    # --- Action: diff ---
    elif args.action == "diff":
        _worktree_diff(args, git_path, worktrees_base_dir)

    # --- Action: manage (interactive) ---
    elif args.action == "manage":
        _worktree_manage(args, git_path, project_dir, worktrees_base_dir)

    # --- Action: clean ---
    elif args.action == "clean":
        worktrees_to_clean = []
        if args.worktree_name:
            if not (worktrees_base_dir / args.worktree_name).exists():
                 print(f"❌ Error: Worktree '{args.worktree_name}' not found.", file=sys.stderr)
                 sys.exit(1)
            worktrees_to_clean.append(args.worktree_name)
        else:
            worktrees = manager.list_worktrees()
            worktrees_to_clean = [w['name'] for w in worktrees]

        if not worktrees_to_clean:
            print("No agent worktrees found to clean.")
            sys.exit(0)

        print("The following worktrees will be removed:")
        for name in worktrees_to_clean:
            print(f"  - {name}")

        if not args.yes:
            confirm = input("\nAre you sure you want to proceed? [y/N]: ").strip().lower()
            if confirm != 'y':
                print("Aborted.")
                sys.exit(0)

        print("\nCleaning worktrees...")
        for name in worktrees_to_clean:
            try:
                manager.remove(name, force=args.force)
                print(f"✅ Removed worktree: {name}")
            except Exception as e:
                print(f"❌ Error removing worktree '{name}': {e}", file=sys.stderr)
        sys.exit(0)


async def main():
    args = parse_args()

    # Handle Plugin commands
    # Use vars(args) to avoid false positives with MagicMock in tests
    if 'run_plugin_func' in vars(args):
        import inspect
        if inspect.iscoroutinefunction(args.run_plugin_func):
            await args.run_plugin_func(args)
        else:
            args.run_plugin_func(args)
        return

    # Handle `shell` command
    if args.command == "shell":
        run_shell(args)
        return

    # Handle `tui` command
    if args.command == "tui":
        run_tui(args)
        return

    if args.command == "quiz":
        run_quiz(args)
        return

    if args.command == "kata":
        run_kata(args)
        return

    # Handle `prompt-lab` command
    if args.command == "prompt-lab":
        run_prompt_lab(args)
        return

    # Handle `knowledge` command
    if args.command == "knowledge":
        run_knowledge(args)
        return

    # Handle `chat` command
    if args.command == "chat":
        await run_chat(args)
        return

    # Handle `ask` command
    if args.command == "ask":
        await run_ask(args)
        return

    # Handle `do` command
    if args.command == "do":
        await run_do(args)
        return

    # Handle `optimize` command
    if args.command == "optimize":
        await run_optimize(args)
        return

    # Handle `perf` command
    if args.command == "perf":
        run_perf(args)
        return

    # Handle `debug` command
    if args.command == "debug":
        await run_debug(args)
        return

    # Handle `code-review` command
    if args.command == "code-review":
        await run_code_review(args)
        return

    # Handle `summarize` command
    if args.command == "summarize":
        await run_summarize(args)
        return

    # Handle `explain` command
    if args.command == "explain":
        await run_explain(args)
        return

    # Handle `init` command
    if args.command == "init":
        run_init(args)
        return

    # Handle `adr` command
    if args.command == "adr":
        await run_adr(args)
        return

    # Handle `onboard` command
    if args.command == "onboard":
        run_onboard(args)
        return

    # Handle `session` command
    if args.command == "session":
        run_session(args)
        return

    # Handle `secrets` command
    if args.command == "secrets":
        run_secrets(args)
        return

    # Handle `db` command
    if args.command in ["db", "database"]:
        await run_db(args)
        return

    # Handle `playground` command
    if args.command == "playground":
        run_playground(args)
        return

    # Handle `completion` command
    if args.command == "completion":
        run_completion()
        return

    # Handle `plan` command
    if args.command == "plan":
        await run_plan(args)
        return

    # Handle `estimate` command
    if args.command == "estimate":
        await run_estimate(args)
        return

    # Handle `config` command
    if args.command == "config":
        sys.exit(run_config(args))

    # Handle `configure` command
    if args.command == "configure":
        run_configure()
        return

    # Handle `validate` command
    if args.command == "validate":
        run_validate()
        return

    # Handle `doctor` command
    if args.command == "doctor":
        run_doctor(args)
        return

    # Handle `clean` command
    if args.command == "clean":
        run_clean(args)
        return

    # Handle `prune` command
    if args.command == "prune":
        run_prune(args)
        return

    # Handle `archive` command
    if args.command == "archive":
        run_archive(args)
        return

    # Handle `empty-trash` command
    if args.command == "empty-trash":
        run_empty_trash(args)
        return

    # Handle `restore` command
    if args.command == "restore":
        run_restore(args)
        return

    # Handle `trash` command
    if args.command == "trash":
        run_trash(args)
        return

    # Handle `revert` command
    if args.command == "revert":
        run_revert(args)
        return

    # Handle `rewind` command
    if args.command == "rewind":
        run_rewind(args)
        return

    # Handle `discard` command
    if args.command == "discard":
        run_discard(args)
        return

    # Handle `undo` command
    if args.command == "undo":
        run_undo(args)
        return

    # Handle `archives' command
    if args.command == "archives":
        run_archives(args)
        return

    # Handle `artifacts` command
    if args.command == "artifacts":
        run_artifacts(args, mode=args.type)
        return

    # Handle `worktrees` command
    if args.command == "worktrees":
        run_worktrees(args)
        return

    # Handle `snapshot` command
    if args.command == "snapshot":
        run_snapshot(args)
        return

    # Handle `list-agents` command
    if args.command == "list-agents":
        run_list_agents()
        return

    # Handle `models` command
    if args.command == "models":
        run_models(args)
        return

    # Handle `glance` command
    if args.command == "glance":
        run_glance(args)
        return

    # Handle `status` command
    if args.command == "status":
        run_status(args)
        return

    # Handle `dashboard` command
    if args.command == "dashboard":
        run_dashboard(args)
        return

    # Handle `summary` command
    if args.command == "summary":
        run_summary(args)
        return

    # Handle `suggest` command
    if args.command == "suggest":
        run_suggest(args)
        return

    # Handle `tour` command
    if args.command == "tour":
        run_tour(args)
        return

    # Handle `history` command
    if args.command == "history":
        run_history(args)
        return

    if args.command == "last":
        run_last(args)
        return

    if args.command == "last-run-id":
        run_last_run_id(args)
        return

    if args.command == "diff-summary":
        run_diff_summary(args)
        return

    if args.command == "diff":
        run_diff(args)
        return

    if args.command == "log":
        run_log(args)
        return

    if args.command == "logs":
        run_logs(args)
        return

    # Handle `workflow` command
    if args.command == "workflow":
        run_workflow(args)
        return

    # Handle `cost` command
    if args.command == "cost":
        run_cost(args)
        return

    # Handle `benchmark` command
    if args.command == "benchmark":
        run_benchmark(args)
        return

    # Handle `sprint` command
    if args.command == "sprint":
        run_sprint_command(args)
        return

    if args.command == "branch":
        run_branch(args)
        return

    if args.command == "mutate":
        run_mutate(
            project_dir=args.project_dir,
            target_file=args.target_file,
            test_command=args.test_command
        )
        return

    if args.command == "test":
        run_test(args)
        return

    if args.command == "lint":
        run_lint(args)
        return

    if args.command == "format":
        run_format(args)
        return

    if args.command == "hooks":
        run_hooks(args)
        return

    if args.command == "replay":
        run_replay(args)
        return

    if args.command in ["recipes", "macro"]:
        await run_recipes(args)
        return

    if args.command == "git":
        run_git(args)
        return

    # Handle `history-graph` command
    if args.command == "history-graph":
        run_history_graph(args)
        return

    if args.command == "tree":
        run_tree(args)
        return
    if args.command == "report":
        run_report(args)
        return

    if args.command == "push":
        run_push(args)
        return

    if args.command == "pull":
        run_pull(args)
        return

    if args.command == "patch":
        run_patch(args)
        return

    if args.command == "issues":
        _run_issues_logic(args)
        return

    if args.command == "pr":
        run_pr(args)
        return

    if args.command == "commit":
        await run_commit(args)
        return

    if args.command == "feature":
        await run_feature(args)
        return

    if args.command == "interact":
        await run_interact(args)
        return

    if args.command == "profile":
        run_profile(args)
        return

    if args.command == "watch":
        run_watch(args)
        return

    if args.command == "why":
        run_why(args)
        return

    if args.command == "blame":
        run_blame(args)
        return

    if args.command == "stash":
        run_stash(args)
        return

    if args.command == "next":
        run_next(args)
        return

    if args.command == "context":
        run_context(args)
        return

    if args.command == "search":
        run_search(args)
        return

    if args.command in ["smart-search", "ssearch"]:
        run_smart_search(args)
        return

    if args.command == "replace":
        run_replace(args)
        return

    if args.command == "todos":
        run_todos(args)
        return

    if args.command == "review":
        run_review(args)
        return

    if args.command == "env":
        run_env(args)
        return

    if args.command == "setup":
        run_setup(args)
        return

    if args.command == "scaffold":
        run_scaffold(args)
        return

    if args.command == "dockerize":
        run_dockerize(args)
        return

    if args.command == "cicd":
        run_cicd(args)
        return

    if args.command == "verify":
        run_verify(args)
        return

    if args.command == "troubleshoot":
        await run_troubleshoot(args)
        return

    if args.command == "sentinel":
        run_sentinel(args)
        return

    # Handle `health` command
    if args.command == "health":
        run_health_check(args.project_dir, output_format=args.format, output_file=args.output)
        return

    if args.command == "debt":
        from shared.debt import run_debt_report
        run_debt_report(args.project_dir, json_output=args.json)
        return

    if args.command == "check-links":
        from shared.link_checker import run_check_links
        success = run_check_links(
            project_dir=args.project_dir,
            files_pattern=args.files,
            ignore=args.ignore,
            timeout=args.timeout,
            concurrency=args.concurrency
        )
        sys.exit(0 if success else 1)

    if args.command == "security":
        run_security(args)
        return

    if args.command == "help":
        run_help(args)
        return

    if args.command == "cherry-pick":
        run_cherry_pick(args)
        return

    if args.command == "rollback":
        run_rollback(args)
        return

    if args.command == "timeline":
        run_timeline(args)
        return

    if args.command == "analytics":
        run_analytics(args)
        return

    if args.command == "deps":
        run_deps(args)
        return

    if args.command == "duplication":
        run_duplication(args)
        return

    if args.command == "unused":
        run_unused(args)
        return

    if args.command == "risk":
        run_risk(args)
        return

    if args.command == "impact":
        run_impact(args)
        return

    if args.command == "a11y":
        run_a11y(args)
        return

    if args.command == "bisect":
        await run_bisect(args)
        return

    if args.command == "map":
        run_map(args)
        return

    if args.command in ["architecture", "arch"]:
        run_architecture(args)
        return

    if args.command == "release":
        run_release(args)
        return

    if args.command == "openapi":
        await run_openapi(args)
        return

    if args.command == "docstring":
        await run_docstring(args)
        return

    if args.command == "refactor":
        await run_refactor(args)
        return

    if args.command == "polish":
        await run_polish(args)
        return

    if args.command == "resolve":
        await run_resolve(args)
        return

    if args.command == "regex":
        await run_regex(args)
        return

    if args.command == "logic-lab":
        await run_logic_lab(args)
        return

    if args.command == "cron-lab":
        await run_cron_lab(args)
        return

    if args.command in ["resolve-conflicts", "fix-conflicts"]:
        await run_resolve_conflicts(args)
        return

    if args.command in ["generate-tests", "gentest"]:
        await run_generate_tests(args)
        return

    if args.command == "dataset":
        run_dataset(args)
        return

    if args.command == "snippets":
        run_snippets(args)
        return

    if args.command == "mock":
        run_mock(args)
        return

    if args.command == "frontend":
        run_frontend(args)
        return

    if args.command == "i18n":
        await run_i18n(args)
        return

    if args.command == "api-lab":
        run_api_lab_cli(args)
        return

    if args.command == "data-lab":
        run_data_lab(args)
        return

    if args.command == "schema-lab":
        run_schema_lab_logic(args)
        return

    if args.command == "research":
        run_research_logic(args.url, args.depth, args.limit)
        return

    if args.command == "serve":
        run_serve(args)
        return

    if args.command == "ide":
        run_ide(args)
        return

    if args.command == "scheduler":
        run_scheduler(args)
        return

    if args.command == "chaos":
        run_chaos(args)
        return

    if args.command == "guardrails":
        run_guardrails(args)
        return

    if args.command == "devtools":
        run_devtools(args)
        return

    if args.command == "standup":
        from shared.standup import run_standup_logic
        await run_standup_logic(args)
        return

    if args.command == "presentation":
        from shared.presentation import run_presentation
        await run_presentation(
            project_dir=args.project_dir,
            output=args.output,
            theme=args.theme,
            agent_type=args.agent,
            model=args.model
        )
        return

    if args.command == "visualize":
        from shared.visualization import run_visualize
        run_visualize(args)
        return

    if args.command == "network":
        run_network(args)
        return

    if args.command == "sanitize":
        run_sanitize(args)
        return

    if args.command == "gantt":
        run_gantt(args)
        return

    if args.command == "badges":
        run_badges(args)
        return

    if args.command in ["crypto-lab", "crypto"]:
        run_crypto_lab(args)
        return

    if args.command in ["image-lab", "img"]:
        run_image_lab(args)
        return

    if args.command in ["media-lab", "media"]:
        run_media_lab(args)
        return

    if args.command in ["xml-lab", "xml"]:
        run_xml_lab(args)
        return

    if args.command in ["markdown-lab", "md", "md-lab"]:
        run_markdown_lab(args)
        return

    if args.command in ["net-lab", "net"]:
        run_net_lab_logic(args)
        return

    if args.command in ["pdf-lab", "pdf"]:
        run_pdf_lab_logic(args)
        return

    if args.command in ["archive-lab", "arc"]:
        run_archive_lab(args)
        return

    if args.command in ["uni-lab", "uni"]:
        run_uni_lab(args)
        return

    if args.command in ["docs-lab", "docs"]:
        run_docs_lab(args)
        return

    if args.command in ["qr-lab", "qr"]:
        run_qr_lab(args)
        return

    if args.command in ["http-lab", "http", "req"]:
        run_http_lab(args)
        return

    if args.command in ["proxy-lab", "proxy"]:
        run_proxy_lab_logic(args)
        return

    if args.command in ["webhook-lab", "webhook", "hook"]:
        run_webhook_lab(args)
        return

    if args.command in ["proc-lab", "proc"]:
        await run_proc_lab_logic(args)
        return

    if args.command in ["geo-lab", "geo"]:
        run_geo_lab(args)
        return

    if args.command in ["struct-lab", "struct", "bin"]:
        run_struct_lab(args)
        return

    if args.command in ["chart-lab", "chart"]:
        run_chart_lab(args)
        return

    if args.command in ["enc-lab", "enc", "encode"]:
        run_enc_lab(args)
        return

    if args.command in ["rss-lab", "rss"]:
        run_rss_lab(args)
        return

    if args.command in ["fs-lab", "fs", "files"]:
        run_fs_lab(args)
        return

    if args.command in ["ws-lab", "ws"]:
        await run_ws_lab_logic(args)
        return

    if args.command in ["hash-lab", "hash"]:
        run_hash_lab(args)
        return

    if args.command in ["random-lab", "rand", "random"]:
        run_random_lab(args)
        return

    if args.command in ["browser-lab", "browser", "web"]:
        await run_browser_lab(args)
        return

    if args.command in ["npm-lab", "npm"]:
        run_npm_lab(args)
        return

    if args.command in ["pypi-lab", "pypi"]:
        run_pypi_lab(args)
        return

    if args.command in ["docker-lab", "docker", "container"]:
        run_docker_lab(args)
        return

    if args.command in ["compose-lab", "compose"]:
        run_compose_lab(args)
        return

    if args.command in ["k8s-lab", "k8s", "kube"]:
        run_k8s_lab(args)
        return

    if args.command == "diff-lab":
        run_diff_lab_logic(args)
        return

    if args.command in ["redis-lab", "redis", "cache"]:
        run_redis_lab(args)
        return

    if args.command in ["kafka-lab", "kafka"]:
        run_kafka_lab(args)
        return

    if args.command in ["email-lab", "email", "mail", "smtp"]:
        await run_email_lab(args)
        return

    if args.command in ["sock-lab", "sock", "nc", "netcat"]:
        await run_sock_lab_logic(args)
        return

    if args.command in ["ssh-lab", "ssh"]:
        run_ssh_lab(args)
        return

    if args.command in ["tmux-lab", "tmux"]:
        run_tmux_lab(args)
        return

    if args.command in ["terraform-lab", "tf", "terraform"]:
        run_terraform_lab(args)
        return

    if args.command in ["dns-lab", "dns"]:
        run_dns_lab(args)
        return

    if args.command in ["whois-lab", "whois"]:
        run_whois_lab(args)
        return

    if args.command in ["s3-lab", "s3"]:
        run_s3_lab_logic(args)
        return

    if args.command in ["graphql-lab", "gql"]:
        run_graphql_lab_logic(args)
        return

    if args.command in ["helm-lab", "helm"]:
        run_helm_lab_logic(args)
        return

    if args.command in ["notebook-lab", "nb"]:
        run_notebook_lab_logic(args)
        return

    if args.command in ["grpc-lab", "grpc"]:
        run_grpc_lab_logic(args)
        return

    if args.command in ["monitor-lab", "monitor", "mon"]:
        run_monitor_lab(args)
        return

    if args.command in ["metrics-lab", "metrics"]:
        run_metrics_lab(args)
        return

    if args.command in ["trace-lab", "trace"]:
        await run_trace_lab(args)
        return

    if args.command in ["notify-lab", "notify"]:
        run_notify_lab(args)
        return

    if args.command in ["contract-lab", "contract"]:
        run_contract_lab(args)
        return

    if args.command in ["ansible-lab", "ansible"]:
        run_ansible_lab(args)
        return

    if args.command in ["hex-lab", "hex"]:
        run_hex_lab(args)
        return

    if args.command in ["speed-lab", "speed"]:
        run_speed_lab(args)
        return

    if args.command in ["load-lab", "load"]:
        await run_load_lab(args)
        return

    if args.command in ["ast-lab", "ast"]:
        run_ast_lab(args)
        return

    if args.command in ["otp-lab", "otp", "totp", "mfa"]:
        run_otp_lab(args)
        return

    if args.command in ["cheatsheet-lab", "cheatsheet", "cheat"]:
        run_cheatsheet(args)
        return

    if args.command in ["calendar-lab", "calendar", "cal"]:
        run_calendar_lab(args)
        return

    if args.command in ["finance-lab", "finance", "fin"]:
        run_finance_lab(args)
        return

    if args.command in ["runner-lab", "runner"]:
        run_runner_lab(args)
        return

    if args.command in ["gitignore-lab", "gitignore", "gi"]:
        run_gitignore_lab(args)
        return

    if args.command in ["ollama-lab", "ollama", "ol"]:
        run_ollama_lab(args)
        return

    if args.command in ["mqtt-lab", "mqtt", "mq"]:
        run_mqtt_lab(args)
        return

    if args.command in ["fuzz-lab", "fuzz"]:
        run_fuzz_lab(args)
        return

    if args.command in ["static-lab", "static", "serve-static"]:
        run_static_lab_logic(args)
        return

    if args.command in ["github-lab", "github", "gh"]:
        run_github_lab_logic(args)
        return

    if args.command in ["cidr-lab", "cidr"]:
        run_cidr_lab(args)
        return

    if args.command == "jwt-lab":
        run_jwt_lab(args)
        return

    if args.command in ["uuid-lab", "uuid"]:
        run_uuid_lab(args)
        return

    if args.command in ["password-lab", "pwd-lab"]:
        run_password_lab(args)
        return

    if args.command in ["text-lab", "txt"]:
        run_text_lab(args)
        return

    if args.command in ["html-lab", "html"]:
        run_html_lab(args)
        return

    if args.command in ["url-lab", "url"]:
        run_url_lab(args)
        return

    if args.command in ["cert-lab", "cert"]:
        run_cert_lab(args)
        return

    if args.command in ["time-lab", "time"]:
        run_time_lab(args)
        return

    if args.command in ["math-lab", "math"]:
        run_math_lab(args)
        return

    if args.command in ["calc-lab", "calc"]:
        run_calc_lab(args)
        return

    if args.command in ["unit-lab", "unit"]:
        run_unit_lab(args)
        return

    if args.command in ["semver-lab", "semver"]:
        run_semver_lab(args)
        return

    if args.command in ["sys-lab", "sys"]:
        run_sys_lab(args)
        return

    if args.command in ["log-lab", "ll"]:
        run_log_lab(args)
        return

    if args.command in ["sql-lab", "sql"]:
        await run_sql_lab(args)
        return

    if args.command in ["json-lab", "json"]:
        run_json_lab(args)
        return

    if args.command in ["yaml-lab", "yaml"]:
        run_yaml_lab(args)
        return

    if args.command in ["toml-lab", "toml"]:
        run_toml_lab(args)
        return

    if args.command in ["csv-lab", "csv"]:
        run_csv_lab(args)
        return

    if args.command in ["excel-lab", "xls", "xlsx", "excel"]:
        run_excel_lab(args)
        return

    if args.command in ["template-lab", "tpl", "template"]:
        run_template_lab(args)
        return

    if args.command == "kanban":
        run_kanban(args)
        return

    if args.command == "port":
        run_port(args)
        return

    if args.command == "color-lab":
        run_color_lab(args)
        return

    if args.command == "resume":
        await run_resume(args)
        return

    if args.command == "retro":
        await run_retro(args)
        return

    if args.command == "smart-context":
        run_smart_context(args)
        return

    if args.command in ["cq", "code-query"]:
        run_code_query_cli(args)
        return

    if args.command in ["systemd-lab", "systemd", "service"]:
        run_systemd_lab(args)
        return

    if args.command in ["path-lab", "path"]:
        run_path_lab(args)
        return

    if args.command in ["http-server-lab", "httpd", "server"]:
        await run_http_server_lab_logic(args)
        return

    if args.command in ["ascii-lab", "ascii"]:
        run_ascii_lab(args)
        return

    if args.command in ["pattern-lab", "pattern", "design"]:
        run_pattern_lab(args)
        return

    if args.command in ["bandwidth-lab", "bandwidth", "bw"]:
        run_bandwidth_lab(args)
        return

    if args.command in ["typing-lab", "type"]:
        run_typing_lab(args)
        return

    if args.command in ["sound-lab", "sound", "audio"]:
        run_sound_lab(args)
        return

    if args.command in ["maze-lab", "maze"]:
        run_maze_lab(args)
        return

    if args.command in ["license-lab", "lic", "license"]:
        run_license_lab(args)
        return

    if args.command in ["rfc-lab", "rfc"]:
        run_rfc_lab(args)
        return

    if args.command in ["productivity-lab", "prod", "focus"]:
        run_productivity_lab_logic(args)
        return

    if args.command in ["rename-lab", "rename"]:
        run_rename_lab(args)
        return

    if args.command in ["find-lab", "find", "locate"]:
        run_find_lab(args)
        return

    if args.command in ["diagram-lab", "diagram", "draw"]:
        run_diagram_lab(args)
        return

    if args.command in ["pipe-lab", "pipe", "stream"]:
        run_pipeline_lab(args)
        return

    if args.command in ["dict-lab", "dict", "define", "synonym", "antonym", "thesaurus"]:
        # If the command itself is one of the actions, we need to adjust args.
        # e.g. "define hello" -> args.command="define", args.word="hello", args.action="define"
        if args.command in ["define", "synonym", "antonym", "thesaurus"]:
             # If the user typed 'define hello', argparse parsed 'define' as command and 'hello' as word.
             # We want args.action to be 'define'.
             # However, our parser definition for dict-lab expects "word" and "action".
             # If we used aliases, 'define' maps to dict-lab parser.
             # So 'main.py define hello' parses 'hello' as word, and action defaults to 'define' or consumes next arg?
             # Let's fix action if needed.
             if args.command == "synonym" or args.command == "thesaurus":
                 args.action = "synonym"
             elif args.command == "antonym":
                 args.action = "antonym"
             else:
                 args.action = "define"

        run_dict_lab(args)
        return

    if args.command in ["emoji-lab", "emoji", "emoj"]:
        run_emoji_lab(args)
        return

    # Initialize Agent Client
    from shared.agent_client import AgentClient
    from shared.utils import generate_agent_id

    project_name = os.environ.get("PROJECT_NAME")
    if not project_name:
        project_name = args.project_dir.resolve().name

    # Load Configuration from File
    # Priority resolved in config_loader: ./ > XDG > Legacy
    ensure_config_exists()
    file_config = load_config_from_file(profile=args.profile)

    # Helper to resolve configuration priority: CLI > Config File > Default
    def resolve(cli_arg, config_key, default_val):
        if cli_arg is not None:
            return cli_arg
        if config_key in file_config:
            return file_config[config_key]
        return default_val

    # Create Config
    config = Config(
        project_dir=args.project_dir,
        agent_id=None,  # Placeholder, set later
        agent_type=args.agent,
        model=resolve(args.model, "model", None),
        max_iterations=resolve(args.max_iterations, "max_iterations", None),
        verbose=args.verbose,
        stream_output=not args.no_stream,
        spec_file=args.spec,
        verify_creation=args.verify_creation,

        # Manager
        manager_frequency=resolve(args.manager_frequency, "manager_frequency", 10),
        manager_model=resolve(args.manager_model, "manager_model", None),
        run_manager_first=args.manager_first,
        login_mode=args.login or file_config.get("login_mode", False),

        timeout=resolve(args.timeout, "timeout", 600.0),
        max_error_wait=resolve(args.max_error_wait, "max_error_wait", 600.0),

        # Sprint
        sprint_mode=args.sprint or file_config.get("sprint_mode", False),
        max_agents=resolve(args.max_agents, "max_agents", 1),

        # Notifications
        slack_webhook_url=file_config.get("slack_webhook_url"),
        discord_webhook_url=file_config.get("discord_webhook_url"),
        notification_settings=file_config.get("notification_settings"),

        # Docker-in-Docker
        dind_enabled=args.dind or file_config.get("dind_enabled", False),

        # Git Hooks
        git_hooks=file_config.get("git_hooks"),
    )

    # Initialize Database
    from shared.database import init_db
    # Ensure project dir exists for DB creation
    config.project_dir.mkdir(parents=True, exist_ok=True)
    init_db(config.project_dir / ".agent_db.sqlite")

    # Load Jira Config
    from shared.config import JiraConfig
    jira_cfg_data = file_config.get("jira", {})
    jira_env_url = os.environ.get("JIRA_URL")
    jira_env_email = os.environ.get("JIRA_EMAIL")
    jira_env_token = os.environ.get("JIRA_TOKEN")

    if jira_env_url:
        jira_cfg_data["url"] = jira_env_url
    if jira_env_email:
        jira_cfg_data["email"] = jira_env_email
    if jira_env_token:
        jira_cfg_data["token"] = jira_env_token

    if args.jira_ticket or args.jira_label:
        if not jira_cfg_data:
            print("Error: Jira arguments provided but no Jira configuration found (config file or env vars).", file=sys.stderr)
            print("Please set JIRA_URL, JIRA_EMAIL, JIRA_TOKEN or configure agent_config.yaml", file=sys.stderr)
            sys.exit(1)
        config.jira = JiraConfig(**jira_cfg_data)

    # Correction for boolean flags initialized with 'store_true' (default False)
    if file_config.get("run_manager_first"):
        config.run_manager_first = True

    # SETUP LOGGER (Moved earlier to support logging during Jira fetch)
    repo_root = Path(__file__).parent
    agents_log_dir = repo_root / "agents/logs"
    agents_log_dir.mkdir(parents=True, exist_ok=True)

    # We need a temp ID for logging before we know the real agent_id (which might come from Jira)
    # But for now, we can use a generic one or wait.
    # Let's setup a basic console logger first?
    # existing setup_logger requires a file. We will update it later.

    # Handle `show-config` command and deprecated `--dry-run`
    if args.command == "show-config":
        run_show_config(config)

    if args.dry_run:
        print("Warning: --dry-run is deprecated. Please use the 'show-config' command instead.", file=sys.stderr)
        run_show_config(config)

    # JIRA LOGIC
    jira_client = None
    # jira_ticket = None  # Unused
    jira_spec_content = ""

    if config.jira and (args.jira_ticket or args.jira_label):
        from shared.jira_client import JiraClient

        try:
            jira_client = JiraClient(config.jira)

            if args.jira_ticket:
                issue = jira_client.get_issue(args.jira_ticket)
            elif args.jira_label:
                issue = jira_client.get_first_todo_by_label(args.jira_label)

            if issue:
                # jira_ticket = issue  # Unused
                print(f"Working on Jira Ticket: {issue.key} - {issue.fields.summary}")

                # Parse Description (for context only)
                desc = issue.fields.description or ""

                # Construct Spec
                jira_spec_content = f"JIRA TICKET {issue.key}\nSUMMARY: {issue.fields.summary}\nDESCRIPTION:\n{desc}"
                config.jira_ticket_key = issue.key
                config.jira_spec_content = jira_spec_content
                project_name = issue.key

                # Transition to In Progress (default 'Start' status)
                start_status = config.jira.status_map.get("start", "In Progress") if config.jira.status_map else "In Progress"
                jira_client.transition_issue(issue.key, start_status)

            else:
                print("No suitable Jira ticket found.")
                sys.exit(0)

        except Exception as e:
            print(f"Jira Integration Error: {e}", file=sys.stderr)
            sys.exit(1)

    # Read spec content for ID generation
    spec_content = ""
    if jira_spec_content:
        spec_content = jira_spec_content
    elif args.spec and args.spec.exists():
        try:
            spec_content = args.spec.read_text()
        except Exception as e:
            print(f"Warning: Could not read spec file for ID generation: {e}", file=sys.stderr)

    # Generate deterministic ID
    agent_id = generate_agent_id(project_name, spec_content, args.agent)
    config.agent_id = agent_id

    log_file = agents_log_dir / f"{agent_id}.log"

    # Configure Root Logger to capture all module logs (e.g. shared.git)
    logger, memory_handler = setup_logger(name="", log_file=log_file, verbose=args.verbose)

    logger.info(f"Starting {args.agent.capitalize()} Agent on {args.project_dir}")
    logger.info(f"Generated Agent ID: {agent_id}")

    # Append the current run ID to the history file
    try:
        history_file = config.project_dir / ".agent_history"
        with open(history_file, "a") as f:
            f.write(f"{agent_id}\n")
    except IOError as e:
        logger.warning(f"Could not write to history file {history_file}: {e}")

    client = AgentClient(agent_id=agent_id, dashboard_url=args.dashboard_url, memory_handler=memory_handler)

    # Check spec requirement for fresh projects (Updated for Jira)
    is_fresh = not config.feature_list_path.exists()
    if is_fresh and not args.spec and not jira_spec_content:
        logger.error(
            "Error: --spec argument or --jira-ticket is required for new projects!"
        )
        sys.exit(1)

    # Git Safety
    # Ensure we are on a safe branch before starting any agent work
    jira_key = config.jira_ticket_key if config.jira else None
    ensure_git_safe(args.project_dir, ticket_key=jira_key)

    # Git Authentication (Env Var Check)
    git_token = os.environ.get("GIT_TOKEN")
    if git_token:
        from shared.git import configure_git_auth
        git_host = os.environ.get("GIT_HOST", "github.com")
        git_user = os.environ.get("GIT_USERNAME", "x-access-token")
        configure_git_auth(git_token, git_host, git_user)

    # Dispatch
    try:
        if config.sprint_mode:
            logger.info("Running in SPRINT MODE")
            await run_sprint(config, agent_client=client)
            return

        if args.agent == "gemini":
            await run_gemini(config, agent_client=client)
        elif args.agent == "cursor":
            await run_cursor(config, agent_client=client)
        elif args.agent == "local":
            await run_local(config, agent_client=client)
        elif args.agent == "openrouter":
            await run_openrouter(config, agent_client=client)
    except KeyboardInterrupt:
        logger.info("\nExecution interrupted by user.")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)

    # Post-Execution Cleanup
    # If project is signed off, run the completion flow and cleaner
    if (config.project_dir / "PROJECT_SIGNED_OFF").exists():
        # Final safety check for Jira completion (in case iteration loop didn't hit it)
        if config.jira and config.jira_ticket_key:
            from shared.workflow import complete_jira_ticket
            await complete_jira_ticket(config)

        logger.info("Project signed off. Finalizing...")
        # note: the autonomous loop itself now handles triggering the cleaner agent
        # if cleanup_report.txt is missing.


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(main())
