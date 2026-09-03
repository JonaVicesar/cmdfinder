"""
Screen for final confirmation 
"""
from textual.screen import Screen
from textual.containers import Vertical, Horizontal
from textual.widgets import Header, Footer, Button, Static
from textual.binding import Binding
class ConfirmScreen(Screen):
    BINDINGS = [
        Binding("escape", "close", "Close"),
        Binding("enter", "close", "Close"),
    ]

    def __init__(self, program, key):   
        super().__init__()
        self.program = program
        self.key = key

    def compose(self):
        yield Header(show_clock=False)
        yield Vertical(
            Static(
                f"\n\u2713 Saved: [b]{self.key}[/b] in [b]{self.program}[/b]\n\n"
                f"Try with: cf {self.program} {self.key.replace('-', ' ')}\n",
                classes="confirmation",
            ),
            Horizontal(
                Button("Add another", id="btn_another"),
                Button("Exit", variant="success", id="btn_exit"),
            ),
            classes="form-container",
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_exit":
            self.app.exit()
        else:
            self.app.pop_screen()
            self.app.pop_screen()

    def action_close(self) -> None:
        self.app.exit()


class AskScreen(Screen):
    """
    Yes/No confirmation before syncing programs from the catalog.
    Push it with a callback it dismisses with True (update) or False (cancel)
    """
    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def __init__(self, title, detail="", yes_label="Yes"):
        super().__init__()
        self.title = title
        self.detail = detail
        self.yes_label = yes_label

    def compose(self):
        yield Header(show_clock=False)
        yield Vertical(
            Static(
                f"\n{self.title}\n"
                + (f"{self.detail}\n" if self.detail else ""),
                classes="subtitle",
            ),
            Horizontal(
                Button(self.yes_label, variant="success", id="btn_yes"),
                Button("Cancel", variant="error", id="btn_no"),
            ),
            classes="form-container",
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "btn_yes")

    def action_cancel(self) -> None:
        self.dismiss(False)
