import cmd
import readline
import sys
import shlex
import asyncio

class InteractiveShell(cmd.Cmd):
    """
    An interactive shell for managing the autonomous coding agent.
    All commands from main.py are dynamically available.
    """
    intro = "Welcome to the agent interactive shell. Type help or ? to list commands.\n"
    prompt = "(agent) "

    def __init__(self, main_module):
        super().__init__()
        self.main_module = main_module
        self.parser = main_module.get_parser()

    def default(self, line):
        """
        Default handler for any command that doesn't have a do_* method.
        This method dynamically dispatches commands to the main_module.
        """
        if line.strip() in ['exit', 'quit', 'EOF']:
            return self.do_exit(line)

        argv = shlex.split(line)
        if not argv:
            return

        try:
            # We need to temporarily patch sys.exit to prevent it from killing the shell
            original_exit = sys.exit
            sys.exit = self._handle_exit

            args = self.parser.parse_args(argv)

            # Find the function to call, e.g., 'run_status'
            if hasattr(args, 'command') and args.command:
                func_name = f"_run_{args.command.replace('-', '_')}_logic"

                if hasattr(self.main_module, func_name):
                    func = getattr(self.main_module, func_name)

                    # For async functions like run_plan, we need to run them in an event loop
                    if asyncio.iscoroutinefunction(func):
                        asyncio.run(func(args))
                    else:
                        func(args)
                else:
                    print(f"*** Unknown command: {args.command}")
            else:
                # This case might be for commands that are not subparsers.
                # Or when no command is given, which should show help.
                self.parser.print_help()

        except SystemExit as e:
            # This will catch argparse's help messages and errors
            if e.code != 0:
                # Argparse has already printed the error message
                pass
        except Exception as e:
            print(f"*** Error: {e}")
        finally:
            sys.exit = original_exit

    def _handle_exit(self, code=0):
        """A patched version of sys.exit that raises a SystemExit exception."""
        raise SystemExit(code)

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
