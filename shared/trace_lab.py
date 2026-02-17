import sys
import os
import shutil
import subprocess
import re
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
from collections import Counter

from shared.agent_client import AgentClient

class TraceLabManager:
    """
    Manages system call tracing using strace.
    """
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.strace_bin = shutil.which("strace")

    def check_availability(self) -> bool:
        return self.strace_bin is not None

    async def run_trace(self, command: List[str], output_file: Path) -> bool:
        """
        Runs a command under strace.
        """
        if not self.check_availability():
            print("❌ 'strace' not found. Please install it (e.g. apt install strace).", file=sys.stderr)
            return False

        # strace arguments:
        # -f: follow forks
        # -s 256: increase string size
        # -o file: output to file
        trace_cmd = [self.strace_bin, "-f", "-s", "256", "-o", str(output_file)] + command

        print(f"--- Tracing: {' '.join(command)} ---")
        print(f"Output: {output_file}")

        try:
            # We run trace command. It will run the target command.
            # stdout/stderr of target command should still go to terminal.
            process = await asyncio.create_subprocess_exec(
                *trace_cmd,
                cwd=self.project_dir
            )
            return_code = await process.wait()

            if return_code != 0:
                print(f"⚠️  Command exited with code {return_code}")
            else:
                print("✅ Command finished successfully.")

            return True

        except Exception as e:
            print(f"❌ Error running trace: {e}", file=sys.stderr)
            return False

    def analyze_trace(self, trace_file: Path) -> Dict[str, Any]:
        """
        Parses strace output to extract useful stats.
        """
        if not trace_file.exists():
            return {"error": "Trace file not found."}

        stats = {
            "files_opened": [],
            "files_failed": [],
            "network_connects": [],
            "errors": Counter(),
            "syscalls": Counter()
        }

        # Regex for open/openat
        # 1234 openat(AT_FDCWD, "/path/to/file", O_RDONLY|...) = 3
        # 1234 openat(AT_FDCWD, "/path/to/missing", O_RDONLY|...) = -1 ENOENT (No such file or directory)
        re_open = re.compile(r'open(?:at)?\([^,]+, "([^"]+)"')

        # Regex for connect
        # connect(3, {sa_family=AF_INET, sin_port=htons(80), sin_addr=inet_addr("1.2.3.4")}, 16) = 0
        re_connect = re.compile(r'connect\(\d+, \{.*sin_addr=inet_addr\("([^"]+)"\).*\}')

        # Regex for result/error
        # ... = -1 ERROR_CODE (Description)
        re_result = re.compile(r'= (-?\d+)(?: ([A-Z0-9]+) \((.*)\))?$')

        # Regex for syscall name
        # PID syscall(
        re_syscall = re.compile(r'(?:\d+\s+)?([a-zA-Z0-9_]+)\(')

        try:
            with open(trace_file, 'r', encoding='utf-8', errors='replace') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    # Extract syscall
                    m_sys = re_syscall.match(line)
                    if m_sys:
                        syscall = m_sys.group(1)
                        stats["syscalls"][syscall] += 1

                    # Check result
                    # Strace lines usually end with " = result"
                    # But if unfinished/resumed, might be different. We skip complex cases for MVP.
                    m_res = re_result.search(line)
                    error_code = None
                    if m_res:
                        res_val = m_res.group(1) # Return value (e.g. 3 or -1)
                        if m_res.group(2): # Error code exists
                            error_code = m_res.group(2)
                            stats["errors"][error_code] += 1

                    # File Open Analysis
                    if "open" in line:
                        m_open = re_open.search(line)
                        if m_open:
                            path = m_open.group(1)
                            if error_code:
                                stats["files_failed"].append({"path": path, "error": error_code})
                            else:
                                stats["files_opened"].append(path)

                    # Network Analysis
                    if "connect" in line:
                        m_conn = re_connect.search(line)
                        if m_conn:
                            ip = m_conn.group(1)
                            stats["network_connects"].append(ip)

        except Exception as e:
            return {"error": str(e)}

        # Deduplicate lists
        stats["files_opened"] = sorted(list(set(stats["files_opened"])))
        # For failed files, we keep error context but dedupe by path+error
        unique_failed = {}
        for item in stats["files_failed"]:
            key = f"{item['path']}|{item['error']}"
            unique_failed[key] = item
        stats["files_failed"] = list(unique_failed.values())

        stats["network_connects"] = sorted(list(set(stats["network_connects"])))

        return stats

    async def explain_trace(self, trace_file: Path, agent_type: str = "gemini", model: Optional[str] = None) -> None:
        """
        Sends trace analysis to AI for explanation.
        """
        analysis = self.analyze_trace(trace_file)
        if "error" in analysis and isinstance(analysis["error"], str):
            print(f"❌ Error analyzing trace: {analysis['error']}")
            return

        print("🤖 Analyzing trace with AI...")

        # Construct prompt
        summary = f"""
Trace Analysis Summary:
- Unique Files Opened: {len(analysis['files_opened'])}
- Unique Files Failed: {len(analysis['files_failed'])}
- Network Connections: {len(analysis['network_connects'])}
- Top Syscalls: {analysis['syscalls'].most_common(5)}
- Top Errors: {analysis['errors'].most_common(5)}

Files Failed (Sample):
{json.dumps(analysis['files_failed'][:10], indent=2)}

Network Connections:
{json.dumps(analysis['network_connects'], indent=2)}
"""
        # Read tail of trace file for context (last 50 lines)
        try:
            with open(trace_file, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
                tail = "".join(lines[-50:])
        except Exception:
            tail = "(Could not read trace tail)"

        prompt = f"""
You are a Linux System Expert. I have run a command under 'strace' and it might have failed or behaved unexpectedly.
Here is the summary of the trace execution:

{summary}

Here are the last 50 lines of the raw trace output:

```
{tail}
```

Please analyze this information.
1. Identify any critical failures (e.g. missing config files, permission denied, connection refused).
2. Explain what the process was trying to do before it exited.
3. Suggest potential fixes.
"""

        client = AgentClient(agent_id="trace_expert")
        response = await client.ask_agent(
            prompt=prompt,
            agent_type=agent_type,
            model=model,
            project_dir=self.project_dir
        )

        print("\n--- AI Analysis ---")
        print(response)
        print("-------------------")

import json

async def run_trace_lab_logic(args):
    """
    CLI entry point for Trace Lab.
    """
    manager = TraceLabManager(args.project_dir)

    if args.action == "run":
        if not args.command_args:
            print("Error: Command required.", file=sys.stderr)
            sys.exit(1)

        # Separate trace-lab args from target command args if using --
        # argparse handles this if we define 'command_args' as nargs=argparse.REMAINDER
        # But main.py usually does this manually for some commands.

        cmd = args.command_args
        if cmd[0] == "--":
            cmd = cmd[1:]

        output_file = Path(args.output).resolve() if args.output else args.project_dir / "trace.log"

        success = await manager.run_trace(cmd, output_file)

        if args.explain:
            await manager.explain_trace(output_file, agent_type=args.agent, model=args.model)
        elif success:
            print(f"To analyze results run: trace-lab analyze {output_file.name}")

    elif args.action == "analyze":
        if not args.file:
            print("Error: Trace file required.", file=sys.stderr)
            sys.exit(1)

        trace_path = Path(args.file).resolve()
        analysis = manager.analyze_trace(trace_path)

        if args.json:
            # specific conversion for Counter
            analysis["errors"] = dict(analysis["errors"])
            analysis["syscalls"] = dict(analysis["syscalls"])
            print(json.dumps(analysis, indent=2))
        else:
            print(f"--- Trace Analysis: {trace_path.name} ---")
            print(f"Unique Files Opened: {len(analysis['files_opened'])}")
            print(f"Unique Files Failed: {len(analysis['files_failed'])}")
            print(f"Network Connections: {len(analysis['network_connects'])}")

            if analysis['errors']:
                print("\nTop Errors:")
                for err, count in analysis['errors'].most_common(5):
                    print(f"  {err}: {count}")

            if analysis['files_failed']:
                print("\nFailed File Operations (Top 10):")
                for item in analysis['files_failed'][:10]:
                    print(f"  {item['path']} -> {item['error']}")

    elif args.action == "explain":
        if not args.file:
            print("Error: Trace file required.", file=sys.stderr)
            sys.exit(1)

        trace_path = Path(args.file).resolve()
        await manager.explain_trace(trace_path, agent_type=args.agent, model=args.model)
