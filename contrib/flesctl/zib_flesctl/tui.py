from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Button


class MyApp(App):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("My Python program")
        yield Button("Start")
        yield Button("Quit")
        yield Footer()


if __name__ == "__main__":
    MyApp().run()
