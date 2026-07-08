"""
Form to load actions and commands
"""
from textual.screen import Screen
from textual.containers import VerticalScroll, Horizontal
from textual.widgets import Header, Footer, Input, TextArea, Button, Label
from textual.binding import Binding

from core import normalize_key
from data_io import save_data


class FormScreen(Screen):
    BINDINGS = [
        Binding("escape", "volver", "Cancelar"),
        Binding("ctrl+s", "guardar", "Guardar"),
    ]

    def __init__(self, data, program):
        super().__init__()
        self.data = data
        self.program = program

    def compose(self):
        yield Header(show_clock=False)
        yield VerticalScroll(
            Label(f"Program: [b]{self.program}[/b]", classes="subtitle"),
            Label("Action name (ex. 'remove branch'):"),
            Input(placeholder="remove branch", id="input_action"),
            Label("Alias separated by a coma (optional):"),
            Input(placeholder="borrar rama, delete branch", id="input_aliases"),
            Label("Description:"),
            Input(placeholder="what does this action", id="input_description"),
            Label("Comands (one for line):"),
            TextArea(id="textarea_comands"),
            Horizontal(
                Button("Save (Ctrl+S)", variant="success", id="btn_save"),
                Button("Cancel (Esc)", variant="error", id="btn_cancel"),
            ),
            classes="form-container",
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_cancel":
            self.action_back()
        else:
            self.action_save()

    def action_back(self) -> None:
        self.app.pop_screen()

    def action_save(self) -> None:
        from tui.screens.confirm import ConfirmScreen

        action_name = self.query_one("#input_action", Input).value.strip()
        if not action_name:
            self.app.bell()
            return
        key = normalize_key(action_name)

        aliases_raw = self.query_one("#input_aliases", Input).value.strip()
        aliases_new = [a.strip() for a in aliases_raw.split(",") if a.strip()]

        description = self.query_one("#input_description", Input).value.strip()

        comands_raw = self.query_one("#textarea_comands", TextArea).text
        comands_new = [l.strip() for l in comands_raw.splitlines() if l.strip()]

        if not comands_new:
            self.app.bell()
            return

        actions = self.data[self.program].setdefault("actions", {})
        exist = actions.get(key, {"aliases": [], "description": "", "comands": []})

        actions[key] = {
            "aliases": list(dict.fromkeys(exist.get("aliases", []) + aliases_new)),
            "description": description or exist.get("description", ""),
            "comands": list(dict.fromkeys(exist.get("comands", []) + comands_new)),
        }

        save_data(self.data)
        self.app.push_screen(ConfirmScreen(self.program, key))
