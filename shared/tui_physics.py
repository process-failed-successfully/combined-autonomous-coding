from textual.app import ComposeResult
from textual.widgets import Label, Button, Input, TabbedContent, TabPane, Static
from textual.containers import Container, Horizontal, Vertical
from textual import on
from shared.physics_lab import PhysicsLabManager

class PhysicsLabTab(Container):
    """Tab for Physics operations."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = PhysicsLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Physics Lab[/bold]", classes="welcome-text")

            with TabbedContent():
                # Velocity Pane
                with TabPane("Velocity"):
                    with Vertical(classes="stat-box"):
                        yield Label("Calculate Velocity (v = d / t)")
                        with Horizontal():
                            yield Input(placeholder="Distance (m)", id="input-phys-dist")
                            yield Input(placeholder="Time (s)", id="input-phys-time")
                            yield Button("Calculate", id="btn-phys-velocity", variant="primary")

                        yield Label("[bold]Result[/bold]")
                        yield Static(id="lbl-phys-velocity-result", classes="result-box")

                # Acceleration Pane
                with TabPane("Acceleration"):
                    with Vertical(classes="stat-box"):
                        yield Label("Calculate Acceleration (a = (vf - vi) / t)")
                        with Horizontal():
                            yield Input(placeholder="Initial Velocity (m/s)", id="input-phys-vi")
                            yield Input(placeholder="Final Velocity (m/s)", id="input-phys-vf")
                            yield Input(placeholder="Time (s)", id="input-phys-acc-time")
                            yield Button("Calculate", id="btn-phys-acceleration", variant="primary")

                        yield Label("[bold]Result[/bold]")
                        yield Static(id="lbl-phys-acceleration-result", classes="result-box")

                # Force Pane
                with TabPane("Force"):
                    with Vertical(classes="stat-box"):
                        yield Label("Calculate Force (F = m * a)")
                        with Horizontal():
                            yield Input(placeholder="Mass (kg)", id="input-phys-mass")
                            yield Input(placeholder="Acceleration (m/s²)", id="input-phys-acc")
                            yield Button("Calculate", id="btn-phys-force", variant="primary")

                        yield Label("[bold]Result[/bold]")
                        yield Static(id="lbl-phys-force-result", classes="result-box")

                # Energy Pane
                with TabPane("Energy"):
                    with Vertical(classes="stat-box"):
                        yield Label("Calculate Kinetic Energy (KE = 1/2 * m * v²)")
                        with Horizontal():
                            yield Input(placeholder="Mass (kg)", id="input-phys-ke-mass")
                            yield Input(placeholder="Velocity (m/s)", id="input-phys-ke-vel")
                            yield Button("Calculate KE", id="btn-phys-ke", variant="primary")

                        yield Label("Calculate Potential Energy (PE = m * g * h)")
                        with Horizontal():
                            yield Input(placeholder="Mass (kg)", id="input-phys-pe-mass")
                            yield Input(placeholder="Height (m)", id="input-phys-pe-height")
                            yield Button("Calculate PE", id="btn-phys-pe", variant="primary")

                        yield Label("[bold]Result[/bold]")
                        yield Static(id="lbl-phys-energy-result", classes="result-box")

    @on(Button.Pressed)
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-phys-velocity":
            self.calculate_velocity()
        elif event.button.id == "btn-phys-acceleration":
            self.calculate_acceleration()
        elif event.button.id == "btn-phys-force":
            self.calculate_force()
        elif event.button.id == "btn-phys-ke":
            self.calculate_kinetic_energy()
        elif event.button.id == "btn-phys-pe":
            self.calculate_potential_energy()

    def calculate_velocity(self) -> None:
        dist_str = self.query_one("#input-phys-dist", Input).value
        time_str = self.query_one("#input-phys-time", Input).value
        lbl = self.query_one("#lbl-phys-velocity-result", Static)

        try:
            d = float(dist_str)
            t = float(time_str)
            result = self.manager.calculate_velocity(d, t)
            if "Error" in result:
                lbl.update(f"[red]{result}[/red]")
            else:
                lbl.update(f"[green]{result}[/green]")
        except ValueError:
            lbl.update("[red]Error: Invalid numeric input.[/red]")

    def calculate_acceleration(self) -> None:
        vi_str = self.query_one("#input-phys-vi", Input).value
        vf_str = self.query_one("#input-phys-vf", Input).value
        time_str = self.query_one("#input-phys-acc-time", Input).value
        lbl = self.query_one("#lbl-phys-acceleration-result", Static)

        try:
            vi = float(vi_str)
            vf = float(vf_str)
            t = float(time_str)
            result = self.manager.calculate_acceleration(vi, vf, t)
            if "Error" in result:
                lbl.update(f"[red]{result}[/red]")
            else:
                lbl.update(f"[green]{result}[/green]")
        except ValueError:
            lbl.update("[red]Error: Invalid numeric input.[/red]")

    def calculate_force(self) -> None:
        m_str = self.query_one("#input-phys-mass", Input).value
        a_str = self.query_one("#input-phys-acc", Input).value
        lbl = self.query_one("#lbl-phys-force-result", Static)

        try:
            m = float(m_str)
            a = float(a_str)
            result = self.manager.calculate_force(m, a)
            if "Error" in result:
                lbl.update(f"[red]{result}[/red]")
            else:
                lbl.update(f"[green]{result}[/green]")
        except ValueError:
            lbl.update("[red]Error: Invalid numeric input.[/red]")

    def calculate_kinetic_energy(self) -> None:
        m_str = self.query_one("#input-phys-ke-mass", Input).value
        v_str = self.query_one("#input-phys-ke-vel", Input).value
        lbl = self.query_one("#lbl-phys-energy-result", Static)

        try:
            m = float(m_str)
            v = float(v_str)
            result = self.manager.calculate_kinetic_energy(m, v)
            if "Error" in result:
                lbl.update(f"[red]{result}[/red]")
            else:
                lbl.update(f"[green]{result}[/green]")
        except ValueError:
            lbl.update("[red]Error: Invalid numeric input.[/red]")

    def calculate_potential_energy(self) -> None:
        m_str = self.query_one("#input-phys-pe-mass", Input).value
        h_str = self.query_one("#input-phys-pe-height", Input).value
        lbl = self.query_one("#lbl-phys-energy-result", Static)

        try:
            m = float(m_str)
            h = float(h_str)
            result = self.manager.calculate_potential_energy(m, h)
            if "Error" in result:
                lbl.update(f"[red]{result}[/red]")
            else:
                lbl.update(f"[green]{result}[/green]")
        except ValueError:
            lbl.update("[red]Error: Invalid numeric input.[/red]")
