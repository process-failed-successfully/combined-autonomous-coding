import json
import re
import sys
import argparse
from datetime import datetime
from collections import Counter
from typing import List, Dict, Any, Generator, Optional

class LogParser:
    """Parses various log formats into structured dictionaries."""

    # Common Log Format (CLF) Regex
    # 127.0.0.1 - frank [10/Oct/2000:13:55:36 -0700] "GET /apache_pb.gif HTTP/1.0" 200 2326
    CLF_REGEX = re.compile(
        r'^(?P<ip>\S+) \S+ (?P<user>\S+) \[(?P<timestamp>.+?)\] "(?P<method>\S+) (?P<path>\S+) (?P<protocol>\S+)" (?P<status>\d+) (?P<size>\S+)'
    )

    # Basic Syslog Regex (RFC 3164ish)
    # Oct 11 22:14:15 mymachine su: 'su root' failed for lonvick on /dev/pts/8
    SYSLOG_REGEX = re.compile(
        r'^(?P<timestamp>[A-Z][a-z]{2}\s+\d+\s\d{2}:\d{2}:\d{2}) (?P<hostname>\S+) (?P<process>\S+?): (?P<message>.*)$'
    )

    # Key-Value Regex (key=value)
    KV_REGEX = re.compile(r'(?P<key>[a-zA-Z0-9_.-]+)=(?P<value>"[^"]*"|\S+)')

    def parse(self, line: str, format_type: str = "auto") -> Optional[Dict[str, Any]]:
        line = line.strip()
        if not line:
            return None

        if format_type == "json":
            return self.parse_json(line)
        elif format_type == "clf":
            return self.parse_clf(line)
        elif format_type == "syslog":
            return self.parse_syslog(line)
        elif format_type == "kv":
            return self.parse_kv(line)
        elif format_type == "auto":
            # Heuristics
            if line.startswith("{") and line.endswith("}"):
                res = self.parse_json(line)
                if res: return res

            # Try CLF
            res = self.parse_clf(line)
            if res: return res

            # Try Syslog
            res = self.parse_syslog(line)
            if res: return res

            # Try KV
            if "=" in line:
                res = self.parse_kv(line)
                if res: return res

            # Fallback: Just return line
            return {"raw": line, "message": line}

        return None

    def parse_json(self, line: str) -> Optional[Dict[str, Any]]:
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            return None

    def parse_clf(self, line: str) -> Optional[Dict[str, Any]]:
        match = self.CLF_REGEX.match(line)
        if match:
            data = match.groupdict()
            # Convert status/size to int/int
            try:
                data['status'] = int(data['status'])
                data['size'] = int(data['size']) if data['size'] != '-' else 0
            except ValueError:
                pass
            return data
        return None

    def parse_syslog(self, line: str) -> Optional[Dict[str, Any]]:
        match = self.SYSLOG_REGEX.match(line)
        if match:
            return match.groupdict()
        return None

    def parse_kv(self, line: str) -> Optional[Dict[str, Any]]:
        matches = self.KV_REGEX.findall(line)
        if matches:
            data = {}
            for key, value in matches:
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                data[key] = value
            return data
        return None

class LogAnalyzer:
    """Analyzes streams of parsed logs."""

    def filter_logs(self, logs: Generator[Dict[str, Any], None, None],
                   level: str = None,
                   keyword: str = None,
                   field_filter: str = None) -> Generator[Dict[str, Any], None, None]:

        for log in logs:
            if not log: continue

            # Level filter (assuming 'level' or 'severity' field)
            if level:
                log_level = str(log.get("level") or log.get("severity") or "").upper()
                if level.upper() not in log_level:
                    continue

            # Keyword search in whole log
            if keyword:
                found = False
                for v in log.values():
                    if keyword.lower() in str(v).lower():
                        found = True
                        break
                if not found:
                    continue

            # Field filter (e.g. status=200)
            if field_filter:
                try:
                    k, v = field_filter.split("=", 1)
                    val = log.get(k)
                    if str(val) != v:
                        continue
                except ValueError:
                    pass # Ignore invalid filter format

            yield log

    def get_stats(self, logs: Generator[Dict[str, Any], None, None], group_by: str) -> List[tuple]:
        counter = Counter()
        for log in logs:
            if not log: continue
            val = log.get(group_by)
            if val is not None:
                counter[str(val)] += 1
        return counter.most_common()

def run_log_lab_logic(args):
    """CLI Handler for Log Lab."""
    parser = LogParser()
    analyzer = LogAnalyzer()

    # Input source: File or Stdin
    if hasattr(args, 'file') and args.file:
        try:
            source = open(args.file, 'r', encoding='utf-8', errors='replace')
        except FileNotFoundError:
            print(f"Error: File '{args.file}' not found.", file=sys.stderr)
            return False
    else:
        source = sys.stdin

    # Generator for parsed logs
    def parsed_stream():
        for line in source:
            parsed = parser.parse(line, format_type=args.format if hasattr(args, 'format') else 'auto')
            if parsed:
                yield parsed
        if source is not sys.stdin:
            source.close()

    # Action Dispatch
    if args.action == "parse":
        for log in parsed_stream():
            print(json.dumps(log))

    elif args.action == "filter":
        filtered = analyzer.filter_logs(
            parsed_stream(),
            level=args.level,
            keyword=args.pattern,
            field_filter=args.field
        )
        for log in filtered:
            print(json.dumps(log))

    elif args.action == "stats":
        if not args.group_by:
            print("Error: --group-by is required for stats.", file=sys.stderr)
            return False

        stats = analyzer.get_stats(parsed_stream(), args.group_by)
        print(f"--- Stats: Group by '{args.group_by}' ---")
        for k, v in stats:
            print(f"{k:<30} : {v}")

    return True
