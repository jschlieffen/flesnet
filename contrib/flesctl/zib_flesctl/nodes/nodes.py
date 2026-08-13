#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 10 14:44:50 2026

@author: jschlieffen
"""

# =============================================================================
# This file is under construction
# TODO: make class worker and worker manager.
# =============================================================================

import subprocess
import time 
import threading 
import queue
import os
import signal
import re 
import nodes_communicator as nc
import thread_channel
import nodes_help_functions as nh

def threads_starter(command, communicator):
    print(command)
    result = subprocess.Popen(command,  stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True, preexec_fn=os.setsid)
    while True:
        msg = communicator.get()
        if msg == 'exit':
            result.terminate()
            result.wait()
            break
        elif msg == 'kill':
            os.killpg(os.getpgid(result.pid),signal.SIGKILL)
            break

def main(node_name,threads_components):
    
    channel = thread_channel.Channel()
    communicator = nc.communicator(channel, node_name)
    communicator.start()
    workers = {}
    for index, process_command in threads_components.items():
        communicator_thread = queue.Queue()
        thread_res = threading.Thread(
            target=threads_starter,
            args=(process_command, communicator_thread)
        )
        thread_res.start()
        workers[index] = {
                'communicator' : communicator_thread,
                'res' : thread_res,
                'status' : True
            }
    while True:
        msg = channel.recv_from_child()
        process, command = msg.split(": ")
        match command:
            case "kill":
                kill_thread_communicator = workers[process]['communicator']
                thread_ = workers[process]['res']
                kill_thread_communicator.put('kill')
                thread_.join()
                #os.killpg(os.getpgid(kill_thread),signal.SIGKILL)
                channel.send_to_child('succeed')
                workers[process]['status'] = False
            case "revive":
                revive_command = threads_components[process]
                communicator_thread = queue.Queue()
                thread_res = threading.Thread(
                        target=threads_starter,
                        args=(revive_command, communicator_thread)
                    )
                thread_res.start()
                workers[process]['res'] = thread_res
                workers[process]['communicator'] = communicator_thread
                workers[process]['status'] = True
            case "stop":
                break
            
    for index,threads in workers.items():
        if threads['status']:
            communicator_thread = threads['communicator']
            thread_ = threads['res']
            communicator_thread.put('exit')
            thread_.join()
    channel.send_to_child('succeed')
    communicator.join()
    
node_name = subprocess.check_output(["hostname", "-s"]).decode().strip()
thread_components = {}
with open(f'tmp/params/{node_name}.txt','r') as f:
    for line in f:
        if ':' in line:
            key, value = line.strip().split(':', 1)
            value = value.strip()
            if 'command' in key:
                tmp, index = key.split('_')
                thread_components[index] = value

main(node_name,thread_components)
                
                
            
        