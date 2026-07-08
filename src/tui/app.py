"""
Main app, just the CSS Styles and run, all the logic of the screens still lives in 
tui/screens/
"""
from textual.app import App

from data_io import load_data
from src.tui.screens.select_program import SelectProgramsScreen

class CmdFinderAddApp(App):
    CSS = """
    .subtitle {
        padding: 1 2;
        color: $text-muted;
    }
    .form-container {
        padding: 1 2;
        height: auto;
    }
    .confirmation {
        padding: 2;
        color: $success;
    }
    Input {
        margin-bottom: 1;
    }
    TextArea {
        height: 8;
        margin-bottom: 1;
    }
    ListView {
        height: auto;
        max-height: 20;
    }
    Button {
        margin-right: 1;
    }
    """

    TITLE = "cmdfinder \u2014 add comand"

    def on_mount(self) -> None:
        data = load_data()
        self.push_screen(SelectProgramsScreen(data))


def run_tui():
    CmdFinderAddApp().run()

if __name__ == "__main__":
    run_tui()
