#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#Created on Thu Jan  9 11:24:40 2025

#@author: jschlieffen
"""
Usage: output.py <logfile> <build_node_idx> <logfile_collectl> <logfile_tf>

Arguments: 
    <logfile> The Logfile to use
    <build_node_idx> The index of the current build node
    <logfile_collectl> The csv-file which collectl should use
    <logfile_tf> The logfile for the timeslice-forwarding
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
from datetime import datetime

# =============================================================================
# This file starts flesnet on a build node. It is started with 
#   srun nodelist=node output.py -N 1 <params>  
# After flesnet is started the program waits for a signal from the 
# central manager. If it receives a signal it will shut down flesnet 
# NOTE: If the program does not terminate correctly, it completly suffices 
#       to just kill the srun process. One does not have to kill  flesnet manually
# =============================================================================

def calc_str(ip, build_nodes_ip,num_build_nodes,desc_size,data_size):
    ip_string = ""
    parts = ip.split('sep')
    for part in parts:
        if part != "":
            ip_string += "tcp://" + part + '/0 '
    parts_build = build_nodes_ip.split('sep')
    shm_string = ""
    for i in range(0,int(num_build_nodes)):
        #shm_string += "shm://%s/fles_out_b%s?desc_size=%s\&data_size=%s " % (parts_build[i],str(i),desc_size,data_size)
        shm_string += "shm://%s/fles_out_b%s" % (parts_build[i],str(i))
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


def write_response(node_name, msg):
    with open("tmp/nodes_response.txt", "w") as f:
        f.write(f"Build {node_name}: done {msg}")
        f.flush()
        os.fsync(f.fileno())
        
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
        
def start_timeslice_forwarded_input(logfile_tf,build_node_idx,use_infiniband):
    logfile_collectl="dwd"
    input_file="efdf"
    logfile_tsclient="sifew"
    node_ip = get_node_ip(use_infiniband)
    tf_input_command = "nodes/./tf_input_node.py %s %s %s %s %s %s" % (input_file,logfile_tf,build_node_idx,node_ip,logfile_collectl, logfile_tsclient)
    print(os.getcwd())
    print(tf_input_command)
    result_tf_input = subprocess.Popen(tf_input_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,preexec_fn=os.setsid)
    #print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    return result_tf_input
    
def build_nodes(ip, build_nodes_ip,logfile, num_build_nodes, build_node_idx, influx_node_ip, influx_token, use_grafana,path, 
                transport_method, customize_string, use_infiniband, use_collectl, logfile_collectl, desc_size,data_size,logfile_tf, use_tf_zib):
    ip_string, shm_string = calc_str(ip, build_nodes_ip, num_build_nodes,desc_size,data_size)
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
    result_flesnet = subprocess.Popen(flesnet_commands, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,preexec_fn=os.setsid)
    input_data = ''
    #print(flesnet_commands)
    #print(result_flesnet)
    """
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
    """
    msg,action = "", ""
    prev_action = ""
    print(use_tf_zib)
    if use_tf_zib == 1:
        result_tf_input = start_timeslice_forwarded_input(logfile_tf, build_node_idx, use_infiniband)
    while True:
        #print(msg)
        time.sleep(0.5)
        try:
            with open("tmp/central_manager.txt", "r") as f:
                msg = f.read().strip()
                #ode, action = line.split(": ")

        except FileNotFoundError:
            msg = ""
        #print(type(msg))
        #print('htc-cmp506' in msg)
        #print('test')
        if f"Build {node_name}" in msg:
            #print('test')
            #print(action)
            #print(msg)
            node, action = msg.split(": ")
            #print(node)
            #print('action ' + action)
            if action == prev_action: 
                continue
            elif action == "kill":
                #print('test kill')
                #result_flesnet.terminate()
                #result_flesnet.wait()
                os.killpg(os.getpgid(result_flesnet.pid), signal.SIGKILL)

                print('test kill 1')
                write_response(node_name, "killing")
                prev_action = action
            elif action == "revive":
                result_flesnet = subprocess.Popen(flesnet_commands, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,preexec_fn=os.setsid)
                write_response(node_name, "reviving")
                prev_action = action
            elif action == "stop":
                print('test action')
                break
    
    if use_collectl == 1:
        #result_collectl.terminate()
        #result_collectl.wait()
        #result_collectl_cpu.terminate()
        #result_collectl_cpu.wait()
        collectl_communicater.put("exit")
        thread_collectl.join()
    result_flesnet.terminate()
    result_flesnet.wait()
    if use_tf_zib == 1:
        stdout, stderr = result_tf_input.communicate()
        print(f"Output tf input: {stdout}")
        print(f"Error tf input: {stderr}")
    write_response(node_name, "terminating")

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
build_nodes_ip = params.get('build node ips')
arg = docopt.docopt(__doc__, version='0.2')

logfile = arg["<logfile>"]
build_node_idx = arg["<build_node_idx>"]
logfile_collectl = arg['<logfile_collectl>']
logfile_tf = arg["<logfile_tf>"]

build_nodes(ip, build_nodes_ip,logfile, num_buildnodes, build_node_idx, influx_node_ip, influx_token, use_grafana,path, 
            transport_method, customize_string, use_infiniband, use_collectl, logfile_collectl,desc_size,data_size, logfile_tf, ZIB_timesliceforwarding)
