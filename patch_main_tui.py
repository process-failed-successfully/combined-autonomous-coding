import sys

with open("main.py", "r") as f:
    content = f.read()

content = content.replace("app = AgentTUI(project_dir=args.project_dir, start_tab=\"tab-nanoid\")", "from shared.tui import AgentTUI\n        app = AgentTUI(project_dir=args.project_dir, start_tab=\"tab-nanoid\")")
with open("main.py", "w") as f:
    f.write(content)
