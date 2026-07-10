import sys
import re
from typing import Dict, Tuple, Optional, Any

class Cron2SystemdManager:
    """
    Parses a crontab line and converts it into Systemd .service and .timer files.
    """

    def _convert_cron_field(self, field: str) -> str:
        """
        Converts a single cron field (like */5, 1-5, or 10) into a systemd-compatible segment.
        Note: Systemd OnCalendar is quite flexible, but has a different syntax.
        """
        if field == '*':
            return '*'

        # Systemd uses / for steps as well, but it might require a start value.
        # e.g., */5 in cron is often 0/5 in systemd, but systemd accepts /5 for minutes.
        # Let's do a direct translation and let systemd interpret it.
        # E.g., */15 -> 0/15 or just */15 (valid in systemd for Time fields)
        return field

    def _map_dow(self, dow: str) -> str:
        """
        Maps cron day-of-week to systemd day-of-week.
        Cron: 0-6 (Sun-Sat) or 1-7 (Mon-Sun).
        Systemd: Mon, Tue, Wed, Thu, Fri, Sat, Sun.
        """
        if dow == '*':
            return ''

        mapping = {
            '0': 'Sun', '7': 'Sun',
            '1': 'Mon', '2': 'Tue', '3': 'Wed',
            '4': 'Thu', '5': 'Fri', '6': 'Sat',
            'sun': 'Sun', 'mon': 'Mon', 'tue': 'Tue', 'wed': 'Wed',
            'thu': 'Thu', 'fri': 'Fri', 'sat': 'Sat'
        }

        parts = dow.split(',')
        res = []
        for p in parts:
            p_lower = p.lower()
            if p_lower in mapping:
                res.append(mapping[p_lower])
            elif '-' in p_lower:
                start, end = p_lower.split('-', 1)
                res.append(f"{mapping.get(start, start)}-{mapping.get(end, end)}")
            else:
                res.append(p)
        return ','.join(res)

    def parse_cron(self, cron_line: str) -> Dict[str, str]:
        """
        Parses a standard cron line:
        min hour dom mon dow [user] command
        """
        cron_line = cron_line.strip()
        if not cron_line or cron_line.startswith('#'):
             raise ValueError("Empty or commented cron line")

        parts = re.split(r'\s+', cron_line, maxsplit=6)
        if len(parts) < 6:
             raise ValueError("Invalid cron line format. Expected at least 6 fields (min hour dom mon dow command)")

        min_f, hour_f, dom_f, mon_f, dow_f = parts[:5]

        # Check if 6th field is a user (alphanumeric without special chars common in commands, usually no slashes)
        # It's ambiguous. In user crontabs, it's 5 fields + command. In /etc/crontab it's 5 fields + user + command.
        # We'll assume standard user crontab (5 time fields + command) for simplicity,
        # but try to detect if 6th field looks like a simple username without slashes or quotes.
        user = "root"
        command = parts[5]

        # We need a more reliable way to detect user crontabs vs system crontabs.
        # Typically users pass standard 5-field crontabs.
        # Let's assume the 6th field is a user only if it matches common user patterns
        # AND it is not a common binary/command name. To keep it simple and robust,
        # we will require users to provide the username as an explicit command-line argument
        # or we just assume the rest of the string is the command unless there are exactly 7 parts
        # and the 6th part is "root" or similar.

        # Actually, let's look at standard cron. If 6th field is a known user, or just word characters
        # followed by an absolute path, it might be a user.
        # A simpler, much more robust approach:
        # Assume it's a 5-field cron (no user) by default.
        command_start_idx = 5
        potential_user = parts[5]

        # System crontabs almost always use 'root' or specific system users.
        # Let's just check if it's explicitly 'root' or matches a strict set of system users,
        # or we look at how many fields are left.
        if len(parts) >= 7 and potential_user in ['root', 'daemon', 'bin', 'sys', 'sync', 'games', 'man', 'lp', 'mail', 'news', 'uucp', 'proxy', 'www-data', 'backup', 'list', 'irc', 'gnats', 'nobody', 'systemd-network', 'systemd-resolve', 'syslog', 'messagebus', '_apt']:
            user = potential_user
            command_start_idx = 6

        command = " ".join(parts[command_start_idx:])

        # Construct OnCalendar string: DayOfWeek Year-Month-Day Hour:Minute:Second
        sys_dow = self._map_dow(dow_f)

        sys_mon = self._convert_cron_field(mon_f)
        sys_dom = self._convert_cron_field(dom_f)
        sys_hour = self._convert_cron_field(hour_f)
        sys_min = self._convert_cron_field(min_f)

        # Systemd format: DayOfWeek Year-Month-Day Hour:Minute:Second
        # E.g. *-*-* *:*:00

        date_part = f"*-{sys_mon}-{sys_dom}"
        time_part = f"{sys_hour}:{sys_min}:00"

        on_calendar = f"{date_part} {time_part}"
        if sys_dow:
            on_calendar = f"{sys_dow} {on_calendar}"

        return {
            "on_calendar": on_calendar,
            "user": user,
            "command": command
        }

    def generate_files(self, name: str, cron_line: str, description: str = "") -> Tuple[str, str]:
        """
        Generates the .service and .timer file contents.
        Returns (service_content, timer_content).
        """
        parsed = self.parse_cron(cron_line)

        if not description:
            description = f"Cron-to-Systemd job: {name}"

        service = f"""[Unit]
Description={description}

[Service]
Type=oneshot
User={parsed['user']}
ExecStart={parsed['command']}
"""

        timer = f"""[Unit]
Description={description} timer

[Timer]
OnCalendar={parsed['on_calendar']}
Persistent=true

[Install]
WantedBy=timers.target
"""
        return service, timer

def run_cron2systemd_lab_logic(args) -> bool:
    """CLI logic for Cron to Systemd Lab."""
    manager = Cron2SystemdManager()

    if getattr(args, "action", None) == "tui" or getattr(args, "tui", False):
        from shared.tui import AgentTUI
        print("Launching Cron2Systemd Lab TUI...")
        app = AgentTUI(project_dir=getattr(args, 'project_dir', None), start_tab="tab-cron2systemd")
        import asyncio
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if getattr(args, '_in_event_loop', False) or (loop and loop.is_running()):
            asyncio.ensure_future(app.run_async())
            return True
        else:
            app.run()
            sys.exit(0)
            return True

    if not getattr(args, "cron_line", None):
        print("Error: --cron-line is required.", file=sys.stderr)
        return False

    name = getattr(args, "name", "cronjob")
    desc = getattr(args, "description", "")

    try:
        service_content, timer_content = manager.generate_files(name, args.cron_line, desc)

        if getattr(args, "out_dir", None):
            import os
            from pathlib import Path
            out_dir = Path(args.out_dir)
            out_dir.mkdir(parents=True, exist_ok=True)

            service_path = out_dir / f"{name}.service"
            timer_path = out_dir / f"{name}.timer"

            service_path.write_text(service_content)
            timer_path.write_text(timer_content)
            print(f"✅ Generated {service_path}")
            print(f"✅ Generated {timer_path}")
        else:
            print(f"--- {name}.service ---")
            print(service_content)
            print(f"--- {name}.timer ---")
            print(timer_content)

        return True
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return False
