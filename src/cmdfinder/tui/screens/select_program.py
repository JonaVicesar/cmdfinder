"""
Split screen: left panel = installed programs, right panel = catalog.
Click an installed program to see its actions.
"""
from textual import work
from textual.screen import Screen
from textual.widgets import Header, Footer, ListView, ListItem, Label, Static, Input
from textual.binding import Binding
from textual.containers import Horizontal, Vertical

from cmdfinder.core import score_text
from cmdfinder.remote_catalog import get_index, install_program, CatalogError

NEW_PROGRAM_ID = "__new__"
CATALOG_PREFIX = "catalog_"
LOCAL_PREFIX = "prog_"
FILTER_THRESHOLD = 30 # minimun score required


def _matches(query, text):
    if not query.strip():
        return True
    return score_text(query, text) >= FILTER_THRESHOLD
class SelectProgramsScreen(Screen):
    BINDINGS = [Binding("escape", "exit", "Exit")]

    def __init__(self, data):
        super().__init__()
        self.data = data
        self.remote_index = {}

    def compose(self):
        yield Header(show_clock=False)
        yield Horizontal(
            # here we divided the screen in two sections

            # this new section is for 'work' with our installed programs
            Vertical(
                Static("  Installed", classes="panel-title"),
                Input(placeholder="Search installed...", id="search_installed"),
                ListView(id="installed_list"),
                id="left_panel",
            ),

            # this section is the same, it didn't change
            Vertical(
                Static("  Catalog", classes="panel-title"),
                Input(placeholder="Search catalog...", id="search_catalog"),
                ListView(id="catalog_list"),
                Static("", id="catalog_status", classes="subtitle"),
                id="right_panel",
            ),
            id="split_container",
        )
        yield Footer()

    async def on_mount(self) -> None:
        await self._render_installed("")
        await self._render_catalog("")
        self._load_remote_index()

    @work(thread=True)
    def _load_remote_index(self) -> None:
        try:
            index = get_index()
        except CatalogError as e:
            self.app.call_from_thread(self._on_index_failed, str(e))
            return
        self.app.call_from_thread(self._on_index_ready, index)

    async def _on_index_ready(self, index: dict) -> None:
        self.remote_index = index
        await self._render_catalog(
            self.query_one("#search_catalog", Input).value
        )

    def _on_index_failed(self, message: str) -> None:
        self.query_one("#catalog_status", Static).update(
            f"[dim]Catalog unavailable: {message}[/dim]"
        )

    async def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "search_installed":
            await self._render_installed(event.value)
        elif event.input.id == "search_catalog":
            await self._render_catalog(event.value)

    async def _render_installed(self, query: str) -> None:
        lst = self.query_one("#installed_list", ListView)
        await lst.clear()

        local_names = sorted(self.data.keys())
        if "general" not in local_names:
            local_names = ["general"] + local_names
        else:
            local_names = ["general"] + [n for n in local_names if n != "general"]

        for name in local_names:
            if not _matches(query, name):
                continue
            desc = self.data.get(name, {}).get("program_description", "")
            n_actions = len(self.data.get(name, {}).get("actions", {}))
            text = f"{name}"
            if desc:
                text += f"  —  {desc}"
            text += f"\n  {n_actions} actions"
            lst.append(ListItem(Label(text), id=f"{LOCAL_PREFIX}{name}"))

        lst.append(ListItem(Label("+ Create new program"), id=NEW_PROGRAM_ID))

    async def _render_catalog(self, query: str) -> None:
        lst = self.query_one("#catalog_list", ListView)
        await lst.clear()

        for name, desc in sorted(self.remote_index.items()):
            if name in self.data:
                continue
            if not _matches(query, name):
                continue
            text = f"{name}"
            if desc:
                text += f"  —  {desc}"
            text += "\n  [catalog]"
            lst.append(ListItem(Label(text), id=f"{CATALOG_PREFIX}{name}"))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        item_id = event.item.id

        if item_id is None:
            return

        if item_id == NEW_PROGRAM_ID:
            from cmdfinder.tui.screens.new_program import NewProgramScreen
            self.app.push_screen(NewProgramScreen(self.data))
            return

        if item_id.startswith(CATALOG_PREFIX):
            name = item_id.removeprefix(CATALOG_PREFIX)
            self._install_from_catalog(name)
            return

        if item_id.startswith(LOCAL_PREFIX):
            program = item_id.removeprefix(LOCAL_PREFIX)
            if program not in self.data:
                desc = (
                    "Commands that do not belong to any program in particular"
                    if program == "general" else ""
                )
                self.data[program] = {"program_description": desc, "actions": {}}
            from cmdfinder.tui.screens.program_actions import ProgramActionsScreen
            #self.app.push_screen(ProgramActionsScreen(self.data, program))

    @work(thread=True)
    def _install_from_catalog(self, name: str) -> None:
        status = self.query_one("#catalog_status", Static)
        self.app.call_from_thread(status.update, f"[dim]Installing '{name}'...[/dim]")
        try:
            program_data = install_program(name)
        except CatalogError as e:
            self.app.call_from_thread(self._on_install_failed, name, str(e))
            return
        self.app.call_from_thread(self._on_install_ok, name, program_data)

    async def _on_install_ok(self, name: str, program_data: dict) -> None:
        self.data[name] = program_data
        n_actions = len(program_data.get("actions", {}))
        self.query_one("#catalog_status", Static).update(
            f"[green]\u2713 '{name}' installed ({n_actions} actions). "
            f"Now available with 'cf {name} ...'[/green]"
        )
        await self._render_installed(
            self.query_one("#search_installed", Input).value
        )
        await self._render_catalog(
            self.query_one("#search_catalog", Input).value
        )

    def _on_install_failed(self, name: str, message: str) -> None:
        self.query_one("#catalog_status", Static).update(
            f"[red]Could not install '{name}': {message}[/red]"
        )

    def action_exit(self) -> None:
        self.app.exit()
