#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 19 15:04:17 2024

@author: jschlieffen
"""

import subprocess

class slurm_commands:
    
    def __init__(self):
        None
        
    def alloc_node(self,node_list):
        return None
    
    def pids(self,Node_ip):
        return None
    
    def kill_process(self,pid):
        return None
    
    def ethernet_ip(self,node_id):
        return None
    
    def infiniband_ip(self,node_id):
        return None
    
    def start_customize_program(self,program_name,node_id):
        return None

class Input_nodes(slurm_commands):
    
    def __init__(self):
        super().__init__()
    
    