import sys
import re
import json
from typing import Dict, Any

class SyslogLabManager:
    """Manages Syslog parsing for RFC 3164 and RFC 5424 formats."""

    # RFC 5424: <PRIVAL>VERSION TIMESTAMP HOSTNAME APP-NAME PROCID MSGID [SD-ID...] MESSAGE
    RFC5424_REGEX = re.compile(
        r"^<(?P<prival>\d+)>(?P<version>\d+)\s+"
        r"(?P<timestamp>\S+)\s+(?P<hostname>\S+)\s+"
        r"(?P<appname>\S+)\s+(?P<procid>\S+)\s+"
        r"(?P<msgid>\S+)\s+(?P<structured_data>(?:-|(?:\[.*?\])+))(?:\s+(?P<message>.*))?$"
    )

    # RFC 3164: <PRIVAL>TIMESTAMP HOSTNAME TAG: MESSAGE
    # Timestamp is usually Mmm dd hh:mm:ss, e.g. Oct 11 22:14:15 or Oct  1 22:14:15
    RFC3164_REGEX = re.compile(
        r"^<(?P<prival>\d+)>(?P<timestamp>[A-Z][a-z]{2}\s+\d+\s+\d{2}:\d{2}:\d{2})\s+"
        r"(?P<hostname>\S+)\s+(?P<tag>[^:\[]+)(?:\[(?P<pid>\d+)\])?:\s*(?P<message>.*)?$"
    )

    def parse(self, message: str) -> Dict[str, Any]:
        """Parses a syslog message and returns its fields."""
        msg = message.strip()

        # Try RFC 5424
        m = self.RFC5424_REGEX.match(msg)
        if m:
            d = m.groupdict()
            prival = int(d["prival"])
            return {
                "type": "RFC 5424",
                "prival": prival,
                "facility": prival >> 3,
                "severity": prival & 7,
                "version": int(d["version"]),
                "timestamp": d["timestamp"],
                "hostname": d["hostname"],
                "appname": d["appname"],
                "procid": d["procid"],
                "msgid": d["msgid"],
                "structured_data": d["structured_data"],
                "message": d["message"] or ""
            }

        # Try RFC 3164
        m = self.RFC3164_REGEX.match(msg)
        if m:
            d = m.groupdict()
            prival = int(d["prival"])
            return {
                "type": "RFC 3164",
                "prival": prival,
                "facility": prival >> 3,
                "severity": prival & 7,
                "timestamp": d["timestamp"],
                "hostname": d["hostname"],
                "tag": d["tag"],
                "pid": d.get("pid"),
                "message": d["message"] or ""
            }

        return {"error": "Message does not match RFC 3164 or RFC 5424 formats."}

def run_syslog_lab_logic(args) -> bool:
    """CLI handler for Syslog Lab."""
    manager = SyslogLabManager()

    if getattr(args, "action", None) == "parse":
        message = ""
        if getattr(args, "message", None):
            message = args.message
        elif not sys.stdin.isatty():
            message = sys.stdin.read()
        else:
            print("Error: Must provide --message or pass data via stdin.", file=sys.stderr)
            return False

        if not message.strip():
             print("Error: Empty syslog message.", file=sys.stderr)
             return False

        # Support multiple messages separated by newlines
        lines = [line for line in message.splitlines() if line.strip()]
        results = []
        for line in lines:
            results.append(manager.parse(line))

        if len(results) == 1:
            print(json.dumps(results[0], indent=2))
            if "error" in results[0]:
                return False
        else:
            print(json.dumps(results, indent=2))
        return True

    print("Error: Action not specified or invalid.", file=sys.stderr)
    return False
