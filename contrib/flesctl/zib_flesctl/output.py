#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#Created on Thu Jan  9 11:24:40 2025

#@author: jschlieffen
"""
Usage: output.py <logfile> <ip> <num_build_nodes> <build_node_idx> <influx_node_ip> <influx_token> <use_grafana> <path> <transport_method> <customize_string> <use_infiniband> <use_collectl> <logfile_collectl>

Arguments: 
    <logfile> The Logfile to use
    <ip> The ip address to use
    <num_build_nodes> The number of build nodes
    <build_node_idx> The index of the current build node
    <influx_node_ip> The ip of the where the influx container is runnning
    <influx_token> The token to the influx-db
    <use_grafana> enables/disables grafana
    <path> The path to flesnet/mstool
    <transport_method> The transport method (rdma/zeromq, libfabric currently not implemented)
    <customize_string> The remaining params for flesnet
    <use_infiniband> Decides whether infiniband shall be used or ethernet
    <use_collectl> Decides if collectl should be used for tracking the network usage
    <logfile_collectl> The csv-file which collectl should use
"""


import subprocess
import time
import docopt
import sys
import os


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
    if use_infiniband == '1':
        collectl_command = f"sudo collectl --plot --sep , -i 1 -sx > {csvfile_name}"
    else:
        collectl_command = f"collectl --plot --sep , -i 1 -sn > {csvfile_name}"
    result_collectl = subprocess.Popen(collectl_command,shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    time.sleep(1)
    return result_collectl

def build_nodes(ip,logfile, num_build_nodes, build_node_idx, influx_node_ip, influx_token, use_grafana,path, 
                transport_method, customize_string, use_infininband, use_collectl, logfile_collectl):
    ip_string, shm_string = calc_str(ip, num_build_nodes)
    if use_collectl == '1':
        result_collectl = start_collectl(use_infiniband, logfile_collectl)
    grafana_string = ''
    if use_grafana == '1':
        os.environ['CBM_INFLUX_TOKEN'] = influx_token
        grafana_string = '-m influx2:%s:8086:flesnet_status: ' % (influx_node_ip)
    flesnet_commands = (
        '%s./flesnet -t %s -L %s -l 1 -I %s -o %s -O %s %s %s > /dev/null 2>&1 &'
        % (path, transport_method, logfile, ip_string, build_node_idx, shm_string, 
           customize_string, grafana_string)
    )
    result_flesnet = subprocess.Popen(flesnet_commands, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    input_data = ''
    print(flesnet_commands)
    while input_data == '':
        input_data = sys.stdin.read().strip()
    if use_collectl == '1':
        result_collectl.terminate()
        result_collectl.wait()
    result_flesnet.terminate()
    result_flesnet.wait()

arg = docopt.docopt(__doc__, version='0.2')

ip = arg["<ip>"]
logfile = arg["<logfile>"]
num_build_nodes = arg["<num_build_nodes>"]
build_node_idx = arg["<build_node_idx>"]
influx_node_ip = arg["<influx_node_ip>"]
influx_token = arg["<influx_token>"]
use_grafana = arg["<use_grafana>"]
path = arg["<path>"]
transport_method = arg["<transport_method>"]
customize_string = arg["<customize_string>"]
use_infiniband = arg['<use_infiniband>']
use_collectl = arg['<use_collectl>']
logfile_collectl = arg['<logfile_collectl>']

build_nodes(ip,logfile, num_build_nodes, build_node_idx, influx_node_ip, influx_token, use_grafana,path, 
            transport_method, customize_string, use_infiniband, use_collectl, logfile_collectl)
