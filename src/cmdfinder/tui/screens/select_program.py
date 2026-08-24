"""
Split screen: left panel = installed programs, right panel = catalog.
Click an installed program to see its actions.
"""
import asyncio

from textual import work
from textual.screen import Screen
from textual.widgets import Header, Footer, ListView, ListItem, Label, Static, Input, Button
from textual.binding import Binding
from textual.containers import Horizontal, Vertical

from cmdfinder.core import score_text
from cmdfinder.remote_catalog import get_index, install_program, check_updates, CatalogError

FILTER_THRESHOLD = 30 # minimun score required


def _matches(query, text):
    if not query.strip():
        return True
    return score_text(query, text) >= FILTER_THRESHOLD

def _index_description(info):
    if isinstance(info, dict):
        return info.get("description", "")
    return str(info)

def _list_item(text, kind, name=None):
    """
    ListItem carrying its payload as plain attributes instead of an id.

    Dynamic ListItems with ids collide (DuplicateIds) whenever a new render
    appends before the previous clear() finished removing the old widgets,
    so we don't use ids here at all.
    """
    item = ListItem(Label(text))
    item.item_kind = kind
    item.item_name = name
    return item

class SelectProgramsScreen(Screen):
    BINDINGS = [Binding("escape", "exit", "Exit")]

    def __init__(self, data):
        super().__init__()
        self.data = data
        self.remote_index = {}
        self.updatable = set()
        self._busy = False
        self._render_lock = asyncio.Lock()

    def compose(self):
        yield Header(show_clock=False)
        yield Horizontal(
            # here we divided the screen in two sections

            # this new section is for 'work' with our installed programs
            Vertical(
                Static("  Installed", classes="panel-title"),
                Input(placeholder="Search installed...", id="search_installed"),
                Button("Update all", id="btn_update_all", variant="warning"),
                ListView(id="installed_list"),
                id="left_panel",
            ),

            # visual separator between the two panels
            Vertical(classes="panel-separator"),

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
        self._refresh_updatable()
        await self._refresh_panels()
        self._load_remote_index()

    async def _refresh_panels(self) -> None:
        """
        Re-render both lists with the current search queries.

        A lock serializes renders: on_mount and on_screen_resume can fire
        back to back, and two interleaved renders would append ListItems
        with duplicated IDs before the previous clear() finishes.
        """
        async with self._render_lock:
            await self._render_installed(
                self.query_one("#search_installed", Input).value
            )
            await self._render_catalog(
                self.query_one("#search_catalog", Input).value
            )

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
        self._refresh_updatable()
        await self._refresh_panels()

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
            if name in self.updatable:
                text += "\n  [yellow]\u2191 update available[/yellow]"
            lst.append(_list_item(text, "local", name))

        lst.append(_list_item("+ Create new program", "new"))

    async def _render_catalog(self, query: str) -> None:
        lst = self.query_one("#catalog_list", ListView)
        await lst.clear()

        for name, info in sorted(self.remote_index.items()):
            if name in self.data:
                continue
            if not _matches(query, name):
                continue
            desc = _index_description(info)
            text = f"{name}"
            if desc:
                text += f"  —  {desc}"
            text += "\n  [catalog]"
            lst.append(_list_item(text, "catalog", name))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        kind = getattr(event.item, "item_kind", None)

        if kind is None:
            return

        if kind == "new":
            from cmdfinder.tui.screens.new_program import NewProgramScreen
            self.app.push_screen(NewProgramScreen(self.data))
            return

        if kind == "catalog":
            if self._busy:
                return
            self._install_from_catalog(event.item.item_name)
            return

        if kind == "local":
            program = event.item.item_name
            if program in self.updatable and not self._busy:
                self._ask_update([program])
                return
            if program not in self.data:
                desc = (
                    "Commands that do not belong to any program in particular"
                    if program == "general" else ""
                )
                self.data[program] = {"program_description": desc, "actions": {}}
            from cmdfinder.tui.screens.program_actions import ProgramActionsScreen
            self.app.push_screen(ProgramActionsScreen(self.data, program))

    async def on_screen_resume(self) -> None:
        await self._refresh_panels()

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
        await self._refresh_panels()

    def _on_install_failed(self, name: str, message: str) -> None:
        self.query_one("#catalog_status", Static).update(
            f"[red]Could not install '{name}': {message}[/red]"
        )

    def _refresh_updatable(self) -> None:
        self.updatable = set(check_updates())
        self.query_one("#btn_update_all", Button).display = bool(self.updatable)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_update_all" and not self._busy:
            self._ask_update(sorted(self.updatable))

    def _ask_update(self, names: list) -> None:
        if not names:
            return
        from cmdfinder.tui.screens.confirm import UpdateConfirmScreen
        self._pending_names = list(names)
        self.app.push_screen(UpdateConfirmScreen(self._pending_names), self._begin_update)

    def _begin_update(self, proceed: bool) -> None:
        if not proceed or self._busy:
            return
        self._busy = True
        self.query_one("#btn_update_all", Button).disabled = True
        self._update_programs(self._pending_names)

    @work(thread=True)
    def _update_programs(self, names: list) -> None:
        status = self.query_one("#catalog_status", Static)
        updated, failed = [], []

        for i, name in enumerate(names, 1):
            self.app.call_from_thread(
                status.update, f"[dim]Updating {i}/{len(names)}: {name}...[/dim]"
            )
            try:
                program_data = install_program(name)
                updated.append((name, program_data))
            except CatalogError as e:
                failed.append((name, str(e)))

        self.app.call_from_thread(self._on_updates_done, updated, failed)

    async def _on_updates_done(self, updated: list, failed: list) -> None:
        for name, program_data in updated:
            self.data[name] = program_data

        self._busy = False
        btn = self.query_one("#btn_update_all", Button)
        btn.disabled = False
        self._refresh_updatable()

        await self._refresh_panels()

        status = self.query_one("#catalog_status", Static)
        parts = []
        if updated:
            parts.append(f"[green]\u2713 Updated: {', '.join(name for name, _ in updated)}[/green]")
        for name, message in failed:
            parts.append(f"[red]Could not update '{name}': {message}[/red]")
        if not parts:
            status.update("[yellow]Nothing was updated[/yellow]")
        else:
            status.update("\n".join(parts))

    def action_exit(self) -> None:
        self.app.exit()
