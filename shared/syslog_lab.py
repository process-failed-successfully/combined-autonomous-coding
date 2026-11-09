import re
from typing import Dict, Any

class SyslogLabManager:
    """Manages Syslog operations (parsing RFC 3164 and RFC 5424)."""

    FACILITIES = [
        "kernel messages", "user-level messages", "mail system", "system daemons",
        "security/authorization messages", "messages generated internally by syslogd",
        "line printer subsystem", "network news subsystem", "UUCP subsystem",
        "clock daemon", "security/authorization messages", "FTP daemon",
        "NTP subsystem", "log audit", "log alert", "clock daemon",
        "local use 0", "local use 1", "local use 2", "local use 3",
        "local use 4", "local use 5", "local use 6", "local use 7"
    ]

    SEVERITIES = [
        "Emergency", "Alert", "Critical", "Error",
        "Warning", "Notice", "Informational", "Debug"
    ]

    def decode_pri(self, pri: int) -> Dict[str, Any]:
        """Decodes the Priority (PRI) value into Facility and Severity."""
        facility = pri // 8
        severity = pri % 8
        return {
            "facility_code": facility,
            "facility": self.FACILITIES[facility] if 0 <= facility < len(self.FACILITIES) else "unknown",
            "severity_code": severity,
            "severity": self.SEVERITIES[severity] if 0 <= severity < len(self.SEVERITIES) else "unknown"
        }

    def parse(self, message: str) -> Dict[str, Any]:
        """Parses a syslog message (RFC 3164 or RFC 5424)."""
        message = message.strip()
        if not message.startswith("<"):
            raise ValueError("Invalid syslog message: missing <PRI>")

        pri_end = message.find(">")
        if pri_end == -1:
            raise ValueError("Invalid syslog message: missing > in PRI")

        try:
            pri = int(message[1:pri_end])
        except ValueError:
            raise ValueError("Invalid PRI value")

        pri_info = self.decode_pri(pri)

        # Try parsing as RFC 5424
        rfc5424_match = re.match(r'^<(\d+)>(\d+)\s+([^ ]+)\s+([^ ]+)\s+([^ ]+)\s+([^ ]+)\s+([^ ]+)\s+(?:(\[.*?\])|-)\s*(.*)$', message)
        if rfc5424_match:
            return {
                "type": "RFC 5424",
                "pri": pri,
                **pri_info,
                "version": int(rfc5424_match.group(2)),
                "timestamp": rfc5424_match.group(3) if rfc5424_match.group(3) != '-' else None,
                "hostname": rfc5424_match.group(4) if rfc5424_match.group(4) != '-' else None,
                "app_name": rfc5424_match.group(5) if rfc5424_match.group(5) != '-' else None,
                "procid": rfc5424_match.group(6) if rfc5424_match.group(6) != '-' else None,
                "msgid": rfc5424_match.group(7) if rfc5424_match.group(7) != '-' else None,
                "structured_data": rfc5424_match.group(8) if rfc5424_match.group(8) != '-' else None,
                "message": rfc5424_match.group(9)
            }

        # Try parsing as RFC 3164
        # A valid RFC 3164 message MUST have a timestamp (Mmm dd hh:mm:ss)
        # and a hostname/IP (although hostname can sometimes be missing, timestamp is strictly required by the RFC for detection)
        rfc3164_pattern = r'^<(\d+)>([A-Z][a-z]{2}\s+\d+\s+\d{2}:\d{2}:\d{2})\s+([\w\.\-]+)?\s*(.*)$'
        m = re.match(rfc3164_pattern, message)

        if m:
            rest = m.group(4)
            tag_msg_match = re.match(r'^([^:\[\s]+)(?:\[(\d+)\])?(?::\s*|\s+)(.*)$', rest)

            tag = None
            pid = None
            msg = rest
            if tag_msg_match:
                tag = tag_msg_match.group(1)
                pid = tag_msg_match.group(2)
                msg = tag_msg_match.group(3)

            return {
                "type": "RFC 3164",
                "pri": pri,
                **pri_info,
                "timestamp": m.group(2),
                "hostname": m.group(3),
                "tag": tag,
                "pid": pid,
                "message": msg
            }

        return {
            "type": "Unknown",
            "pri": pri,
            **pri_info,
            "message": message[pri_end+1:].strip()
        }
