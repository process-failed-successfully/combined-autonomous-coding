# from textual.widgets import Label

class MockLabel:
    def __init__(self, text):
        self.text = text

def run_hello(args):
    print(f"Hello, {args.name}!")

def register_cli(subparsers):
    parser = subparsers.add_parser("hello", help="Prints hello")
    parser.add_argument("name", help="Name to greet")
    parser.set_defaults(run_plugin_func=run_hello)

def register_tui():
    return ("Hello", MockLabel("Hello from Plugin!"))
