import sys
import re
from pathlib import Path

# Regex to detect the start of a log entry
LOG_ENTRY_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} - (INFO|DEBUG|WARNING|ERROR) -")

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def parse_log_file(log_path):
    """Parses a log file into a list of structured events."""
    events = []
    try:
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        current_event_content = []
        for line in lines:
            if LOG_ENTRY_PATTERN.match(line) and current_event_content:
                # Start of a new event, so save the current one
                events.append("".join(current_event_content))
                current_event_content = [line]
            else:
                # Continuation of the current event
                current_event_content.append(line)

        # Add the last event
        if current_event_content:
            events.append("".join(current_event_content))

    except IOError as e:
        print(f"❌ Error reading log file: {e}", file=sys.stderr)
        return None
    return events

def display_event(event, event_number, total_events):
    """Clears the screen and displays a single log event."""
    # Simple clear screen for Unix-like systems and Windows
    print("\033[H\033[J", end="")

    header = f"--- Event {event_number}/{total_events} ---"
    print(bcolors.HEADER + bcolors.BOLD + header + bcolors.ENDC)
    print(bcolors.OKCYAN + event.strip() + bcolors.ENDC)
    print(bcolors.HEADER + bcolors.BOLD + "-" * len(header) + bcolors.ENDC)

def run_replay(args):
    """Interactively replays a previous agent run from its log file."""
    project_dir = args.project_dir.resolve()
    run_id = args.run_id

    # 1. Determine the Run ID
    if not run_id:
        history_file = project_dir / ".agent_history"
        if not history_file.exists():
            print("❌ Error: No agent run history found for this project.", file=sys.stderr)
            sys.exit(1)
        try:
            with open(history_file, "r") as f:
                run_ids = [line.strip() for line in f if line.strip()]
            if not run_ids:
                print("❌ Error: Agent history is empty.", file=sys.stderr)
                sys.exit(1)
            run_id = run_ids[-1]
            print(f"No Run ID specified. Replaying the latest run: {run_id}")
        except IOError as e:
            print(f"❌ Error reading history file: {e}", file=sys.stderr)
            sys.exit(1)

    # 2. Find and parse the log file
    repo_root = Path(__file__).parent.parent
    log_file = repo_root / f"agents/logs/{run_id}.log"

    if not log_file.exists():
        print(f"❌ Error: Log file not found for Run ID '{run_id}'.", file=sys.stderr)
        print(f"  - Searched at: {log_file}", file=sys.stderr)
        sys.exit(1)

    events = parse_log_file(log_file)
    if not events:
        print("No events found in the log file. Is it empty or malformed?", file=sys.stderr)
        sys.exit(1)

    # 3. Start interactive replay loop
    current_step = 0
    total_steps = len(events)

    while True:
        display_event(events[current_step], current_step + 1, total_steps)

        prompt = (f"Navigate with: (n)ext, (b)ack, (j)ump, (q)uit "
                  f"[{bcolors.BOLD}{current_step + 1}/{total_steps}{bcolors.ENDC}]> ")
        try:
            action = input(prompt).strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting replay.")
            break

        if action == 'n':
            if current_step < total_steps - 1:
                current_step += 1
            else:
                print("Already at the last event.")
                input("Press Enter to continue...")
        elif action == 'b':
            if current_step > 0:
                current_step -= 1
            else:
                print("Already at the first event.")
                input("Press Enter to continue...")
        elif action == 'j':
            try:
                jump_to = int(input(f"Jump to event (1-{total_steps}): ").strip()) - 1
                if 0 <= jump_to < total_steps:
                    current_step = jump_to
                else:
                    print(f"Invalid event number. Please enter a number between 1 and {total_steps}.")
                    input("Press Enter to continue...")
            except ValueError:
                print("Invalid input. Please enter a number.")
                input("Press Enter to continue...")
        elif action == 'q':
            print("Exiting replay.")
            break
        else:
            print(f"Unknown command: '{action}'")
            input("Press Enter to continue...")

    sys.exit(0)
