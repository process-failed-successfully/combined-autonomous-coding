from textual.widgets import Label

def register_cli(subparsers):
    """Registers a CLI command."""
    parser = subparsers.add_parser("example", help="Example Plugin Command")
    parser.set_defaults(func=run_example)

def run_example(args):
    print("This is an example plugin running!")

def register_tui():
    """Registers a TUI tab."""
    return ("Example", Label("This is an example plugin tab."))
