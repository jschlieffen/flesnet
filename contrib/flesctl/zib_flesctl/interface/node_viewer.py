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



def calc_output_str(input_string):
    patterns = [
        (r"logs/collectl/(build|entry)_nodes/(build|entry)_node_(.+?)\.csv",lambda m: f"{m.group(1)} node: {m.group(3)}"),
        (r"logs/collectl/tsclient/sender_node_(.+?)\.csv", lambda m: f"sender node: {m.group(1)}"),
        (r"logs/collectl/tsclient/receiving_node_(.+?)\.csv", lambda m: f"receiving node: {m.group(1)}"),
        (r"logs/collectl/timeslice_forwarding/input_nodes/input_node_(.+?)\.csv", lambda m: f"input node: {m.group(1)}"),
        (r"logs/collectl/timeslice_forwarding/output_nodes/output_node_(.+?)\.csv", lambda m: f"output node: {m.group(1)}"),
        (r"logs/collectl/timeslice_forwarding/central_manager/central_manager_(.+?)\.csv", lambda m: f"Central manager: {m.group(1)}"),
    ]
    for pattern, formatter in patterns:
        match = re.search(pattern,input_string)
        if match:
            return formatter(match)
    return input_string


def create_node_list(filenames,parameters):
    nodes = []

    for filename in filenames:
        output = calc_output_str(filename)
        if ": " not in output:
            continue
        node_type, node = output.split(": ", 1)
        nodes.append((node_type, node))
    return nodes


class NodeViewer(VerticalScroll):

    def __init__(self,filenames,parameters,**kwargs):
        super().__init__(**kwargs)
        self.filenames = filenames
        self.parameters = parameters
        
        
    def compose(self) -> ComposeResult:
        nodes = create_node_list(self.filenames,self.parameters)
        if not nodes:
            yield Static("No nodes available.",classes="no-nodes")
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
            
            
    def on_button_pressed(self,event: Button.Pressed):
        button_id = event.button.id
        if not button_id:
            return
        if not button_id.startswith("node-"):
            return
        try:
            index = int(button_id.removeprefix("node-"))
        except ValueError:
            return
        nodes = create_node_list(self.filenames,self.parameters)
        if index < 0 or index >= len(nodes):
            return
        node_type, node = nodes[index]
        self.app.push_screen(NodeInfoScreen(node_type,node))
