import argparse
from textual.widgets import Label

def register_cli(subparsers):
    """Registers a CLI command."""
    parser = subparsers.add_parser("my-command", help="My custom plugin command")
    parser.set_defaults(func=run_my_command)

def run_my_command(args):
    print("Hello from my custom plugin!")

def register_tui():
    """Registers a TUI tab. Returns (Title, WidgetInstance)."""
    return ("My Tab", Label("Hello from Plugin TUI!"))