"""
Screen that shows all actions for a selected program.
Click an action to edit it, or '+ Add action' to create a new one.
"""
from textual.screen import Screen
from textual.widgets import Header, Footer, ListView, ListItem, Label, Button, Static
from textual.binding import Binding
from textual.containers import Vertical

from cmdfinder.core import normalize_key

class ProgramActionsScreen(Screen):
    BINDINGS = [Binding("escape", "back", "Back")]

    ACTION_PREFIX = "action_"
    ADD_ACTION_ID = "__add_action__"

    def __init__(self, data, program):
        super().__init__()
        self.data = data
        self.program = program

    def compose(self):
        actions = self.data.get(self.program, {}).get("actions", {})
        desc = self.data.get(self.program, {}).get("program_description", "")

        yield Header(show_clock=False)
        yield Vertical(
            Static(
                f"  [b]{self.program}[/b]" + (f"  —  {desc}" if desc else ""),
                classes="subtitle",
            ),
            ListView(id="actions_list"),
            Button("+ Add action", id="btn_add", variant="success"),
            id="actions_container",
        )
        yield Footer()

    async def on_mount(self) -> None:
        await self._render_actions()

    async def _render_actions(self) -> None:
        lst = self.query_one("#actions_list", ListView)
        await lst.clear()

        actions = self.data.get(self.program, {}).get("actions", {})
        for key in sorted(actions.keys()):
            info = actions[key]
            description = info.get("description", "")
            n_aliases = len(info.get("aliases", []))
            n_commands = len(info.get("commands", []))

            text = f"{key}"
            if description:
                text += f"  —  {description}"
            text += f"\n  {n_aliases} aliases · {n_commands} commands"

            lst.append(ListItem(Label(text), id=f"{self.ACTION_PREFIX}{key}"))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        item_id = event.item.id

        if item_id == self.ADD_ACTION_ID:
            self._open_form(action_key=None)
            return

        if item_id and item_id.startswith(self.ACTION_PREFIX):
            action_key = item_id.removeprefix(self.ACTION_PREFIX)
            self._open_form(action_key=action_key)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_add":
            self._open_form(action_key=None)

    def _open_form(self, action_key=None):
        from cmdfinder.tui.screens.form import FormScreen
        self.app.push_screen(FormScreen(self.data, self.program, action_key=action_key))

    def action_back(self) -> None:
        self.app.pop_screen()