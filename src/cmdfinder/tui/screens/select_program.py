"""
Choose a local program, install one from the remote catalog
or create a new one. The input search filters both sources at once
"""
from textual import work
from textual.screen import Screen
from textual.widgets import Header, Footer, ListView, ListItem, Label, Static, Input
from textual.binding import Binding

from cmdfinder.core import score_text
from cmdfinder.remote_catalog import get_index, install_program, CatalogError

NEW_PROGRAM_ID = "__new__"
CATALOG_PREFIX = "catalog_"
LOCAL_PREFIX = "prog_"
MINIMUN = 30 # minimun score required

def _matches(query, text):
    if not query.strip():
        return True
    return score_text(query, text) >= MINIMUN
class SelectProgramsScreen(Screen):
    BINDINGS = [Binding("escape", "exit", "Exit")]

    def __init__(self, data):
        super().__init__()
        self.data = data
        self.remote_index = {}

    def compose(self):
        yield Header(show_clock=False)
        yield Static(
            "  Pick a program, install from catalog, or create a new one.",
            classes="subtitle",
        )
        yield Input(placeholder="Search (local or catalog)...", id="search_input")
        yield ListView(id="programs_list")
        yield Static("", id="catalog_status", classes="subtitle")
        yield Footer()

    async def on_mount(self) -> None:
        await self._render_list("")
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
        await self._render_list(self.query_one("#search_input", Input).value)

    def _on_index_failed(self, message: str) -> None:
        self.query_one("#catalog_status", Static).update(
            f"[dim]Catalog unavailable: {message}[/dim]"
        )

    async def on_input_changed(self, event: Input.Changed) -> None:
        await self._render_list(event.value)

    async def _render_list(self, query: str) -> None:
        lst = self.query_one("#programs_list", ListView)
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
            text = f"{name}" + (f"  \u2014  {desc}" if desc else "")
            lst.append(ListItem(Label(text), id=f"{LOCAL_PREFIX}{name}"))

        for name, desc in sorted(self.remote_index.items()):
            if name in self.data:
                continue
            if not _matches(query, name):
                continue
            text = f"\u2b07 {name}  \u2014  {desc}  [catalog]"
            lst.append(ListItem(Label(text), id=f"{CATALOG_PREFIX}{name}"))

        lst.append(ListItem(Label("+ Create new program"), id=NEW_PROGRAM_ID))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        item_id = event.item.id

        if item_id == NEW_PROGRAM_ID:
            from cmdfinder.tui.screens.new_program import NewProgramScreen
            self.app.push_screen(NewProgramScreen(self.data))
            return

        if item_id == None:
            return

        if item_id.startswith(CATALOG_PREFIX):
            name = item_id.removeprefix(CATALOG_PREFIX)
            self._install_from_catalog(name)
            return

        from cmdfinder.tui.screens.form import FormScreen

        program = item_id.removeprefix(LOCAL_PREFIX)
        if program not in self.data:
            desc = (
                "Commands that do not belong to any program in particular"
                if program == "general" else ""
            )
            self.data[program] = {"program_description": desc, "actions": {}}
        self.app.push_screen(FormScreen(self.data, program))

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
        await self._render_list(self.query_one("#search_input", Input).value)

    def _on_install_failed(self, name: str, message: str) -> None:
        self.query_one("#catalog_status", Static).update(
            f"[red]Could not install '{name}': {message}[/red]"
        )

    def action_exit(self) -> None:
        self.app.exit()
