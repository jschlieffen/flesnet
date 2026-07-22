#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 17 17:30:28 2026

@author: jschlieffen
"""

from queue import Queue

class Channel:
    def __init__(self):
        self.parent_to_child = Queue()
        self.child_to_parent = Queue()


    # Parent API
    def send_to_child(self, msg):
        self.parent_to_child.put(msg)

    def recv_from_child(self):
        return self.child_to_parent.get()

    # Worker API
    def recv_from_parent(self):
        return self.parent_to_child.get()

    def send_to_parent(self, msg):
        self.child_to_parent.put(msg)