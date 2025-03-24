#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#Created on Thu Jan  9 11:24:40 2025

#@author: jschlieffen
"""
Usage: output.py <logfile> <ip> <num_build_nodes> <build_node_idx> <influx_node_ip> <influx_token> <use_grafana>

Arguments: 
    <ip> The ip address to use
    <logfile> The Logfile to use
    <num_build_nodes> The number of build nodes
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

def build_nodes(ip,logfile, num_build_nodes, build_node_idx, influx_node_ip, influx_token, use_grafana):
    ip_string, shm_string = calc_str(ip, num_build_nodes)
    os.environ['CBM_INFLUX_TOKEN'] = influx_token
    grafana_string = ''
    if use_grafana:
        grafana_string = '-m influx2:%s:8086:flesnet_status: ' % (influx_node_ip)
    flesnet_commands = '../../../build/./flesnet -t rdma -L %s -l 2 -I %s -o %s -O %s --timeslice-size 1 --processor-instances 0 -e "_" %s > /dev/null 2>&1 &' % (logfile,ip_string, build_node_idx, shm_string, grafana_string)
    result_flesnet = subprocess.Popen(flesnet_commands, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    input_data = ''
    while input_data == '':
        input_data = sys.stdin.read().strip()
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
build_nodes(ip,logfile, num_build_nodes, build_node_idx, influx_node_ip, influx_token, use_grafana)
