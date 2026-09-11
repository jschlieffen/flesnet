#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Aug 27 15:58:11 2026

@author: jschlieffen
"""

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Static
from textual import work
from pathlib import Path
import time
import re
import interface.config_parser as cp
import interface.interactive_config_parser as ipc
from logging_lib.log_msg import *
import interface.flesctrl_starter as starter
import interface.node_info as node_info
import interface.node_viewer as node_viewer

class StartFrame(Screen):

    def compose(self) -> ComposeResult:
        with Horizontal(id="top-bar"):
            yield Static("flescontrol")
            yield Button(
                "X",
                id="exit",
                variant="error",
            )
        with Vertical(id="top-area"):
            yield Horizontal(
                Static(
                    "start simulation",
                    classes="action-label",
                ),
                Button(
                    "Start",
                    id="start",
                    variant="success",
                ),
                classes="action-row",
            )
            yield Horizontal(
                Static(
                    "allocate nodes",
                    classes="action-label",
                ),
                Button(
                    "Allocate",
                    id="allocate",
                ),
                classes="action-row",
            )
        yield cp.ParameterEditor(
            self.app.parameters,
            id="parameter-editor",
        )

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "start":
            starter.start_flesctrl()
            self.app.push_screen(
                "intermediate"
            )
            
        elif event.button.id == "allocate":
            starter.allocate_nodes()
            self.app.notify(
                "Allocate nodes"
            )
        elif event.button.id == "exit":

            self.app.exit()
            self.app.result_start = "exit"


class MainFrame(Screen):

    def __init__(self):
        self.nodes_visible = False
        super().__init__()
    def compose(self) -> ComposeResult:
        with Horizontal(id="top-bar"):
            yield Static("Simulation")
            yield Button("X", id="exit", variant="error")
        with Vertical(id="main-controls"):
            yield Horizontal(
                Static(
                    "stop simulation",
                    classes="action-label",
                ),
                Button(
                    "Stop",
                    id="stop",
                    variant="error",
                ),
                classes="action-row",
            )
            yield Horizontal(
                Static(
                    "Show nodes",
                    classes="action-label",
                ),
                Button(
                    "Show nodes",
                    id="show-nodes",
                ),
                classes="action-row",
            )
        yield VerticalScroll( id="node-area")

    def on_button_pressed(self,event: Button.Pressed,):
        button_id = event.button.id
        if button_id == "stop":
            starter.stop_flesctrl()
            self.app.exit()
            return
        if button_id == "exit":
            self.app.result_main = "exit"
            self.app.exit()
            return
        if button_id == "show-nodes":
            self.show_nodes()
            return
        if event.button.has_class("node-button"):
            node_type = event.button.node_type
            node = event.button.node
            filename = event.button.filename
            self.app.push_screen(
                node_info.NodeInfoScreen(
                    node_type,
                    node,
                    filename
                )
            )
            return

            
    def show_nodes(self):
        node_area = self.query_one("#node-area")

        if self.nodes_visible:
            node_area.display = False
            self.nodes_visible = False
            return
        node_area.display = True
        self.nodes_visible = True
        if len(node_area.children) > 0:
            return
        try:
            file_names, parameters = self.get_params()
        except FileNotFoundError:
            node_area.mount(
                Static(
                    "No running program found.",
                    classes="node-info"
                )
            )
            return
        num_input_nodes = parameters["num_input_nodes"]
        num_output_nodes = parameters["num_output_nodes"]
        num_cm = parameters["num_cm"]
        input_nodes = file_names[:num_input_nodes]
        output_start = num_input_nodes
        output_end = output_start + num_output_nodes
        output_nodes = file_names[output_start:output_end]
        cm_start = output_end
        cm_end = cm_start + num_cm
        central_managers = file_names[cm_start:cm_end]
        groups = [
            ("Input nodes", "Input node", input_nodes),
            ("Output nodes", "Output node", output_nodes),
            ("Central managers", "Central manager", central_managers),
        ]
        for group_name, node_type, filenames in groups:
            if not filenames:
                continue
            node_area.mount(
                Static(
                    group_name,
                    classes="node-group-title"
                )
            )
            for index, filename in enumerate(filenames):
                node = self.get_node_name(filename)
                button_id = (
                    f"node-button-"
                    f"{node_type.lower().replace(' ', '-')}-"
                    f"{index}"
                )
                button = Button(
                    node,
                    id=f"node-button-{index}-{node_type.lower().replace(' ', '-')}",
                    classes="node-button",
                )
                button.node_type = node_type
                button.node = node
                button.filename = filename
                node_area.mount(button)
                
                
    def show_node_info(self, node_type, node, filename):
        self.app.push_screen(
            node_info.NodeInfoScreen(
                node_type=node_type,
                node=node,
                filename=filename,
            )
        )
    # =========================================================
    # READ interface_params.txt
    # =========================================================

    @staticmethod
    def get_params():
        file_names = []
        num_receivers = 0
        num_inputnodes = 0
        num_outputnodes = 0
        num_cm = 0
        use_GSI_TS_forwarding = False
        use_ZIB_TS_forwarding = False
        with open("tmp/interface/interface_params.txt","r",) as f:
            for line in f:
                line = line.strip()
                if line.startswith("file_name:"):
                    _, data = line.split(
                        "file_name: ",
                        1,
                    )
                    logfile, file_data = data.split(
                        ", ",
                        1,
                    )
                    file_names.append(
                        logfile
                    )
                elif line.startswith("num_receivers: "):
                    num_receivers = int(line.split(": ", 1)[1])
                elif line.startswith("num_inputnodes: "):
                    num_inputnodes = int(line.split(": ", 1)[1])
                elif line.startswith("num_outputnodes: "):
                    num_outputnodes = int(line.split(": ", 1)[1])
                elif line.startswith("num_cm: "):
                    num_cm = int(line.split(": ", 1)[1])
                elif line.startswith("use_GSI_TS_forwarding: "):
                    use_GSI_TS_forwarding = (line.split(": ", 1)[1] == "1")
                elif line.startswith("use_ZIB_TS_forwarding: "):
                    use_ZIB_TS_forwarding = (line.split(": ", 1)[1] == "1")

        parameters = {
            "num_receiver_nodes": num_receivers,
            "num_input_nodes": num_inputnodes,
            "num_output_nodes": num_outputnodes,
            "num_cm": num_cm,
            "use_GSI_TS_forwarding": use_GSI_TS_forwarding,
            "use_ZIB_TS_forwarding": use_ZIB_TS_forwarding,
        }
        return file_names, parameters

    # =========================================================
    # NODE NAME
    # =========================================================

    @staticmethod
    def get_node_name(filename):
        patterns = [
            r"sender_node_(.+?)\.log",
            r"receiving_node_(.+?)\.log",
            r"input_node_(.+?)\.log",
            r"output_node_(.+?)\.log",
            r"central_manager_(.+?)\.log",
        ]
        for pattern in patterns:
            match = re.search(pattern, filename,)
            if match:
                return match.group(1)
        return None


class IntermediateFrame(Screen):
    def compose(self):
        with Horizontal(id="top-bar"):
            yield Static("Starting simulation")
            yield Button(
                "X",
                id="exit",
                variant="error",
            )
        yield Static("Starting simulation...", id="starting")
        yield Static(
            "To see the current state open a new terminal,\n"
            "connect to cluster and enter:\n"
            "tmux attach-session",
            id="instructions",
        )

    def on_mount(self):
        self.monitor_startup()

    @work(thread=True)
    def monitor_startup(self):
        response_file = Path("tmp/interface/interface_response.txt")
        while True:
            try:
                msg = response_file.read_text().strip()
            except FileNotFoundError:
                msg = ""
            if msg == "0: done starting":
                self.app.call_from_thread(self.startup_finished)
                return
            time.sleep(0.1)

    def startup_finished(self):
        self.app.pop_screen()
        self.app.push_screen("main")

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "exit":
            self.app.result_start = "exit"
            self.app.exit()


class flesApp(App):
    CSS_PATH = "css_files/flesapp.tcss"
    SCREENS = {
        "start": StartFrame,
        "main": MainFrame,
        "intermediate": IntermediateFrame,
    }
    
    def __init__(self,attach_session):
        super().__init__()
        self.result_start = None
        self.attach_session = attach_session

    def on_mount(self):
        self.parameters = (ipc.params_interactive())
        if self.attach_session:
            self.push_screen("intermediate")
        else:
            self.push_screen("start")

