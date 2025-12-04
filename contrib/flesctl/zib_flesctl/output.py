#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#Created on Thu Jan  9 11:24:40 2025

#@author: jschlieffen
"""
Usage: output.py <logfile> <build_node_idx> <logfile_collectl>

Arguments: 
    <logfile> The Logfile to use
    <build_node_idx> The index of the current build node
    <logfile_collectl> The csv-file which collectl should use
"""


import subprocess
import time
import docopt
import sys
import os
import threading
import queue


# =============================================================================
# This file starts flesnet on a build node. It is started with 
#   srun nodelist=node output.py -N 1 <params>  
# After flesnet is started the program waits for a signal from the 
# central manager. If it receives a signal it will shut down flesnet 
# NOTE: If the program does not terminate correctly, it completly suffices 
#       to just kill the srun process. One does not have to kill  flesnet manually
# =============================================================================

def calc_str(ip,num_build_nodes):
    ip_string = ""
    parts = ip.split('sep')
    for part in parts:
        if part != "":
            ip_string += "tcp://" + part + '/0 '
    shm_string = ""
    for i in range(0,int(num_build_nodes)):
        shm_string += "shm:/fles_out_b%s/0 " % (str(i))
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
            #print('test collectl')
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

def build_nodes(ip,logfile, num_build_nodes, build_node_idx, influx_node_ip, influx_token, use_grafana,path, 
                transport_method, customize_string, use_infininband, use_collectl, logfile_collectl):
    ip_string, shm_string = calc_str(ip, num_build_nodes)
    if use_collectl == 1:
        basename = os.path.splitext(os.path.basename(logfile))[0]
        filename_cpus = f"tmp/{basename}.txt"
        get_alloc_cpus(filename_cpus)
        #result_collectl = start_collectl(use_infiniband, logfile_collectl)
        #result_collectl_cpu = start_collectl_cpu(logfile_collectl)
        collectl_communicater = queue.Queue()
        thread_collectl = threading.Thread(target=start_collectl_thread, args=(use_infiniband, logfile_collectl, collectl_communicater))
        thread_collectl.start()
        time.sleep(1)
    grafana_string = ''
    if use_grafana == 1:
        os.environ['CBM_INFLUX_TOKEN'] = influx_token
        grafana_string = '-m influx2:%s:8086:flesnet_status: ' % (influx_node_ip)
    flesnet_commands = (
        '%s./flesnet -t %s -L %s -l 1 -I %s -o %s -O %s %s %s > /dev/null 2>&1 &'
        % (path, transport_method, logfile, ip_string, build_node_idx, shm_string, 
           customize_string, grafana_string)
    )
    print(flesnet_commands)
    result_flesnet = subprocess.Popen(flesnet_commands, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    input_data = ''
    #print(flesnet_commands)
    #print(result_flesnet)
    while 'stop' not in input_data:
        input_data = sys.stdin.read().strip()
        if input_data == 'kill':
            print('kill')
            #result_flesnet.terminate()
            #result_flesnet.wait()
        elif input_data == 'revieve':
            print('revieve')
            #result_flesnet = subprocess.Popen(flesnet_commands, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    print(input_data)
    print(type(input_data))
    if use_collectl == 1:
        #result_collectl.terminate()
        #result_collectl.wait()
        #result_collectl_cpu.terminate()
        #result_collectl_cpu.wait()
        collectl_communicater.put("exit")
        thread_collectl.join()
    result_flesnet.terminate()
    result_flesnet.wait()

params = {}
#print('test12')
with open('tmp/build_nodes_params.txt', 'r') as f:
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

#print(params)
for key, value in params.items():
    globals()[key] = value

ip = params.get('entry node ips')

arg = docopt.docopt(__doc__, version='0.2')

logfile = arg["<logfile>"]
build_node_idx = arg["<build_node_idx>"]
logfile_collectl = arg['<logfile_collectl>']

build_nodes(ip,logfile, num_buildnodes, build_node_idx, influx_node_ip, influx_token, use_grafana,path, 
            transport_method, customize_string, use_infiniband, use_collectl, logfile_collectl)
