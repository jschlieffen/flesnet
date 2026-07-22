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
import nodes_communicator as nc
import thread_channel
import nodes_help_functions as nh
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
        shm_string += "shm://%s/fles_out_b%s " % (parts_build[i],str(i))
    return ip_string, shm_string

def start_timeslice_forwarded_input(logfile_tf,build_node_idx,use_infiniband):
    logfile_collectl="dwd"
    input_file="efdf"
    logfile_tsclient="sifew"
    node_ip = nh.get_node_ip(use_infiniband)
    tf_input_command = "nodes/./tf_input_node.py %s %s %s %s %s %s" % (input_file,logfile_tf,build_node_idx,node_ip,logfile_collectl, logfile_tsclient)
    print(tf_input_command)
    result_tf_input = subprocess.Popen(tf_input_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,preexec_fn=os.setsid)
    return result_tf_input

def start_timeslice_forwarded_input_GSI(logfile_tf, build_node_idx, use_infiniband):
    logfile_collectl = "dwdw"
    input_file = "efefd"
    logfile_tsclient="sifew"
    node_ip = nh.get_node_ip(use_infiniband)
    tf_input_command = "nodes/./timeslice_forwarding_sender.py %s %s %s %s %s %s" % (input_file,logfile_tf, build_node_idx, logfile_collectl, node_ip,logfile_tsclient)
    result_tf_input = subprocess.Popen(tf_input_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,preexec_fn=os.setsid)
    return result_tf_input
    
def build_nodes(ip, build_nodes_ip,logfile, num_build_nodes, build_node_idx, influx_node_ip, influx_token, use_grafana,path, 
                transport_method, customize_string, use_infiniband, use_collectl, logfile_collectl, desc_size,data_size,logfile_tf, use_tf_zib, use_tf_GSI):
    ip_string, shm_string = calc_str(ip, build_nodes_ip, num_build_nodes,desc_size,data_size)
    node_name = subprocess.check_output(["hostname", "-s"]).decode().strip()
    channel = thread_channel.Channel()
    communicator = nc.communicator(channel, "Build", node_name)
    communicator.start()
    if use_collectl == 1:
        basename = os.path.splitext(os.path.basename(logfile))[0]
        filename_cpus = f"tmp/{basename}.txt"
        nh.get_alloc_cpus(filename_cpus)
        collectl_communicater = queue.Queue()
        thread_collectl = threading.Thread(target=nh.start_collectl_thread, args=(use_infiniband, logfile_collectl, collectl_communicater))
        thread_collectl.start()
        time.sleep(1)
    grafana_string = ''
    if use_grafana == 1:
        os.environ['CBM_INFLUX_TOKEN'] = influx_token
        grafana_string = '-m influx2:%s:flesnet_status: ' % (influx_node_ip)
    flesnet_commands = (
        '%s./flesnet -t %s -L %s -l 1 -I %s -o %s -O %s %s %s > /dev/null 2>&1 &'
        % (path, transport_method, logfile, ip_string, build_node_idx, shm_string, 
           customize_string, grafana_string)
    )
    print(flesnet_commands)
    result_flesnet = subprocess.Popen(flesnet_commands, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,preexec_fn=os.setsid)
    msg,action = "", ""
    prev_action = ""
    if use_tf_zib == 1:
        result_tf_input = start_timeslice_forwarded_input(logfile_tf, build_node_idx, use_infiniband)
    elif use_tf_GSI == 1:
        result_tf_input = start_timeslice_forwarded_input_GSI(logfile_tf, build_node_idx, use_infiniband)
    msg = ""
    while True:
        msg = channel.recv_from_child()
        match msg:
            case "kill":
                os.killpg(os.getpgid(result_flesnet.pid), signal.SIGKILL)
                channel.send_to_child("succeed")
            case "revieve":
                result_flesnet = subprocess.Popen(flesnet_commands, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,preexec_fn=os.setsid)
                channel.send_to_child("succeed")
            case "stop":

                break
    
    if use_collectl == 1:
        collectl_communicater.put("exit")
        thread_collectl.join()
    result_flesnet.terminate()
    result_flesnet.wait()
    if use_tf_zib == 1 or use_tf_GSI == 1:
        stdout, stderr = result_tf_input.communicate()
        print(f"Output tf input: {stdout}")
        print(f"Error tf input: {stderr}")
    channel.send_to_child("succeed")
    communicator.join()


params = {}
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
            transport_method, customize_string, use_infiniband, use_collectl, logfile_collectl,desc_size,data_size, logfile_tf, ZIB_timesliceforwarding, activate_timesliceforwarding)
