from textual.app import App
from shared.tui_cuid2 import Cuid2LabTab

class MockApp(App):
    def compose(self):
        yield Cuid2LabTab()

app = MockApp()
app.run(headless=True)
