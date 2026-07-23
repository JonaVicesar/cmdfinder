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