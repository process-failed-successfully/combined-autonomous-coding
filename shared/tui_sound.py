from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label, Input, Button, Select, TabbedContent, TabPane, Static
from textual import on
from pathlib import Path
from shared.sound_lab import SoundLabManager

class SoundLabTab(Container):
    """Tab for Sound Lab (Tone, Noise, DTMF, Morse)."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = SoundLabManager(project_dir)
        self.last_samples = []

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Sound Lab[/bold]", classes="welcome-text")

            with TabbedContent(id="sound-tabs"):
                # --- TONE ---
                with TabPane("Tone", id="tab-tone"):
                    with Horizontal(classes="stat-box"):
                        with Vertical():
                            yield Label("Frequency (Hz):")
                            yield Input(placeholder="440.0", id="tone-freq", value="440.0")
                        with Vertical():
                            yield Label("Duration (s):")
                            yield Input(placeholder="1.0", id="tone-duration", value="1.0")
                        with Vertical():
                            yield Label("Waveform:")
                            yield Select.from_values(["sine", "square", "sawtooth", "triangle"], id="tone-wave", value="sine")

                    with Horizontal(classes="stat-box"):
                        yield Button("Generate Tone", id="btn-gen-tone", variant="primary")
                        yield Button("Save", id="btn-save-tone", variant="success")

                # --- NOISE ---
                with TabPane("Noise", id="tab-noise"):
                    with Horizontal(classes="stat-box"):
                        with Vertical():
                            yield Label("Duration (s):")
                            yield Input(placeholder="1.0", id="noise-duration", value="1.0")
                        with Vertical():
                            yield Label("Type:")
                            yield Select.from_values(["white"], id="noise-type", value="white")

                    with Horizontal(classes="stat-box"):
                        yield Button("Generate Noise", id="btn-gen-noise", variant="primary")
                        yield Button("Save", id="btn-save-noise", variant="success")

                # --- DTMF ---
                with TabPane("DTMF", id="tab-dtmf"):
                    with Vertical(classes="stat-box"):
                        yield Label("Sequence:")
                        yield Input(placeholder="0123456789ABCD*#", id="dtmf-seq", value="123")

                    with Horizontal(classes="stat-box"):
                        yield Button("Generate DTMF", id="btn-gen-dtmf", variant="primary")
                        yield Button("Save", id="btn-save-dtmf", variant="success")

                # --- MORSE ---
                with TabPane("Morse", id="tab-morse"):
                    with Vertical(classes="stat-box"):
                        yield Label("Text:")
                        yield Input(placeholder="HELLO WORLD", id="morse-text", value="SOS")
                        with Horizontal():
                            yield Label("WPM:")
                            yield Input(placeholder="20", id="morse-wpm", value="20")
                            yield Label("Frequency:")
                            yield Input(placeholder="600", id="morse-freq", value="600")

                    with Horizontal(classes="stat-box"):
                        yield Button("Generate Morse", id="btn-gen-morse", variant="primary")
                        yield Button("Save", id="btn-save-morse", variant="success")

            # --- PREVIEW ---
            with Vertical(classes="stat-box", id="sound-preview-container"):
                yield Label("[bold]Waveform Visualization (First 200 samples)[/bold]")
                yield Static(id="sound-visualizer", classes="code-box")
                yield Label("", id="sound-status")

    def render_waveform(self, samples: list[float], width: int = 100) -> str:
        """Renders an ASCII waveform."""
        if not samples:
            return "No data."

        # Take a slice of reasonable size to show the wave shape
        # Showing too many samples in one line is hard without sub-sampling.
        # Let's show first 200 samples.
        slice_size = min(len(samples), 200)
        data = samples[:slice_size]

        # We can try to fit it into 'width' chars by subsampling if needed
        step = max(1, len(data) // width)
        data = data[::step]

        chars = " ▂▃▄▅▆▇█"
        result = ""
        for s in data:
            # Normalize -1..1 to 0..1
            n = (s + 1.0) / 2.0
            idx = int(n * (len(chars) - 1))
            idx = max(0, min(idx, len(chars) - 1))
            result += chars[idx]
        return result

    @on(Button.Pressed)
    def on_button_click(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if "tone" in bid: self.handle_tone(bid)
        elif "noise" in bid: self.handle_noise(bid)
        elif "dtmf" in bid: self.handle_dtmf(bid)
        elif "morse" in bid: self.handle_morse(bid)

    def update_visualizer(self, samples: list[float]) -> None:
        self.last_samples = samples
        vis = self.query_one("#sound-visualizer", Static)
        width = vis.size.width or 80

        waveform = self.render_waveform(samples, width=width)
        vis.update(waveform)
        self.query_one("#sound-status", Label).update(f"Generated {len(samples)} samples.")

    def handle_tone(self, bid: str) -> None:
        try:
            freq = float(self.query_one("#tone-freq", Input).value or 440)
            dur = float(self.query_one("#tone-duration", Input).value or 1.0)
            wave = self.query_one("#tone-wave", Select).value or "sine"

            if bid == "btn-gen-tone":
                samples = self.manager.get_tone_samples(freq, dur, wave)
                self.update_visualizer(samples)
            elif bid == "btn-save-tone":
                path = self.manager.generate_tone(freq, dur, wave, output_path="tone.wav")
                self.notify(f"Saved to {path}")
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

    def handle_noise(self, bid: str) -> None:
        try:
            dur = float(self.query_one("#noise-duration", Input).value or 1.0)
            ntype = self.query_one("#noise-type", Select).value or "white"

            if bid == "btn-gen-noise":
                samples = self.manager.get_noise_samples(ntype, dur)
                self.update_visualizer(samples)
            elif bid == "btn-save-noise":
                path = self.manager.generate_noise(ntype, dur, output_path="noise.wav")
                self.notify(f"Saved to {path}")
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

    def handle_dtmf(self, bid: str) -> None:
        try:
            seq = self.query_one("#dtmf-seq", Input).value
            if not seq: return

            if bid == "btn-gen-dtmf":
                samples = self.manager.get_dtmf_samples(seq)
                self.update_visualizer(samples)
            elif bid == "btn-save-dtmf":
                path = self.manager.generate_dtmf(seq, output_path="dtmf.wav")
                self.notify(f"Saved to {path}")
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

    def handle_morse(self, bid: str) -> None:
        try:
            text = self.query_one("#morse-text", Input).value
            wpm = int(self.query_one("#morse-wpm", Input).value or 20)
            freq = float(self.query_one("#morse-freq", Input).value or 600)

            if not text: return

            if bid == "btn-gen-morse":
                samples = self.manager.get_morse_samples(text, wpm, freq)
                self.update_visualizer(samples)
            elif bid == "btn-save-morse":
                path = self.manager.generate_morse(text, output_path="morse.wav", wpm=wpm, frequency=freq)
                self.notify(f"Saved to {path}")
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")
