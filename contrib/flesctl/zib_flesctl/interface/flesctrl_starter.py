#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 30 20:12:50 2026

@author: jschlieffen
"""

import subprocess


#TODO: use boilerplate-code for tmux send-keys
def allocate_nodes():
    session_name = 'flesctrl'
    session_exists = subprocess.run(
        ['tmux', 'has-session', '-t', session_name],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    if session_exists.returncode != 0:
        subprocess.run(['tmux', 'new-session', '-d', '-s', session_name])
    cmd = "./exec.sh --interactive"
    subprocess.run(['tmux', 'send-keys', '-t', session_name, cmd,'Enter'])   

def revoke_allocation():
    try:
        session_name = 'flesctrl'
        cmd = 'exit'
        subprocess.run(['tmux', 'send-keys', '-t', session_name, cmd,'Enter'])
        #logger.success("Process killed")
    except Exception as e:
        return False
    return True


def start_flesctrl():
    session_name = 'flesctrl'
    session_exists = subprocess.run(
        ['tmux', 'has-session', '-t', session_name],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    if session_exists.returncode != 0:
        subprocess.run(['tmux', 'new-session', '-d', '-s', session_name])
    cmd = "./execution.py --interactive"
    subprocess.run(['tmux', 'send-keys', '-t', session_name, cmd,'Enter'])   
    
def stop_flesctrl():
    try:
        session_name = 'flesctrl'
        cmd = 'C-c'
        subprocess.run(['tmux', 'send-keys', '-t', session_name, cmd,'Enter'])
        #logger.success("Process killed")
    except Exception as e:
        return False
    return True
        