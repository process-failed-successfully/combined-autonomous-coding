import sys

def patch_tui_hex():
    with open('shared/tui_hex.py', 'r') as f:
        content = f.read()

    old_compose = """    def compose(self) -> ComposeResult:
        with Horizontal(classes="hex-header"):
            yield Label("File:", classes="label")
            yield Input(placeholder="Path to file...", id="hex-file-input")
            yield Button("Load", id="btn-hex-load", variant="primary")
            yield Button("Save", id="btn-hex-save", variant="success", disabled=True)

        yield DataTable(id="hex-grid")
        yield Label("Ready", id="hex-status", classes="hex-status")"""

    new_compose = """    def compose(self) -> ComposeResult:
        with Vertical():
            with Horizontal(classes="hex-header"):
                yield Label("File:", classes="label")
                yield Input(placeholder="Path to file...", id="hex-file-input")
                yield Button("Load", id="btn-hex-load", variant="primary")
                yield Button("Save", id="btn-hex-save", variant="success", disabled=True)

            yield DataTable(id="hex-grid")
            yield Label("Ready", id="hex-status", classes="hex-status")"""

    if old_compose in content:
        content = content.replace(old_compose, new_compose)
        with open('shared/tui_hex.py', 'w') as f:
            f.write(content)
        print("Patched tui_hex.py successfully.")
    else:
        print("Could not find old_compose in tui_hex.py")

if __name__ == '__main__':
    patch_tui_hex()
