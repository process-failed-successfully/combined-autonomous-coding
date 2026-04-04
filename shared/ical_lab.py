import sys
import datetime
import re

class ICalManager:
    """Manages parsing, generating, and validating iCalendar (RFC 5545) data."""

    def __init__(self):
        pass

    def parse_ics(self, text: str) -> list[dict]:
        """Parses an iCalendar string and extracts VEVENTs."""
        events = []
        in_event = False
        current_event = {}

        # Unfold lines (RFC 5545 section 3.1)
        # Lines ending in CRLF followed immediately by a space or tab are unfolded
        unfolded_text = re.sub(r'\r?\n[ \t]', '', text)

        lines = unfolded_text.splitlines()
        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith("BEGIN:VEVENT"):
                in_event = True
                current_event = {}
            elif line.startswith("END:VEVENT"):
                if in_event:
                    events.append(current_event)
                in_event = False
            elif in_event:
                if ":" in line:
                    key, value = line.split(":", 1)
                    # Handle parameters like DTSTART;TZID=America/New_York
                    if ";" in key:
                        key = key.split(";")[0]

                    key = key.upper()
                    # Unescape text
                    value = value.replace(r"\,", ",").replace(r"\;", ";").replace(r"\n", "\n").replace(r"\N", "\n").replace(r"\\", "\\")
                    current_event[key] = value

        return events

    def generate_ics(self, summary: str, dtstart: datetime.datetime, dtend: datetime.datetime, location: str = "", description: str = "") -> str:
        """Generates a simple iCalendar string."""
        now = datetime.datetime.now(datetime.timezone.utc)

        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Combined Autonomous Coding Agent//ICal Lab//EN",
            "CALSCALE:GREGORIAN",
            "BEGIN:VEVENT"
        ]

        uid = f"{now.strftime('%Y%m%dT%H%M%SZ')}-{hash(summary)}@ical-lab"
        lines.append(f"UID:{uid}")
        lines.append(f"DTSTAMP:{now.strftime('%Y%m%dT%H%M%SZ')}")

        # Format dates (assuming naive or UTC for simplicity in this lab)
        start_str = dtstart.strftime('%Y%m%dT%H%M%SZ') if dtstart.tzinfo else dtstart.strftime('%Y%m%dT%H%M%S')
        end_str = dtend.strftime('%Y%m%dT%H%M%SZ') if dtend.tzinfo else dtend.strftime('%Y%m%dT%H%M%S')

        lines.append(f"DTSTART:{start_str}")
        lines.append(f"DTEND:{end_str}")

        def escape_text(t: str) -> str:
            return t.replace("\\", "\\\\").replace(";", r"\;").replace(",", r"\,").replace("\n", r"\n")

        if summary:
            lines.append(f"SUMMARY:{escape_text(summary)}")
        if location:
            lines.append(f"LOCATION:{escape_text(location)}")
        if description:
            lines.append(f"DESCRIPTION:{escape_text(description)}")

        lines.extend([
            "END:VEVENT",
            "END:VCALENDAR"
        ])

        # Wrap lines longer than 75 octets (RFC 5545 section 3.1)
        wrapped_lines = []
        for line in lines:
            while len(line) > 75:
                wrapped_lines.append(line[:75])
                line = " " + line[75:]
            wrapped_lines.append(line)

        return "\r\n".join(wrapped_lines) + "\r\n"

    def validate_ics(self, text: str) -> bool:
        """Basic validation to check if text resembles an iCalendar file."""
        if not text:
            return False

        text = text.strip()
        has_begin = text.startswith("BEGIN:VCALENDAR") or "BEGIN:VCALENDAR\r\n" in text or "BEGIN:VCALENDAR\n" in text
        has_end = text.endswith("END:VCALENDAR") or "\r\nEND:VCALENDAR" in text or "\nEND:VCALENDAR" in text
        has_version = "VERSION:" in text

        return has_begin and has_end and has_version


def run_ical_lab_logic(args):
    """CLI logic for ICal Lab."""
    manager = ICalManager()

    # If action is 'tui', we do nothing here as TUI is handled in main.py
    if getattr(args, 'action', None) == 'tui':
        return True

    text = ""
    if hasattr(args, 'text') and args.text:
        text = args.text
    elif hasattr(args, 'file') and args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                text = f.read()
        except Exception as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            sys.exit(1)
    elif not sys.stdin.isatty():
        text = sys.stdin.read()

    action = getattr(args, 'action', 'parse')

    if action == 'parse':
        if not text:
            print("Error: Input text required via --text, --file, or stdin.", file=sys.stderr)
            sys.exit(1)
        events = manager.parse_ics(text)
        import json
        print(json.dumps(events, indent=2))
        return True

    elif action == 'validate':
        if not text:
            print("Error: Input text required via --text, --file, or stdin.", file=sys.stderr)
            sys.exit(1)
        is_valid = manager.validate_ics(text)
        print("Valid iCalendar format." if is_valid else "Invalid iCalendar format.")
        if not is_valid:
            sys.exit(1)
        return True

    elif action == 'generate':
        summary = getattr(args, 'summary', 'New Event')
        start_str = getattr(args, 'start', None)
        end_str = getattr(args, 'end', None)

        if not start_str or not end_str:
            print("Error: --start and --end are required for generation (Format: YYYY-MM-DD HH:MM).", file=sys.stderr)
            sys.exit(1)

        try:
            dtstart = datetime.datetime.strptime(start_str, "%Y-%m-%d %H:%M")
            dtend = datetime.datetime.strptime(end_str, "%Y-%m-%d %H:%M")
        except ValueError:
            print("Error: Invalid date format. Use YYYY-MM-DD HH:MM.", file=sys.stderr)
            sys.exit(1)

        location = getattr(args, 'location', "")
        description = getattr(args, 'description', "")

        output = manager.generate_ics(summary, dtstart, dtend, location, description)
        print(output, end="")
        return True

    return False
