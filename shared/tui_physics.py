from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Label, Button, Input, Static, TabbedContent, TabPane
from textual import on
from shared.physics_lab import PhysicsLabManager

class PhysicsLabTab(Vertical):
    """A TUI tab for Physics Lab calculations."""

    def compose(self) -> ComposeResult:
        yield Label("Physics Lab - Mechanics", id="physics-title", classes="tab-title")
        with TabbedContent():
            with TabPane("Velocity (v=d/t)"):
                yield Vertical(
                    Horizontal(
                        Input(placeholder="Distance (m)", id="phys-v-d"),
                        Input(placeholder="Time (s)", id="phys-v-t"),
                        Button("Calculate", id="phys-btn-v", variant="primary")
                    ),
                    Static("", id="phys-res-v", classes="result-box")
                )
            with TabPane("Force (F=ma)"):
                yield Vertical(
                    Horizontal(
                        Input(placeholder="Mass (kg)", id="phys-f-m"),
                        Input(placeholder="Acceleration (m/s²)", id="phys-f-a"),
                        Button("Calculate", id="phys-btn-f", variant="primary")
                    ),
                    Static("", id="phys-res-f", classes="result-box")
                )
            with TabPane("Kinetic Energy"):
                yield Vertical(
                    Horizontal(
                        Input(placeholder="Mass (kg)", id="phys-k-m"),
                        Input(placeholder="Velocity (m/s)", id="phys-k-v"),
                        Button("Calculate", id="phys-btn-k", variant="primary")
                    ),
                    Static("", id="phys-res-k", classes="result-box")
                )

    @on(Button.Pressed, "#phys-btn-v")
    def calc_v(self, event: Button.Pressed) -> None:
        try:
            d = float(self.query_one("#phys-v-d").value)
            t = float(self.query_one("#phys-v-t").value)
            res = PhysicsLabManager().calculate_velocity(d, t)
            self.query_one("#phys-res-v").update(res)
        except ValueError:
            self.query_one("#phys-res-v").update("Error: Invalid input")

    @on(Button.Pressed, "#phys-btn-f")
    def calc_f(self, event: Button.Pressed) -> None:
        try:
            m = float(self.query_one("#phys-f-m").value)
            a = float(self.query_one("#phys-f-a").value)
            res = PhysicsLabManager().calculate_force(m, a)
            self.query_one("#phys-res-f").update(res)
        except ValueError:
            self.query_one("#phys-res-f").update("Error: Invalid input")

    @on(Button.Pressed, "#phys-btn-k")
    def calc_k(self, event: Button.Pressed) -> None:
        try:
            m = float(self.query_one("#phys-k-m").value)
            v = float(self.query_one("#phys-k-v").value)
            res = PhysicsLabManager().calculate_kinetic_energy(m, v)
            self.query_one("#phys-res-k").update(res)
        except ValueError:
            self.query_one("#phys-res-k").update("Error: Invalid input")
