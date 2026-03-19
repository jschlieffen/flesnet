#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#Created on Wed Mar 11 16:01:17 2026

#@author: jschlieffen


"""
Usage: timeslice_forwarding_sender.py <input_file> <logfile> <input_node_idx> <logfile_collectl> <input_node_ip>

Arguments: 
    <input_file> The .tsa input file
    <logfile> The Logfile to use
    <input_node_idx> The index of the input node given by flesctrl
    <logfile_collectl> The csv-file which collectl should use
    <input_node_ip> The input node ip 
"""

import subprocess
import time
import docopt
import sys
import os
import threading
import queue
import signal
import re


def calc_str(input_file, port, use_flesnet, input_node_idx, input_node_ip):
    if use_flesnet:
        input_str = f"-i shm:fles_out_b{input_node_idx}"
    else:
        input_str = f"-i file:{input_file}"
    ip_str = f"-o tcp://*:{port}"
    return input_str, ip_str

def start_collectl(use_infiniband, csvfile_name):
    if use_infiniband == 1:
        collectl_command = f"sudo collectl --plot --sep , -i 1 -sx > {csvfile_name}"
        #print(collectl_command)
    else:
        collectl_command = f"collectl --plot --sep , -i 1 -sn > {csvfile_name}"
    result_collectl = subprocess.Popen(collectl_command,shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    time.sleep(1)
    return result_collectl

def start_collectl_cpu(csv_file_name):
    cpu_csv_file_name = csv_file_name.replace(".csv", "_cpu_usage.csv")
    collectl_command = f"collectl --plot --sep , -i 1 -sC > {cpu_csv_file_name}"
    result_collectl = subprocess.Popen(collectl_command,shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    time.sleep(1)
    return result_collectl


def start_collectl_thread(use_infiniband, logfile_collectl, collectl_communicater):
    result_collectl = start_collectl(use_infiniband, logfile_collectl)
    result_collectl_cpu = start_collectl_cpu(logfile_collectl)
    while True:
        msg = collectl_communicater.get()
        if msg == "exit":
            result_collectl.terminate()
            result_collectl.wait()
            result_collectl_cpu.terminate()
            result_collectl_cpu.wait()
            break


def get_alloc_cpus(filename):
    taskset_command = "taskset -cp $$"
    result_taskset = subprocess.Popen(taskset_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = result_taskset.communicate()
    match = stdout.split(":")[-1].strip()
    entries = match.split(",")
    alloc_cpus = []
    for entry in entries:
        if "-" in entry:
            start, end = map(int, entry.split("-"))
            alloc_cpus.extend(range(start,end + 1))
        else:
            alloc_cpus.append(int(entry))
    with open(filename, "w") as file:
        for cpu in alloc_cpus:
            file.write(f"{cpu}\n")

def write_response(node_name, msg):
    with open("tmp/nodes_response.txt", "w") as f:
        f.write(f"Sender {node_name}: done {msg}")
        f.flush()
        os.fsync(f.fileno())


def input_node(port, input_node_idx, use_collectl, path, input_file, use_flesnet , logfile, use_dtsa_files, logfile_collectl, use_grafana, influx_token, influx_node_ip, use_infiniband, input_node_ip):
    input_str, ip_str = calc_str(input_file, port, use_flesnet, input_node_idx, input_node_ip)
    node_name = subprocess.check_output(["hostname", "-s"]).decode().strip()
    if use_collectl == 1:
        basename = os.path.splitext(os.path.basename(logfile))[0]
        filename_cpus = f"tmp/{basename}.txt"
        get_alloc_cpus(filename_cpus)
        collectl_communicater = queue.Queue()
        thread_collectl = threading.Thread(target=start_collectl_thread, args=(use_infiniband, logfile_collectl, collectl_communicater))
        thread_collectl.start()
        time.sleep(1)
    grafana_string = ''
    if use_grafana == 1:
        os.environ['CBM_INFLUX_TOKEN'] = influx_token
        grafana_string = '-m influx2:%s:8086:tsclient_status:' % (influx_node_ip) 
    D_flag = ""
    if use_dtsa_files == 1:
        D_flag = "-D 1"
    input_node_commands = (
        '%s./tsclient -L %s %s %s %s %s' 
        % (path,logfile,input_str, ip_str, grafana_string, D_flag)
    )
    print(input_node_commands)
    result_input_node = subprocess.Popen(input_node_commands, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, preexec_fn=os.setsid)
    msg,action = "",""
    prev_action = ""
    while True:
        time.sleep(0.5)
        try:
            with open("tmp/central_manager.txt", "r") as f:
                msg = f.read().strip()
                f.close()

        except FileNotFoundError:
            msg = ""
        if f"Sender {node_name}" in msg:
            node, action = msg.split(": ")

            if action == prev_action:
                continue
            if action == "kill":
                os.killpg(os.getpgid(result_input_node.pid), signal.SIGKILL)
                write_response(node_name, 'killing')
                prev_action = action
            elif action == "revive":
                result_input_node = subprocess.Popen(input_node_commands, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, preexec_fn=os.setsid)
                write_response(node_name,'reviving')
                prev_action = action
            elif action == "stop":
                break
    if use_collectl == 1:
        collectl_communicater.put("exit")
        thread_collectl.join()
    result_input_node.terminate()
    result_input_node.wait()
    write_response(node_name, "terminating")

    
params = {}
with open('tmp/sender_nodes_params.txt', 'r') as f:
    for line in f:
        if ':' in line:
            key, value = line.strip().split(':', 1)
            value = value.strip()
            if value.lower() == 'true':
                value = True
            elif value.lower() == 'false':
                value = False
            else:
                try:
                    value = int(value)
                except ValueError:
                    pass
            params[key] = value
    f.close()

for key, value in params.items():
    globals()[key] = value
    
arg = docopt.docopt(__doc__, version='0.2')
input_file = arg["<input_file>"]
logfile = arg["<logfile>"]
input_node_idx = arg["<input_node_idx>"]
logfile_collectl = arg["<logfile_collectl>"]
input_node_ip = arg["<input_node_ip>"]

input_node(port, input_node_idx, use_collectl, path, input_file, use_flesnet, logfile, use_dtsa_files, logfile_collectl, use_grafana, influx_token, influx_node_ip, use_infiniband, input_node_ip)