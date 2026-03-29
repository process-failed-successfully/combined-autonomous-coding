import sys

def patch_main():
    with open("main.py", "r") as f:
        content = f.read()

    # Add xpath-lab to KNOWN_COMMANDS
    if '"xpath-lab"' not in content:
        content = content.replace('"jmespath-lab", "jmespath", "jp",\n', '"jmespath-lab", "jmespath", "jp",\n    "xpath-lab", "xpath",\n')

    # Add import for xpath_lab
    if "from shared.xpath_lab import run_xpath_lab_logic" not in content:
        content = content.replace("from shared.jmespath_lab import run_jmespath_lab_logic\n", "from shared.jmespath_lab import run_jmespath_lab_logic\nfrom shared.xpath_lab import run_xpath_lab_logic\n")

    # Add run_xpath_lab function
    if "def run_xpath_lab(" not in content:
        func = """def run_xpath_lab(args):
    \"\"\"Runs the XPath Lab.\"\"\"
    if getattr(args, 'action', None) == 'tui':
        from shared.tui import AgentTUI
        print("Launching XPath Lab TUI...")
        app = AgentTUI(project_dir=getattr(args, 'project_dir', None), start_tab="tab-xpath")
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
    elif getattr(args, 'action', None) == 'evaluate':
        run_xpath_lab_logic(args)
        sys.exit(0)
    else:
        print("Error: Invalid action. Use 'tui' or 'evaluate'.", file=sys.stderr)
        sys.exit(1)

"""
        content = content.replace("def run_jmespath_lab(args):\n", func + "def run_jmespath_lab(args):\n")

    # Add parser_xpath
    if "parser_xpath =" not in content:
        parser = """    # --- XPath Lab command ---
    parser_xpath = subparsers.add_parser(
        "xpath-lab",
        aliases=["xpath"],
        help="XPath Lab utilities (evaluate, tui)."
    )
    xpath_subparsers = parser_xpath.add_subparsers(dest="action")
    xpath_tui_parser = xpath_subparsers.add_parser("tui", help="Launch XPath Lab TUI.")

    xpath_eval_parser = xpath_subparsers.add_parser("evaluate", help="Evaluate XPath expressions.")
    xpath_eval_parser.add_argument("input", help="Input XML file path or '-' for stdin.")
    xpath_eval_parser.add_argument("expression", help="XPath expression.")

"""
        content = content.replace("    # --- JMESPath Lab command ---\n", parser + "    # --- JMESPath Lab command ---\n")

    # Add dispatch logic
    if 'args.command in ["xpath-lab", "xpath"]' not in content:
        dispatch = """    if args.command in ["xpath-lab", "xpath"]:
        run_xpath_lab(args)
        return

"""
        content = content.replace('    if args.command in ["jmespath-lab", "jmespath", "jp"]:\n', dispatch + '    if args.command in ["jmespath-lab", "jmespath", "jp"]:\n')

    with open("main.py", "w") as f:
        f.write(content)

if __name__ == "__main__":
    patch_main()
