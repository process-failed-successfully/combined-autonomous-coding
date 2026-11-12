import sys
import json
import re
from typing import Dict, Any, Optional

class SyslogLabManager:
    """Manager for parsing Syslog messages (RFC 3164 and RFC 5424)."""

    # RFC 3164 Format: <PRI>TIMESTAMP HOSTNAME APP-NAME: MSG
    # Note: APP-NAME: might not always be present or might vary, we'll use a lenient regex.
    # Timestamp is Mmm dd hh:mm:ss
    RFC3164_REGEX = re.compile(
        r"^<(?P<pri>\d+)>"
        r"(?P<timestamp>[A-Z][a-z]{2}\s+\d+\s+\d{2}:\d{2}:\d{2})\s+"
        r"(?P<hostname>[^\s]+)\s+"
        r"(?:(?P<appname>[a-zA-Z0-9_\-\.]+)(?:\[(?P<procid>\d+)\])?:\s+)?"
        r"(?P<msg>.*)$"
    )

    # RFC 5424 Format: <PRI>VERSION TIMESTAMP HOSTNAME APP-NAME PROCID MSGID STRUCTURED-DATA MSG
    RFC5424_REGEX = re.compile(
        r"^<(?P<pri>\d+)>(?P<version>\d+)\s+"
        r"(?P<timestamp>[^\s]+)\s+"
        r"(?P<hostname>[^\s]+)\s+"
        r"(?P<appname>[^\s]+)\s+"
        r"(?P<procid>[^\s]+)\s+"
        r"(?P<msgid>[^\s]+)\s+"
        r"(?P<structured_data>-|\[.*?\](?=\s|$))\s*"
        r"(?P<msg>.*)$"
    )

    def parse_syslog(self, message: str) -> Dict[str, Any]:
        """Parses a syslog message and returns a dictionary with extracted fields."""
        message = message.strip()

        # Try RFC 5424 first (more structured)
        match = self.RFC5424_REGEX.match(message)
        if match:
            parsed = match.groupdict()
            return self._enrich_parsed_data(parsed, format="RFC5424")

        # Try RFC 3164
        match = self.RFC3164_REGEX.match(message)
        if match:
            parsed = match.groupdict()
            return self._enrich_parsed_data(parsed, format="RFC3164")

        return {"error": "Invalid syslog message format", "raw": message}

    def _enrich_parsed_data(self, parsed: Dict[str, Any], format: str) -> Dict[str, Any]:
        """Enriches parsed data with calculated fields like facility and severity."""
        result = {"format": format}
        for k, v in parsed.items():
            if v == "-":
                result[k] = None
            else:
                result[k] = v

        if result.get("pri") is not None:
            try:
                pri_val = int(result["pri"])
                facility = pri_val // 8
                severity = pri_val % 8
                result["facility"] = facility
                result["severity"] = severity

                # Facility string mapping
                facilities = [
                    "kernel messages", "user-level messages", "mail system", "system daemons",
                    "security/authorization messages", "messages generated internally by syslogd",
                    "line printer subsystem", "network news subsystem", "UUCP subsystem", "clock daemon",
                    "security/authorization messages", "FTP daemon", "NTP subsystem", "log audit",
                    "log alert", "clock daemon", "local use 0", "local use 1", "local use 2",
                    "local use 3", "local use 4", "local use 5", "local use 6", "local use 7"
                ]
                result["facility_label"] = facilities[facility] if 0 <= facility < len(facilities) else "unknown"

                # Severity string mapping
                severities = [
                    "Emergency", "Alert", "Critical", "Error", "Warning", "Notice", "Informational", "Debug"
                ]
                result["severity_label"] = severities[severity] if 0 <= severity < len(severities) else "unknown"

            except ValueError:
                pass

        return result

def run_syslog_lab_logic(args):
    manager = SyslogLabManager()

    if getattr(args, "action", None) == "parse":
        result = manager.parse_syslog(args.message)
        print(json.dumps(result, indent=2))
        return True

    print("Error: Action must be 'parse' or 'tui'.")
    return False
