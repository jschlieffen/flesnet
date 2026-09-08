from __future__ import annotations

import math
from collections import deque
from pathlib import Path
from threading import Event

from rich.text import Text

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, RichLog, Static
import re

LOGFILE = Path("data.log")
MAX_POINTS = 60



def extract_rate(log_line):
    match = re.search(r'GB/s:\s*(\d+(?:\.\d+)?)', log_line)
    if match:
        return float(match.group(1))

    match = re.search(r'MB/s:\s*(\d+(?:\.\d+)?)', log_line)
    if match:
        return float(match.group(1)) / 1000

    return None
        
class RateChart(Static):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.values: deque[float] = deque(maxlen=MAX_POINTS)

    def add_value(self,value: float) -> None:
        self.values.append(value)
        self.refresh()

    def clear(self) -> None:
        self.values.clear()
        self.refresh()

    def render(self) -> Text:
        width = self.size.width
        height = self.size.height
        if width < 30 or height < 10:
            return Text("Terminal too small")
        if not self.values:
            return Text("Waiting for data...")
        values = list(self.values)
        y_label_width = 9
        left = y_label_width
        right = 2
        top = 2
        bottom = 2
        plot_width = ( width - left - right )
        plot_height = (height - top - bottom)
        if (plot_width < 5 or plot_height < 5):
            return Text("Terminal too small")

        ymin = min(values)
        ymax = max(values)
        if math.isclose(ymin, ymax):
            ymin -= 1
            ymax += 1
        padding = (ymax - ymin) * 0.05
        ymin -= padding
        ymax += padding
        grid = [[" " for _ in range(plot_width)]for _ in range(plot_height)]
        for i in range(6):
            ratio = i / 5
            y = round((1 - ratio)* (plot_height - 1))
            for x in range(plot_width):
                grid[y][x] = "·"
        points = []
        for i, value in enumerate(values):
            if len(values) == 1:
                x = plot_width // 2
            else:
                x = round(i * (plot_width - 1) / (len(values) - 1))
            ratio = ((value - ymin) / (ymax - ymin))
            y = round((1 - ratio)* (plot_height - 1))
            points.append((x, y))
        for x, y in points:
            if (0 <= y < plot_height and 0 <= x < plot_width):
                grid[y][x] = "●"
        result = Text()
        result.append("Data Rate\n",  style="bold white")
        for row, line in enumerate(grid):
            ratio = 1 - (row / max(plot_height - 1,1))
            value = (ymin + ratio* (ymax - ymin))
            result.append(f"{value:7.1f} │", style="white")
            for char in line:
                if char == "●":
                    result.append(char, style="bold cyan")
                else:
                    result.append(char,style="grey30")
            result.append("\n")
        result.append(" " * y_label_width + "└" + "─" * plot_width + "\n",style="white",)
        result.append(" " * (y_label_width + 1) + "old" + " " * max(0, plot_width - 6,) + "now", style="white")
        return result


class RateScreen(Screen):
    CSS = """
    Screen {
        layout: vertical;
    }

    #toolbar {
        height: 3;
        padding: 0 1;
    }

    #toolbar Button {
        margin-right: 1;
    }

    #main {
        height: 1fr;
    }

    #log {
        width: 1fr;
        height: 1fr;
        border: solid green;
    }

    #chart {
        width: 1fr;
        height: 1fr;
        border: solid cyan;
    }

    #status {
        height: 1;
        padding-left: 1;
    }
    """
    def __init__(self, node_type,node, logfile):
        super().__init__()

        self.node_type = node_type
        self.node = node
        self.logfile = Path(logfile)
        

        self.paused = False
        self.stop_event = Event()

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="node-info-header"):
            yield Button("<", id="back")
            yield Static(f"{self.node_type} {self.node}",id="node-title" )
        with Horizontal(id="toolbar"):
            yield Button(
                "Pause",
                id="pause",
            )
            yield Button(
                "Clear Log",
                id="clear-log",
            )
            yield Button(
                "Clear Plot",
                id="clear-plot",
            )
            yield Button(
                "Bottom",
                id="bottom",
            )
        with Horizontal(id="main"):
            yield RichLog(id="log", wrap=False,markup=False, highlight=False)
            yield RateChart(id="chart")
        yield Static(f"{self.node_type} {self.node} - Starting...", id="status")
        yield Footer()

    def on_mount(self) -> None:
        self.log_widget = self.query_one("#log",RichLog )
        self.chart = self.query_one("#chart",RateChart)
        self.status = self.query_one( "#status", Static)
        self.run_worker(self.tail_file,thread=True)

    def tail_file(self) -> None:
        while not self.logfile.exists():
            if self.stop_event.wait(0.5):
                return
        try:
            with self.logfile.open("r",encoding="utf-8") as file:
                file.seek(0)
                while not self.stop_event.is_set():
                    if self.paused:
                        self.stop_event.wait(0.1)
                        continue
                    line = file.readline()
                    if line:
                        line = line.rstrip("\n")
                        self.app.call_from_thread(self.log_widget.write, line)
                        rate = extract_rate(line)
                        if rate is not None:
                            self.app.call_from_thread(self.chart.add_value,rate)
                            self.app.call_from_thread(self.update_status,rate)
                    else:
                        self.stop_event.wait(0.1)
        except OSError as exc:
            self.app.call_from_thread(self.status.update,f"File error: {exc}")
            
            
    def update_status(self,rate: float) -> None:

        self.status.update(f"{self.node_type} {self.node} Rate: {rate:.2f} MB/s Points: {len(self.chart.values)}")
        
        
        
    def on_button_pressed(self, event: Button.Pressed,) -> None:

        button_id = event.button.id
        if button_id == "back":
            self.app.pop_screen()
            return
        elif button_id == "pause":
            self.paused = not self.paused
            event.button.label = ("Resume" if self.paused else "Pause")
        elif button_id == "clear-log":
            self.log_widget.clear()
        elif button_id == "clear-plot":
            self.chart.clear()
        elif button_id == "bottom":
            self.log_widget.scroll_end(animate=False)

    def on_unmount(self) -> None:
        self.stop_event.set()
