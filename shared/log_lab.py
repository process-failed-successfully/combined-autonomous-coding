import json
import sys
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from collections import Counter
from shared.log_explorer import LogParser, AgentStep

class LogLabManager:
    """
    Manages log parsing, filtering, and analysis.
    """
    def __init__(self):
        self.parser = LogParser()

    def parse(self, log_path: Path, mode: str = "steps") -> List[Dict[str, Any]]:
        """Parses a log file into structured data."""
        if not log_path.exists():
            raise FileNotFoundError(f"Log file not found: {log_path}")

        if mode == "steps":
            steps = self.parser.parse_run(log_path)
            return [self._step_to_dict(s) for s in steps]
        elif mode == "raw":
            # Using internal method _parse_entries from LogParser
            entries = self.parser._parse_entries(log_path)
            return [self._entry_to_dict(e) for e in entries]
        else:
            raise ValueError(f"Unknown mode: {mode}")

    def filter_logs(self, log_path: Path, level: Optional[str] = None, pattern: Optional[str] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Filters log entries based on level and regex pattern."""
        entries = self.parser._parse_entries(log_path)

        filtered = []
        for entry in entries:
            if level and entry.level.upper() != level.upper():
                continue
            if pattern and not re.search(pattern, entry.message, re.IGNORECASE):
                continue
            filtered.append(self._entry_to_dict(entry))

        if limit:
            filtered = filtered[:limit]

        return filtered

    def stats(self, log_path: Path) -> Dict[str, Any]:
        """Calculates statistics for a log file."""
        entries = self.parser._parse_entries(log_path)

        if not entries:
            return {"count": 0}

        total_count = len(entries)
        levels = Counter(e.level for e in entries)

        # Calculate duration
        start_time = entries[0].timestamp
        end_time = entries[-1].timestamp

        # Error analysis
        errors = [e for e in entries if e.level == "ERROR"]
        error_rate = len(errors) / total_count if total_count > 0 else 0

        # Frequent messages (simplify/truncate for grouping)
        messages = [e.message.split('\n')[0][:80] for e in entries]
        top_messages = Counter(messages).most_common(5)

        return {
            "total_entries": total_count,
            "levels": dict(levels),
            "start_time": start_time,
            "end_time": end_time,
            "error_count": len(errors),
            "error_rate": f"{error_rate:.2%}",
            "top_messages": top_messages
        }

    def _step_to_dict(self, step: AgentStep) -> Dict[str, Any]:
        return {
            "id": step.step_id,
            "timestamp": step.timestamp,
            "type": step.type,
            "description": step.description,
            "details": step.details
        }

    def _entry_to_dict(self, entry) -> Dict[str, Any]:
        return {
            "timestamp": entry.timestamp,
            "level": entry.level,
            "message": entry.message
        }

def run_log_lab_logic(args):
    """CLI entry point for Log Lab."""
    manager = LogLabManager()

    # Resolve log path
    log_file = Path(args.file) if args.file else None

    if not log_file:
        # Try to find from run_id or latest
        repo_root = Path(__file__).parents[1] # shared/ -> root
        logs_dir = repo_root / "agents/logs"

        if args.run_id:
            log_file = logs_dir / f"{args.run_id}.log"
        else:
            # Find latest
            try:
                all_logs = sorted(logs_dir.glob('*.log'), key=lambda p: p.stat().st_mtime, reverse=True)
                if all_logs:
                    log_file = all_logs[0]
            except Exception:
                pass

    if not log_file or not log_file.exists():
        print(f"Error: Log file not found: {log_file}", file=sys.stderr)
        sys.exit(1)

    # Print header to stderr so JSON output is clean
    print(f"--- Processing log: {log_file.name} ---", file=sys.stderr)

    if args.action == "parse":
        try:
            data = manager.parse(log_file, mode=args.mode)
            print(json.dumps(data, indent=2))
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "filter":
        try:
            data = manager.filter_logs(log_file, level=args.level, pattern=args.pattern, limit=args.limit)
            if args.json:
                print(json.dumps(data, indent=2))
            else:
                for entry in data:
                    print(f"{entry['timestamp']} - {entry['level']} - {entry['message']}")
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "stats":
        try:
            stats = manager.stats(log_file)
            if args.json:
                print(json.dumps(stats, indent=2))
            else:
                print("--- Log Statistics ---")
                print(f"Total Entries: {stats['total_entries']}")
                print(f"Time Range:    {stats['start_time']} - {stats['end_time']}")
                print(f"Error Count:   {stats['error_count']} ({stats['error_rate']})")
                print("\nLevels:")
                for l, c in stats['levels'].items():
                    print(f"  {l:<8}: {c}")
                print("\nTop Messages:")
                for msg, count in stats['top_messages']:
                    print(f"  [{count}] {msg}")
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
