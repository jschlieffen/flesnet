#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 19 17:32:03 2026

@author: jschlieffen
"""

import os
import time


def give_command(node_type,node,process,action):
    with open('tmp/interface/interface_commands.txt','w') as f:
        f.write(f'{node_type}: {node}: {process}: {action}')
        f.flush()
        f.close
    check_response(node,action)
    
def check_response(node,action):
    msg = ''
    while msg != f'{node}: done {action}':
        with open('tmp/interface/interface_response.txt','r') as f:
            msg = f.read()
        time.sleep(0.1)
    