#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Aug 27 20:09:34 2026

@author: jschlieffen
"""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Static

import interface.interface_communicator as comm

from interface.rate_screen import RateScreen

class NodeInfoScreen(Screen):

    def __init__(self, node_type, node,filename):
        super().__init__()

        self.node_type = node_type
        self.node = node
        self.filename = filename
            
    def compose(self) -> ComposeResult:
        with Horizontal(id="node-info-header"):
            yield Button("<", id="back")
            yield Static(f"{self.node_type} {self.node}", id="node-title")
        with Vertical(id="node-actions"):
            with Horizontal(classes="node-action"):
                yield Static(
                    "node info:",
                    classes="node-action-label",
                )
                yield Button(
                    "OFF",
                    id="node-info",
                )
            with Horizontal(classes="node-action"):
                yield Static(
                    "check active:",
                    classes="node-action-label",
                )
                yield Button(
                    "OFF",
                    id="check-active",
                )
            with Horizontal(classes="node-action"):
                yield Static(
                    "kill:",
                    classes="node-action-label",
                )
                yield Button(
                    "OFF",
                    id="kill",
                )
            with Horizontal(classes="node-action"):
                yield Static(
                    "revive:",
                    classes="node-action-label",
                )
                yield Button(
                    "OFF",
                    id="revive",
                )
            with Horizontal(classes="node-action"):
                yield Static(
                    "remove node:",
                    classes="node-action-label",
                )
                yield Button(
                    "OFF",
                    id="remove-node",
                )

    def on_button_pressed(self, event: Button.Pressed):
        button_id = event.button.id
        if button_id == "back":
            self.app.pop_screen()
            return
        if button_id == 'node-info':
            self.app.push_screen(RateScreen(self.node_type,self.node, self.filename))
            return
        commands = {
            "check-active": "check active",
            "kill": "kill",
            "revive": "revive",
            "remove-node": "remove node",
        }
        if button_id not in commands:
            return
        command = commands[button_id]
        if event.button.label == "OFF":
            event.button.label = "ON"
            event.button.variant = "success"
        else:
            event.button.label = "OFF"
            event.button.variant = "default"
        comm.give_command(self.node_type,self.node, 0, command)
