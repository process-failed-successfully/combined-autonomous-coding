import cmd
import readline
import sys
from typing import List

class InteractiveShell(cmd.Cmd):
    """
    An interactive shell for managing the autonomous coding agent.
    """
    intro = "Welcome to the interactive shell. Type help or ? to list commands.\\n"
    prompt = "(agent) "

    def __init__(self, main_module):
        super().__init__()
        self.main_module = main_module

    def do_exit(self, arg):
        """Exit the interactive shell."""
        print("Exiting.")
        return True

    def do_quit(self, arg):
        """Exit the interactive shell."""
        return self.do_exit(arg)

    def do_EOF(self, arg):
        """Exit the interactive shell when an EOF is received (Ctrl+D)."""
        print()
        return self.do_exit(arg)

    def emptyline(self):
        """Do nothing on an empty line."""
        pass

    def do_status(self, arg):
        """Displays the current status of the agent project."""
        args = self.parse_args(arg)
        project_dir = args.project_dir if 'project_dir' in args else '.'
        self.main_module._run_status_logic(project_dir=project_dir)

    def do_logs(self, arg):
        """Displays agent logs. Usage: logs [run_id]"""
        args = self.parse_args(arg)
        run_id = args.args[0] if args.args else None
        self.main_module._run_logs_logic(run_id=run_id)

    def do_summary(self, arg):
        """Displays a high-level summary of the project's status."""
        args = self.parse_args(arg)
        project_dir = args.project_dir if 'project_dir' in args else '.'
        self.main_module._run_summary_logic(project_dir=project_dir)

    def do_history(self, arg):
        """Displays a history of agent runs for the project."""
        args = self.parse_args(arg)
        project_dir = args.project_dir if 'project_dir' in args else '.'
        self.main_module._run_history_logic(project_dir=project_dir)

    def do_diff_summary(self, arg):
        """Displays a summary of uncommitted git changes."""
        args = self.parse_args(arg)
        project_dir = args.project_dir if 'project_dir' in args else '.'
        self.main_module._run_diff_summary_logic(project_dir=project_dir)

    def parse_args(self, arg_str):
        """Helper to parse arguments from the shell."""
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument('-p', '--project-dir', type=str, default='.')
        parser.add_argument('args', nargs=argparse.REMAINDER)
        # Use shlex to handle quoted arguments
        import shlex
        return parser.parse_args(shlex.split(arg_str))
