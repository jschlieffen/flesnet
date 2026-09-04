#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Aug 27 20:12:26 2026

@author: jschlieffen
"""

from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import Button, Static

import re

from interface.node_info import NodeInfoScreen


def get_params():
    file_names = []

    num_receivers = 0
    num_inputnodes = 0
    num_outputnodes = 0
    num_cm = 0

    enable_graph = False
    enable_progess_bar = False
    use_GSI_TS_forwarding = False
    use_ZIB_TS_forwarding = False

    with open(
        "tmp/interface/interface_params.txt",
        "r",
    ) as f:

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

                file_names.append(logfile)

            elif line.startswith("num_receivers: "):

                num_receivers = int(
                    line.split(": ", 1)[1]
                )

            elif line.startswith("num_inputnodes: "):

                num_inputnodes = int(
                    line.split(": ", 1)[1]
                )

            elif line.startswith("num_outputnodes: "):

                num_outputnodes = int(
                    line.split(": ", 1)[1]
                )

            elif line.startswith("num_cm: "):

                num_cm = int(
                    line.split(": ", 1)[1]
                )

            elif line.startswith("enable_graph:"):

                enable_graph = (
                    line.split(": ", 1)[1] == "1"
                )

            elif line.startswith("enable_progess_bar:"):

                enable_progess_bar = (
                    line.split(": ", 1)[1] == "1"
                )

            elif line.startswith(
                "use_GSI_TS_forwarding: "
            ):

                use_GSI_TS_forwarding = (
                    line.split(": ", 1)[1] == "1"
                )

            elif line.startswith(
                "use_ZIB_TS_forwarding: "
            ):

                use_ZIB_TS_forwarding = (
                    line.split(": ", 1)[1] == "1"
                )

    parameters = {
        "num_receiver_nodes": num_receivers,
        "num_input_nodes": num_inputnodes,
        "num_output_nodes": num_outputnodes,
        "num_cm": num_cm,
        "use_GSI_TS_forwarding": use_GSI_TS_forwarding,
        "use_ZIB_TS_forwarding": use_ZIB_TS_forwarding,
    }

    return file_names, parameters


def calc_output_str(input_string):
    """
    Convert a logfile path into a human-readable node name.
    """

    patterns = [
        (
            r"logs/collectl/(build|entry)_nodes/(build|entry)_node_(.+?)\.csv",
            lambda m: f"{m.group(1)} node: {m.group(3)}"
        ),
        (
            r"logs/collectl/tsclient/sender_node_(.+?)\.csv",
            lambda m: f"sender node: {m.group(1)}"
        ),
        (
            r"logs/collectl/tsclient/receiving_node_(.+?)\.csv",
            lambda m: f"receiving node: {m.group(1)}"
        ),
        (
            r"logs/collectl/timeslice_forwarding/input_nodes/input_node_(.+?)\.csv",
            lambda m: f"input node: {m.group(1)}"
        ),
        (
            r"logs/collectl/timeslice_forwarding/output_nodes/output_node_(.+?)\.csv",
            lambda m: f"output node: {m.group(1)}"
        ),
        (
            r"logs/collectl/timeslice_forwarding/central_manager/central_manager_(.+?)\.csv",
            lambda m: f"Central manager: {m.group(1)}"
        ),
    ]

    for pattern, formatter in patterns:

        match = re.search(
            pattern,
            input_string,
        )

        if match:
            return formatter(match)

    return input_string


def create_node_list(
    filenames,
    parameters,
):
    """
    Create a simple list of nodes from the filenames.

    Returns:

        [
            ("Sender node", "node001"),
            ("Receiver node", "node002"),
            ...
        ]
    """

    nodes = []

    for filename in filenames:

        output = calc_output_str(filename)

        if ": " not in output:
            continue

        node_type, node = output.split(
            ": ",
            1,
        )

        nodes.append(
            (
                node_type,
                node,
            )
        )

    return nodes


class NodeViewer(VerticalScroll):
    """
    Displays the available nodes.

    Each node has a 'Show info' button.
    """

    def __init__(
        self,
        filenames,
        parameters,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self.filenames = filenames
        self.parameters = parameters

    def compose(self) -> ComposeResult:

        nodes = create_node_list(
            self.filenames,
            self.parameters,
        )

        if not nodes:

            yield Static(
                "No nodes available.",
                classes="no-nodes",
            )

            return

        for index, (node_type, node) in enumerate(nodes):

            yield Horizontal(
                Static(
                    f"{node_type}: {node}",
                    classes="node-label",
                ),

                Button(
                    "Show info",
                    id=f"node-{index}",
                ),

                classes="node-row",
            )

    def on_button_pressed(
        self,
        event: Button.Pressed,
    ):

        button_id = event.button.id

        if not button_id:
            return

        if not button_id.startswith("node-"):
            return

        try:
            index = int(
                button_id.removeprefix("node-")
            )
        except ValueError:
            return

        nodes = create_node_list(
            self.filenames,
            self.parameters,
        )

        if index < 0 or index >= len(nodes):
            return

        node_type, node = nodes[index]

        self.app.push_screen(
            NodeInfoScreen(
                node_type,
                node,
            )
        )
