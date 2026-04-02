#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#Created on Wed Jan  8 16:54:02 2025

#@author: jschlieffen

"""
Usage: input.py <input_file> <logfile> <entry_node_idx> <logfile_collectl>

Arguments: 
    <input_file> The input dmsa file for the mstool
    <logfile> The Logfile to use
    <entry_node_idx> The index of the current entry node
    <logfile_collectl> The csv-file which collectl should use
"""

import subprocess
import time
import docopt
import sys
import os
import threading
import queue
import signal

# =============================================================================
# This file starts mstool and flesnet on an entry node. It is started with 
#   srun nodelist=node input.py -N 1 <params>  
# After flesnet is started the program waits for a signal from the 
# central manager. If it receives a signal it will shut down flesnet and the 
# mstool. 
# NOTE: If the program does not terminate correctly, it completly suffices 
#       to just kill the srun process. One does not have to kill mstool and 
#       flesnet manually
# =============================================================================

def calc_str(ip, entry_nodes_ip ,num_entry_nodes, use_pattern_gen,mean,size_var,pattern,overlap):
    ip_string = ""
    parts = ip.split('sep')
    for part in parts:
        if part != "":
            ip_string += "tcp://" + part + '/0 '
    parts_entry = entry_nodes_ips.split('sep')
    shm_string = ""
    if use_pattern_gen == 1:
        for i in range(0,int(num_entry_nodes)):
            shm_string += "pgen://%s/fles_in_e%s?mean=%s\&size_var=%s\&overlap=%s\&pattern=%s " % (parts_entry[i],str(i),mean, size_var,overlap,pattern)
    else: 
        for i in range(0,int(num_entry_nodes)):
            shm_string += "shm://%s/fles_in_e%s/0 " % (parts_entry[i],str(i))
    return ip_string, shm_string

def start_collectl(use_infiniband, csvfile_name):
    if use_infiniband == 1:
        collectl_command = f"sudo collectl --plot --sep , -i 1 -sx > {csvfile_name}"
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

def start_mstool(path,dmsa_file, entry_node_idx, D_flag, mstool_communicater):
    mstool_commands = '%s./mstool -i %s -O fles_in_e%s %s > /dev/null 2>&1 &' % (path,dmsa_file, str(entry_node_idx), D_flag)
    result_mstool = subprocess.Popen(mstool_commands, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    while True:
        msg = mstool_communicater.get()
        if msg == 'exit':
            result_mstool.terminate()
            result_mstool.wait()
            break
    
    
def write_response(node_name, msg):
    with open("tmp/nodes_response.txt", "w") as f:
        f.write(f"Entry {node_name}: done {msg}")
        f.flush()
        os.fsync(f.fileno())

def entry_nodes(dmsa_file,ip, entry_nodes_ip,logfile, num_entry_nodes, entry_node_idx, influx_node_ip, influx_token, use_grafana,path, 
                transport_method, customize_string, use_pattern_gen, use_dmsa_files, use_infiniband, use_collectl, logfile_collectl,
                mean,size_var,pattern,overlap):
    ip_string, shm_string = calc_str(ip, entry_nodes_ip, num_entry_nodes, use_pattern_gen, mean,size_var,pattern,overlap)
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
        grafana_string = '-m influx2:%s:8086:flesnet_status:' % (influx_node_ip) 
    D_flag = ""
    if use_dmsa_files == 1:
        D_flag = "-D 1"
    if use_pattern_gen == 0:
        mstool_commands = '%s./mstool -i %s -O fles_in_e%s %s > /dev/null 2>&1 &' % (path,dmsa_file, str(entry_node_idx), D_flag)
        print(mstool_commands)
        mstool_communicater = queue.Queue()
        thread_mstool = threading.Thread(target=start_mstool, args=(path, dmsa_file, entry_node_idx, D_flag, mstool_communicater))
        thread_mstool.start()
        time.sleep(1)
    customize_string = customize_string.replace("--processor-instances 1 -e", "--processor-instances 0 -e")
    flesnet_commands = (
        '%s./flesnet -t %s -L %s -l 1 -i %s -I %s -O %s %s %s > /dev/null 2>&1 &' 
        % (path,transport_method,logfile,str(entry_node_idx), shm_string,ip_string,
          customize_string, grafana_string)
    )
    print(flesnet_commands)
    result_flesnet = subprocess.Popen(flesnet_commands, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, preexec_fn=os.setsid)
    msg,action = "", ""
    prev_action = ""
    while True:
        time.sleep(0.5)
        try:
            with open("tmp/central_manager.txt", "r") as f:
                msg = f.read().strip()
                #ode, action = line.split(": ")
                f.close()

        except FileNotFoundError:
            msg = ""
        if f"Entry {node_name}" in msg:
            node, action = msg.split(": ")
            if action == prev_action: 
                continue
            if action == "kill":
                os.killpg(os.getpgid(result_flesnet.pid), signal.SIGKILL)
                write_response(node_name, "killing")
                prev_action = action
            elif action == "revive":
                result_flesnet = subprocess.Popen(flesnet_commands, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,preexec_fn=os.setsid)
                write_response(node_name, "reviving")
                prev_action = action
            elif action == "stop":
                break
    if use_collectl == 1:
        collectl_communicater.put("exit")
        thread_collectl.join()
    if use_pattern_gen == 0:
        mstool_communicater.put("exit")
        thread_mstool.join()
    result_flesnet.terminate()
    result_flesnet.wait()
    write_response(node_name, "terminating")
    

params = {}
with open('tmp/entry_nodes_params.txt', 'r') as f:
    print('test1')
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

entry_nodes_ips = params.get('entry node ips')
ip = params.get('build node ips')
arg = docopt.docopt(__doc__, version='0.2')
input_file = arg["<input_file>"]
logfile = arg["<logfile>"]
entry_node_idx = arg["<entry_node_idx>"]
logfile_collectl = arg['<logfile_collectl>']

entry_nodes(input_file,ip, entry_nodes_ips, logfile,num_entrynodes, entry_node_idx, influx_node_ip, influx_token, use_grafana,path, 
            transport_method, customize_string, use_pattern_gen, use_dmsa_files, use_infiniband, use_collectl,
            logfile_collectl, mean, size_var,pattern,overlap)



    