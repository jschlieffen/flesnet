#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 17 17:00:30 2026

@author: jschlieffen
"""


import queue
from threading import Thread
import time
import os
import traceback

class communicator(Thread):
    def __init__(self,channel,node):
        super().__init__(daemon=True)
        self.channel = channel
        self.node = node
        
    def write_response(self, msg):
        with open(f"tmp/communication/{self.node}.txt", "w") as f:
            f.write(f"{self.node}: {msg}")
            f.flush()
            os.fsync(f.fileno())
    
    def run(self):
        self.write_response('test improv.')
        while True:
            time.sleep(0.1)
            try:
                with open('tmp/communication/central_manager.txt', "r") as f:
                    msg = f.read().strip()
                    #ode, action = line.split(": ")
                    f.close()
            except FileNotFoundError:
                msg = ""
            prev_action = ""
            
            if f"{self.node}" in msg:
                
                node,process, action = msg.split(": ")
                if action == prev_action: 
                    continue
                if action == "kill":
                    if not self.give_command('kill',process):
                        break
                    prev_action = action
                elif action == "revieve":
                    if not self.give_command('revieve',process):
                        break
                    prev_action = action
                elif action == "stop":
                    self.write_response('done stop')
                    self.give_command('stop',process)
                    prev_action = action
                    break
                    
    def give_command(self,action,process):
        self.channel.send_to_parent(f"{process}: {action}")
        msg = self.channel.recv_from_parent()
        match msg:
                case "succeed":
                    self.write_response(f"done {action}")
                    return True
    
                case "shutdown":
                    self.write_response(f'failed {action}')
                    return False
