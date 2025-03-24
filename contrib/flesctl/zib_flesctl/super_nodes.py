#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#Created on Wed Jan  8 16:54:02 2025

#@author: jschlieffen

"""
Usage: input.py <input_file> <logfile_entry_node> <logfile_build_node> <build_nodes_ip> <entry_nodes_ip> <num_entry_nodes> <num_build_nodes> <entry_node_idx> <build_node_idx> <influx_node_ip> <influx_token> <use_grafana>

Arguments: 
    <input_file> The input dmsa file for the mstool
    <build_nodes_ip> The ips of the build nodes
    <entry_nodes_ip> The ips of the entry nodes
    <logfile_entry_node> The Logfile of the entry node of this node
    <logfile_build_node> The logfile of the build node of this node
    <num_entry_nodes> The number of entry nodes
    <num_build_nodes> The number of the build nodes
    <entry_node_idx> The index of the current entry node
    <build_node_idx> The index of the current build node
    <influx_node_ip> The ip of the where the influx container is runnning
    <influx_token> The token to the influx-db
    <use_grafana> enables/disables grafana
"""

import subprocess
import time
import docopt
import sys
import os

def calc_str(ip,num_entry_nodes):
    ip_string = ""
    parts = ip.split('sep')
    for part in parts:
        if part != "":
            ip_string += "tcp://" + part + '/0 '
    shm_string = ""
    for i in range(0,int(num_entry_nodes)):
        shm_string += "shm:/fles_in_e%s/0 " % (str(i))
    return ip_string, shm_string


# =============================================================================
# TODO: Get better variable names for the commands done
# TODO: make the log file name depend on the node_id done
# =============================================================================
def entry_nodes(dmsa_file,build_nodes_ip,entry_nodes_ip,logfile_entry_node, logfile_build_nodes, num_entry_nodes, num_build_nodes, entry_node_idx, build_node_idx,
                influx_node_ip, influx_token, use_grafana):
    os.environ['CBM_INFLUX_TOKEN'] = influx_token
    ip_string, shm_string = calc_str(build_nodes_ip, num_entry_nodes)
    grafana_string = ''
    print(shm_string)
    if use_grafana:
        grafana_string = '-m influx2:%s:8086:flesnet_status:' % (influx_node_ip) 
    mstool_commands = '../../../build/./mstool -i %s -O fles_in_e%s -D 1 > /dev/null 2>&1 &' % (dmsa_file, str(entry_node_idx))
    flesnet_commands = '../../../build/./flesnet -t rdma -L %s -l 2 -i %s -I %s -O %s --timeslice-size 1 --processor-instances 0 -e "_" %s > /dev/null 2>&1 &' % (
        logfile_entry_node,str(entry_node_idx), shm_string,ip_string, grafana_string)
    result_mstool = subprocess.Popen(mstool_commands, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    time.sleep(1)
    result_flesnet = subprocess.Popen(flesnet_commands, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    build_nodes(entry_nodes_ip,logfile_build_nodes, num_build_nodes, build_node_idx, influx_node_ip, influx_token, use_grafana)
    result_mstool.terminate()
    result_flesnet.terminate()
    result_mstool.wait()
    result_flesnet.wait()
    print('test')

def build_nodes(entry_nodes_ip,logfile_build_nodes, num_build_nodes, build_node_idx, influx_node_ip, influx_token, use_grafana):
    ip_string, shm_string = calc_str(entry_nodes_ip, num_build_nodes)
    os.environ['CBM_INFLUX_TOKEN'] = influx_token
    grafana_string = ''
    if use_grafana:
        grafana_string = '-m influx2:%s:8086:flesnet_status: ' % (influx_node_ip)
    flesnet_commands = '../../../build/./flesnet -t rdma -L %s -l 2 -I %s -o %s -O %s --timeslice-size 1 --processor-instances 0 -e "_" %s > /dev/null 2>&1 &' % (
        logfile_build_nodes,ip_string, build_node_idx, shm_string, grafana_string)
    result_flesnet = subprocess.Popen(flesnet_commands, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    input_data = ''
    while input_data == '':
        input_data = sys.stdin.read().strip()
    result_flesnet.terminate()
    result_flesnet.wait()

arg = docopt.docopt(__doc__, version='0.2')
input_file = arg["<input_file>"]
build_nodes_ip = arg["<build_nodes_ip>"]
entry_nodes_ip = arg["<entry_nodes_ip>"]
logfile_entry_node = arg["<logfile_entry_node>"]
logfile_build_node = arg["<logfile_build_node>"]
num_entry_nodes = arg["<num_entry_nodes>"]
num_build_nodes = arg["<num_build_nodes>"]
entry_node_idx = arg["<entry_node_idx>"]
build_node_idx = arg["<build_node_idx>"]
influx_node_ip = arg["<influx_node_ip>"]
influx_token = arg["<influx_token>"]
use_grafana = arg["<use_grafana>"]
print('test')
entry_nodes(input_file,build_nodes_ip, entry_nodes_ip, logfile_entry_node, logfile_build_node, num_entry_nodes, num_build_nodes, entry_node_idx, build_node_idx,
            influx_node_ip, influx_token, use_grafana)