"""
Choose a existent program, 'general' or create a new one
"""
from textual.screen import Screen
from textual.containers import Vertical
from textual.widgets import Header, Footer, ListView, ListItem, Label, Static
from textual.binding import Binding

NEW_PROGRAM_ID = "__new__"


class SelectProgramsScreen(Screen):
    BINDINGS = [Binding("escape", "exit", "Exit")]

    def __init__(self, data):
        super().__init__()
        self.data = data

    def compose(self):
        yield Header(show_clock=False)
        yield Static(
            "  Choose a program (or create a new). 'general' is for "
            "comands that do not belong to any program in particular",
            classes="subtitle",
        )
        items = []
        names = sorted(self.data.keys())
        if "general" not in names:
            names = ["general"] + names
        else:
            names = ["general"] + [n for n in names if n != "general"]

        for name in names:
            desc = self.data.get(name, {}).get("program_description", "")
            text = f"{name}" + (f"  \u2014  {desc}" if desc else "")
            items.append(ListItem(Label(text), id=f"prog_{name}"))

        items.append(ListItem(Label("+ Create new program"), id=NEW_PROGRAM_ID))

        yield ListView(*items, id="programs_list")
        yield Footer()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        from    cmdfinder.tui.screens.new_program import NewProgramScreen
        from    cmdfinder.tui.screens.form import FormScreen

        item_id = event.item.id
        if item_id == NEW_PROGRAM_ID:
            self.app.push_screen(NewProgramScreen(self.data))
      
        else:
            program = item_id.removeprefix("prog_")
            if program not in self.data:
                desc = (
                    "Comands that do not belong to any program in particular"
                    if program == "general" else ""
                )
                self.data[program] = {"program_description": desc, "actions": {}}
            self.app.push_screen(FormScreen(self.data, program))

    def action_exit(self) -> None:
        self.app.exit()
