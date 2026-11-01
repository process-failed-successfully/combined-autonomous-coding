import re
import sys
import json
from typing import Dict, Any

FACILITIES = [
    "kernel messages", "user-level messages", "mail system", "system daemons",
    "security/authorization messages", "messages generated internally by syslogd",
    "line printer subsystem", "network news subsystem", "UUCP subsystem", "clock daemon",
    "security/authorization messages", "FTP daemon", "NTP subsystem", "log audit",
    "log alert", "clock daemon (note 2)", "local use 0 (local0)", "local use 1 (local1)",
    "local use 2 (local2)", "local use 3 (local3)", "local use 4 (local4)",
    "local use 5 (local5)", "local use 6 (local6)", "local use 7 (local7)"
]

SEVERITIES = [
    "Emergency: system is unusable",
    "Alert: action must be taken immediately",
    "Critical: critical conditions",
    "Error: error conditions",
    "Warning: warning conditions",
    "Notice: normal but significant condition",
    "Informational: informational messages",
    "Debug: debug-level messages"
]

class SyslogLabManager:
    def parse_priority(self, pri: int) -> Dict[str, Any]:
        facility_val = pri // 8
        severity_val = pri % 8

        facility_str = FACILITIES[facility_val] if 0 <= facility_val < len(FACILITIES) else f"Unknown ({facility_val})"
        severity_str = SEVERITIES[severity_val] if 0 <= severity_val < len(SEVERITIES) else f"Unknown ({severity_val})"

        return {
            "prival": pri,
            "facility_value": facility_val,
            "facility": facility_str,
            "severity_value": severity_val,
            "severity": severity_str
        }

    def parse(self, message: str) -> Dict[str, Any]:
        message = message.strip()

        # Check if it starts with <PRIVAL>
        pri_match = re.match(r"^<(\d{1,3})>", message)
        if not pri_match:
            raise ValueError("Not a valid syslog message (missing <PRIVAL>)")

        pri_val = int(pri_match.group(1))
        pri_data = self.parse_priority(pri_val)

        # RFC5424
        # <PRIVAL>VERSION TIMESTAMP HOSTNAME APP-NAME PROCID MSGID STRUCTURED-DATA MSG
        rfc5424_pattern = r"^<(\d{1,3})>(\d{1,2})\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+|\[.*?\])(?:\s+(.*))?$"
        match_5424 = re.match(rfc5424_pattern, message)
        if match_5424:
            return {
                "format": "RFC5424",
                "priority": pri_data,
                "version": match_5424.group(2),
                "timestamp": match_5424.group(3),
                "hostname": match_5424.group(4),
                "app_name": match_5424.group(5),
                "procid": match_5424.group(6),
                "msgid": match_5424.group(7),
                "structured_data": match_5424.group(8),
                "message": match_5424.group(9) or ""
            }

        # RFC3164
        # <PRIVAL>TIMESTAMP HOSTNAME TAG: MSG
        rfc3164_pattern = r"^<(\d{1,3})>([A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+(\S+)\s+([^:]+):\s*(.*)$"
        match_3164 = re.match(rfc3164_pattern, message)
        if match_3164:
            tag = match_3164.group(4)
            app_name = tag
            procid = "-"
            tag_match = re.match(r"^([^\[]+)(?:\[(\d+)\])?$", tag)
            if tag_match:
                app_name = tag_match.group(1)
                procid = tag_match.group(2) if tag_match.group(2) else "-"

            return {
                "format": "RFC3164",
                "priority": pri_data,
                "timestamp": match_3164.group(2),
                "hostname": match_3164.group(3),
                "app_name": app_name,
                "procid": procid,
                "message": match_3164.group(5)
            }

        return {
            "format": "Unknown (Has Priority)",
            "priority": pri_data,
            "message": message[len(pri_match.group(0)):]
        }

def run_syslog_lab_logic(args) -> None:
    if getattr(args, "action", "") == "tui":
        from shared.tui import AgentTUI
        app = AgentTUI(project_dir=getattr(args, 'project_dir', None), start_tab="tab-syslog")
        app.run()
        sys.exit(0)

    manager = SyslogLabManager()

    if getattr(args, "action", "") == "parse":
        try:
            result = manager.parse(args.message)
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(f"Error parsing syslog: {e}", file=sys.stderr)
            sys.exit(1)
