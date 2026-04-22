with open("main.py", "r") as f:
    content = f.read()

# Add to KNOWN_COMMANDS
known_cmds_str = '"uuid-lab", "uuid",'
if '"ksuid-lab", "ksuid",' not in content:
    content = content.replace(known_cmds_str, '"ksuid-lab", "ksuid", ' + known_cmds_str)

# Add CLI run_ksuid_lab logic block
run_func_block = """def run_ksuid_lab(args):
    \"\"\"Runs the KSUID Lab.\"\"\"
    if args.action == "tui":
        from shared.tui import AgentTUI
        print("Launching KSUID Lab TUI...")
        app = AgentTUI(project_dir=args.project_dir, start_tab="tab-ksuid")
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

    from shared.ksuid_lab import run_ksuid_lab_logic
    run_ksuid_lab_logic(args)
    sys.exit(0)

def run_uuid_lab"""

if "def run_ksuid_lab(args):" not in content:
    content = content.replace("def run_uuid_lab", run_func_block)

# Add subparser registration
parser_block = """    parser_ksuid = subparsers.add_parser(
        "ksuid-lab",
        aliases=["ksuid"],
        help="KSUID Generator and Inspector."
    )
    ksuid_subparsers = parser_ksuid.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # ksuid generate
    parser_ksuid_gen = ksuid_subparsers.add_parser("generate", aliases=["gen"], help="Generate KSUIDs.")
    parser_ksuid_gen.add_argument("--count", "-c", type=int, default=1, help="Number of KSUIDs to generate.")

    # ksuid inspect
    parser_ksuid_inspect = ksuid_subparsers.add_parser("inspect", aliases=["decode"], help="Inspect a KSUID.")
    parser_ksuid_inspect.add_argument("ksuid", help="The KSUID to inspect.")

    # ksuid tui
    parser_ksuid_tui = ksuid_subparsers.add_parser("tui", help="Launch KSUID Lab TUI.")

    parser_uuid = subparsers.add_parser("""

if "parser_ksuid = subparsers.add_parser(" not in content:
    content = content.replace("    parser_uuid = subparsers.add_parser(", parser_block)

# Add run command dispatch logic
dispatch_block = """    if args.command in ["ksuid-lab", "ksuid"]:
        run_ksuid_lab(args)
        return

    if args.command in ["uuid-lab", "uuid"]:"""

if "if args.command in [\"ksuid-lab\", \"ksuid\"]:" not in content:
    content = content.replace("    if args.command in [\"uuid-lab\", \"uuid\"]:", dispatch_block)

with open("main.py", "w") as f:
    f.write(content)
