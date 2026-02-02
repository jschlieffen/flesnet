#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#Created on Wed Jan 28 16:04:43 2026

#@author: jschlieffen


"""
Usage: tf_central_manager.py <logfile> <logfile_collectl>

Arguments: 
    <logfile> The Logfile to use
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


def calc_str(ip,port):
    return f"-m {ip}:{port}"

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

def write_response(node_name, msg):
    with open("tmp/nodes_response.txt", "w") as f:
        f.write(f"TF Central Manager {node_name}: done {msg}")
        f.flush()
        os.fsync(f.fileno())

def central_manager(ip,port,logfile,logfile_collectl,use_collectl,use_infiniband,path):
    ip_string = calc_str(ip, port)
    node_name = subprocess.check_output(["hostname", "-s"]).decode().strip()
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
    '''
    grafana_string = ''
    if use_grafana == 1:
        os.environ['CBM_INFLUX_TOKEN'] = influx_token
        grafana_string = '-m influx2:%s:8086:flesnet_status:' % (influx_node_ip) 
    '''
    cm_commands = (
        '%s./timeslice_forwarder %s > %s 2>&1 &' 
        % (path, ip_string,logfile)
    )
    print(cm_commands)
    result_cm = subprocess.Popen(cm_commands, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, preexec_fn=os.setsid)
    input_data = ''
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
        #print(msg)
        #print(node_name)
        if f"TF Central Manager {node_name}" in msg:
            #print('test')
            #print(action)
            node, action = msg.split(": ")
            #print(node)
            #print('action ' + action)
            if action == prev_action: 
                continue
            if action == "kill":
                print('test kill')
                #result_flesnet.terminate()
                #result_flesnet.wait()
                os.killpg(os.getpgid(result_cm.pid), signal.SIGKILL)
                print('test kill 1')
                write_response(node_name, "killing")
                prev_action = action
            elif action == "revive":
                result_cm = subprocess.Popen(cm_commands, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,preexec_fn=os.setsid)
                write_response(node_name, "reviving")
                prev_action = action
            elif action == "stop":
                print('test action')
                break
    
    #print(input_data)
    #print(type(input_data))
    if use_collectl == 1:
        #result_collectl.terminate()
        #result_collectl.wait()
        #result_collectl_cpu.terminate()
        #result_collectl_cpu.wait()
        collectl_communicater.put("exit")
        thread_collectl.join()
    result_cm.terminate()
    result_cm.wait()
    write_response(node_name, "terminating")
    

params = {}
#print('test12')
with open('tmp/tf_cm_nodes_params.txt', 'r') as f:
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

print(params)
for key, value in params.items():
    globals()[key] = value

ip = params.get('cm node ips')
#print(entry_nodes_ips)
arg = docopt.docopt(__doc__, version='0.2')
logfile = arg["<logfile>"]
logfile_collectl = arg['<logfile_collectl>']
#customize_string = "--timeslice-size 100 --processor-instances 0 -e \"../../../build/./tsclient -i shm:%s -o tcp://*:5556\""

central_manager(ip,port,logfile,logfile_collectl,use_collectl,use_infiniband,path)

