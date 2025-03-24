#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#Created on Wed Jan  8 16:54:02 2025

#@author: jschlieffen

"""
Usage: input.py <input_file> <logfile> <ip> <num_entry_nodes> <entry_node_idx> <influx_node_ip> <influx_token> <use_grafana>

Arguments: 
    <input_file> The input dmsa file for the mstool
    <ip> The ip address to use
    <logfile> The Logfile to use
    <num_entry_nodes> The number of entry nodes
    <entry_node_idx> The index of the current entry node
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
def entry_nodes(dmsa_file,ip,logfile, num_entry_nodes, entry_node_idx, influx_node_ip, influx_token, use_grafana):
    os.environ['CBM_INFLUX_TOKEN'] = influx_token
    ip_string, shm_string = calc_str(ip, num_entry_nodes)
    grafana_string = ''
    if use_grafana:
        grafana_string = '-m influx2:%s:8086:flesnet_status:' % (influx_node_ip) 
    mstool_commands = '../../../build/./mstool -i %s -O fles_in_e%s -D 1 > /dev/null 2>&1 &' % (dmsa_file, str(entry_node_idx))
    flesnet_commands = '../../../build/./flesnet -t rdma -L %s -l 2 -i %s -I %s -O %s --timeslice-size 1 --processor-instances 0 -e "_" %s > /dev/null 2>&1 &' % (logfile,str(entry_node_idx), shm_string,ip_string, grafana_string)
    result_mstool = subprocess.Popen(mstool_commands, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    time.sleep(1)
    result_flesnet = subprocess.Popen(flesnet_commands, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    input_data = ''
    while input_data == '':
        input_data = sys.stdin.read().strip()
    result_mstool.terminate()
    result_flesnet.terminate()
    result_mstool.wait()
    result_flesnet.wait()
    


arg = docopt.docopt(__doc__, version='0.2')
input_file = arg["<input_file>"]
ip = arg["<ip>"]
logfile = arg["<logfile>"]
num_entry_nodes = arg["<num_entry_nodes>"]
entry_node_idx = arg["<entry_node_idx>"]
influx_node_ip = arg["<influx_node_ip>"]
influx_token = arg["<influx_token>"]
use_grafana = arg["<use_grafana>"]
entry_nodes(input_file,ip, logfile,num_entry_nodes, entry_node_idx, influx_node_ip, influx_token, use_grafana)



    