import sys

def patch_main():
    with open('main.py', 'r') as f:
        content = f.read()

    # Insert import
    import_statement = "from shared.typegen_lab import run_typegen_lab_logic\n"
    if "from shared.typegen_lab" not in content:
        content = content.replace("from shared.stego_lab import run_stego_lab_logic\n", "from shared.stego_lab import run_stego_lab_logic\n" + import_statement)

    # Insert argument parsing
    arg_parsing = """    # --- Typegen Lab ---
    parser_typegen = subparsers.add_parser(
        "typegen-lab", aliases=["typegen"],
        help="Generate type definitions from JSON."
    )
    typegen_subparsers = parser_typegen.add_subparsers(dest="action", help="Typegen actions")

    typegen_generate = typegen_subparsers.add_parser("generate", help="Generate types from JSON")
    typegen_generate.add_argument("--json", help="JSON string to convert")
    typegen_generate.add_argument("--file", "-f", help="Path to JSON file")
    typegen_generate.add_argument("--lang", "-l", choices=["typescript", "go", "python", "rust"], default="typescript", help="Target language")
    typegen_generate.add_argument("--name", "-n", default="Root", help="Name of the root struct/interface")
    typegen_generate.add_argument("--output", "-o", help="File to write generated types to")

    typegen_subparsers.add_parser("tui", help="Launch the Typegen Lab TUI")

"""
    if "parser_typegen = subparsers.add_parser" not in content:
        content = content.replace("    # --- Stego Lab ---", arg_parsing + "    # --- Stego Lab ---")

    # Insert command routing
    cmd_routing = """    if args.command in ["typegen-lab", "typegen"]:
        if getattr(args, "action", None) == "tui" or getattr(args, "tui", False):
            from shared.tui import AgentTUI
            print("Launching Typegen Lab TUI...")
            app = AgentTUI(project_dir=getattr(args, 'project_dir', Path(".")), start_tab="tab-typegen")
            import asyncio
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None
            if loop and loop.is_running():
                asyncio.ensure_future(app.run_async())
            else:
                app.run()
                sys.exit(0)
            return

        run_typegen_lab_logic(args)
        return

"""
    if "if args.command in [\"typegen-lab\", \"typegen\"]:" not in content:
        content = content.replace("    if args.command in [\"stego-lab\", \"stego\"]:", cmd_routing + "    if args.command in [\"stego-lab\", \"stego\"]:")

    with open('main.py', 'w') as f:
        f.write(content)

if __name__ == '__main__':
    patch_main()
