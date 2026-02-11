#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#Created on Wed Jan 28 18:48:28 2026

#@author: jschlieffen


"""
Usage: tf_input_node.py <input_file> <logfile> <input_node_idx> <input_node_ip> <logfile_collectl> <logfile_tsclient>

Arguments: 
    <input_file> The .tsa input file
    <logfile> The Logfile to use
    <input_node_idx> The index of the current input node
    <input_node_ip> The ip of the input node
    <logfile_collectl> The csv-file which collectl should use
    <logfile_tsclient> The logfile for the tsclient if used
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

def ethernet_ip():
    command = 'ip a' 
    try:
        result = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)    
        stdout,stderr = result.communicate()
    except subprocess.CalledProcessError as e:
        print(e)
    match = re.search(r'eth0:(.*?)scope global eth0',stdout,re.DOTALL)
    content = match.group(1)
    match2 = re.search(r'inet (.*?)/23',content,re.DOTALL)
    content2 = match2.group(1)
    return content2
    
def infiniband_ip():
    #print(node_id)
    command = 'ip a' 
    try:
        result = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout,stderr = result.communicate()
    except subprocess.CalledProcessError as e:
        print(e)
    match = re.search(r'ib0:(.*?)scope global ib0',stdout,re.DOTALL)
    content = match.group(1)
    match2 = re.search(r'inet (.*?)/23',content,re.DOTALL)
    content2 = match2.group(1)
    return content2   
     
def get_node_ip(use_infiniband):
    if use_infiniband == 1:
        return infiniband_ip()
    else:
        return ethernet_ip()  

# =============================================================================
# TODO:use_iofniband
# =============================================================================
def calc_str(input_node_ip,port,cm_node_ip,input_node_idx):
    ip = get_node_ip(1)
    shm_str = f"fles_out_b{input_node_idx}"
    str_ = f"-i {input_node_ip}:{port} -m {cm_node_ip}:{port} -n {input_node_idx} -g 1 --shm-id {shm_str}"
    return str_,shm_str

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
        f.write(f"TF Input {node_name}: done {msg}")
        f.flush()
        os.fsync(f.fileno())

def start_tsclient(path,input_file,shm_str, logfile_tsclient, use_dtsa_files ,tsclient_communicater):
    if use_dtsa_files == 1:
        dtsa_command = "-D 1"
    else:
        dtsa_command = ""
    tsclient_command = f"{path}./tsclient -L {logfile_tsclient} -i file:{input_file} -o shm:{shm_str}?n=26 {dtsa_command}"
    result_tsclient = subprocess.Popen(tsclient_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    #result_tsclient.wait()
    while True:
        msg = tsclient_communicater.get()
        if msg == 'exit':
            #print('test tsclient')
            result_tsclient.terminate()
            result_tsclient.wait()
            break

def input_node(input_node_ip,port,cm_node_ip,input_node_idx,use_collectl,use_infiniband, path, input_file, use_flesnet, logfile_tsclient, use_dtsa_files,logfile_collectl):
    print('input node path:', os.getcwd())
    str_,shm_str = calc_str(input_node_ip,port,cm_node_ip,input_node_idx)
    node_name = subprocess.check_output(["hostname", "-s"]).decode().strip()
    if use_collectl == 1:
        print(use_collectl)
        print(logfile_collectl)
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
    if use_flesnet == 0:
        #tsclient_commands = '%s./tsclient -i %s -O fles_in_e%s %s > /dev/null 2>&1 &' % (path,dmsa_file, str(entry_node_idx), D_flag)
        #result_tsclient = subprocess.Popen(tsclient_commands, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        tsclient_communicater = queue.Queue()
        print(use_dtsa_files)
        print(type(use_dtsa_files))
        thread_tsclient = threading.Thread(target=start_tsclient, args=(path,input_file, shm_str, logfile_tsclient, use_dtsa_files, tsclient_communicater))
        thread_tsclient.start()
        time.sleep(1)
    input_node_commands = (
        '%s./timeslice_forwarder %s > %s 2>&1 &' 
        % (path,str_,logfile)
    )
    '''
    input_node_commands = (
        '%s./timeslice_forwarder %s' 
        % (path,str_)
    )
    '''
    print(input_node_commands)
    result_input_node = subprocess.Popen(input_node_commands, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, preexec_fn=os.setsid)
    input_data = ''
    msg,action = "", ""
    prev_action = ""
    while True:
        time.sleep(0.5)
        try:
            with open("tmp/central_manager.txt", "r") as f:
                msg = f.read().strip()
                #ode, action = line.split(": ")

        except FileNotFoundError:
            msg = ""
        #print(msg)
        #print(node_name)
        if f"TF Input {node_name}" in msg:
            #print(msg)
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
                os.killpg(os.getpgid(result_input_node.pid), signal.SIGKILL)
                print('test kill 1')
                write_response(node_name, "killing")
                prev_action = action
            elif action == "revive":
                result_input_node = subprocess.Popen(input_node_commands, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,preexec_fn=os.setsid)
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
    if use_flesnet == 0:
        #result_mstool.terminate()
        #result_mstool.wait()
        tsclient_communicater.put("exit")
        thread_tsclient.join()
    result_input_node.terminate()
    result_input_node.wait()
    #os.killpg(result_input_node.pid, signal.SIGTERM)
    #stdout, stderr = result_input_node.communicate(timeout=5)
    #print("STDOUT:")
    #print(stdout)
    
    #print("STDERR:")
    #print(stderr)
    write_response(node_name, "terminating")
    

params = {}
#print('test12')
with open('tmp/tf_input_nodes_params.txt', 'r') as f:
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

cm_node_ip = params.get('cm node ips')

arg = docopt.docopt(__doc__, version='0.2')
input_file = arg["<input_file>"]
logfile = arg["<logfile>"]
input_node_idx = arg["<input_node_idx>"]
input_node_ip = arg["<input_node_ip>"]
logfile_collectl = arg['<logfile_collectl>']
logfile_tsclient = arg['<logfile_tsclient>']
#customize_string = "--timeslice-size 100 --processor-instances 0 -e \"../../../build/./tsclient -i shm:%s -o tcp://*:5556\""

input_node(input_node_ip,port,cm_node_ip,input_node_idx,use_collectl,use_infiniband, path, input_file, use_flesnet, logfile_tsclient, use_dtsa_files,logfile_collectl)

