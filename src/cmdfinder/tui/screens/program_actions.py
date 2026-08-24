"""
Screen that shows all actions for a selected program.
Click an action to edit it, or '+ Add action' to create a new one.
"""
import asyncio

from textual.screen import Screen
from textual.widgets import Header, Footer, ListView, ListItem, Label, Button, Static
from textual.binding import Binding
from textual.containers import Vertical

from cmdfinder.core import normalize_key

class ProgramActionsScreen(Screen):
    BINDINGS = [Binding("escape", "back", "Back")]

    def __init__(self, data, program):
        super().__init__()
        self.data = data
        self.program = program
        self._render_lock = asyncio.Lock()

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

    async def on_screen_resume(self) -> None:
        await self._render_actions()

    async def _render_actions(self) -> None:
        # same lock as SelectProgramsScreen: mount and resume can interleave
        async with self._render_lock:
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

                item = ListItem(Label(text))
                item.action_key = key
                lst.append(item)

            add_item = ListItem(Label("+ Add action"))
            add_item.action_key = None
            lst.append(add_item)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if not hasattr(event.item, "action_key"):
            return
        self._open_form(action_key=event.item.action_key)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_add":
            self._open_form(action_key=None)

    def _open_form(self, action_key=None):
        from cmdfinder.tui.screens.form import FormScreen
        self.app.push_screen(FormScreen(self.data, self.program, action_key=action_key))

    def action_back(self) -> None:
        self.app.pop_screen()