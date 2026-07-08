"""
Write name and description of the new program
"""
from textual.screen import Screen
from textual.containers import Vertical, Horizontal
from textual.widgets import Header, Footer, Input, Button, Label
from textual.binding import Binding


class NewProgramScreen(Screen):
    BINDINGS = [Binding("escape", "volver", "Volver")]

    def __init__(self, data):
        super().__init__()
        self.data = data

    def compose(self):
        yield Header(show_clock=False)
        yield Vertical(
            Label("Name of the new program (ej. curl, tmux, vim):"),
            Input(placeholder="program_name", id="input_program_name"),
            Label("Short description:"),
            Input(placeholder="What it is / what it does", id="input_desc_program"),
            Horizontal(
                Button("Continue", variant="success", id="btn_continue"),
                Button("Cancel", variant="error", id="btn_cancel"),
            ),
            classes="form-container",
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        from src.tui.screens.form import FormScreen

        if event.button.id == "btn_cancel":
            self.app.pop_screen()
            return
        name = self.query_one("#input_program_name", Input).value.strip().lower()
        desc = self.query_one("#input_desc_program", Input).value.strip()
        if not name:
            self.app.bell()
            return
        if name not in self.data:
            self.data[name] = {"program_description": desc, "actions": {}}
        self.app.pop_screen()
        self.app.push_screen(FormScreen(self.data, name))

    def action_back(self) -> None:
        self.app.pop_screen()


