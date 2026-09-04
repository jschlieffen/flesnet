from pathlib import Path
from threading import Event
import time

from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import Button, Footer, Header, RichLog


class LogTailApp(App):
    CSS = """
    #buttons {
        height: 3;
        padding: 0 1;
    }

    #buttons Button {
        margin-right: 1;
    }

    #log {
        height: 1fr;
        border: solid green;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()

        with Horizontal(id="buttons"):
            yield Button("Clear", id="clear")
            yield Button("Pause", id="pause")
            yield Button("Bottom", id="bottom")

        yield RichLog(id="log", wrap=False)

        yield Footer()

    def on_mount(self) -> None:
        self.log_widget = self.query_one("#log", RichLog)

        self.paused = False
        self.stop_event = Event()

        self.run_worker(
            self.tail_log,
            thread=True,
        )

    def tail_log(self) -> None:
        path = Path("app.log")

        with path.open("r", encoding="utf-8") as f:
            # Start from the beginning:
            # tail -n +1 -f app.log
            while not self.stop_event.is_set():

                if self.paused:
                    # Event.wait() can be interrupted when shutting down.
                    self.stop_event.wait(0.1)
                    continue

                line = f.readline()

                if line:
                    self.call_from_thread(
                        self.log_widget.write,
                        line.rstrip("\n"),
                    )
                else:
                    # Don't busy-loop while waiting for new log entries.
                    self.stop_event.wait(0.1)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id

        if button_id == "clear":
            self.log_widget.clear()

        elif button_id == "pause":
            self.paused = not self.paused

            event.button.label = (
                "Resume" if self.paused else "Pause"
            )

        elif button_id == "bottom":
            self.log_widget.scroll_end(animate=False)

    def on_unmount(self) -> None:
        self.stop_event.set()


if __name__ == "__main__":
    LogTailApp().run()
