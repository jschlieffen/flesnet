#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#Created on Wed Jan  8 16:54:02 2025

#@author: jschlieffen

"""
Usage: input.py <input_file> <logfile> <ip> <num_entry_nodes> <entry_node_idx> <influx_node_ip> <influx_token> <use_grafana> <path> <transport_method> <customize_string> <use_pattern_gen> <use_dmsa_files>

Arguments: 
    <input_file> The input dmsa file for the mstool
    <ip> The ip address to use
    <logfile> The Logfile to use
    <num_entry_nodes> The number of entry nodes
    <entry_node_idx> The index of the current entry node
    <influx_node_ip> The ip of the where the influx container is runnning
    <influx_token> The token to the influx-db
    <use_grafana> enables/disables grafana
    <path> The path to flesnet/mstool
    <transport_method> The transport method (rdma/zeromq, libfabric currently not implemented)
    <customize_string> The remaining params for flesnet
    <use_pattern_gen> enables/disables usage of the pattern generator
    <use_dmsa_files> Decides if the input files are dmsa files
"""

import subprocess
import time
import docopt
import sys
import os

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

def calc_str(ip,num_entry_nodes, use_pattern_gen):
    ip_string = ""
    parts = ip.split('sep')
    for part in parts:
        if part != "":
            ip_string += "tcp://" + part + '/0 '
    shm_string = ""
    if use_pattern_gen == '1':
        for i in range(0,int(num_entry_nodes)):
            shm_string += "pgen:/fles_in_e%s/0 " % (str(i))
    else: 
        for i in range(0,int(num_entry_nodes)):
            shm_string += "shm:/fles_in_e%s/0 " % (str(i))
    return ip_string, shm_string


def entry_nodes(dmsa_file,ip,logfile, num_entry_nodes, entry_node_idx, influx_node_ip, influx_token, use_grafana,path, 
                transport_method, customize_string, use_pattern_gen, use_dmsa_files):
    ip_string, shm_string = calc_str(ip, num_entry_nodes, use_pattern_gen)
    grafana_string = ''
    if use_grafana:
        os.environ['CBM_INFLUX_TOKEN'] = influx_token
        grafana_string = '-m influx2:%s:8086:flesnet_status:' % (influx_node_ip) 
    D_flag = ""
    if use_dmsa_files == '1':
        D_flag = "-D 1"
    if use_pattern_gen == '0':
        mstool_commands = '%s./mstool -i %s -O fles_in_e%s %s > /dev/null 2>&1 &' % (path,dmsa_file, str(entry_node_idx), D_flag)
        result_mstool = subprocess.Popen(mstool_commands, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        time.sleep(1)
    flesnet_commands = (
        '%s./flesnet -t %s -L %s -l 1 -i %s -I %s -O %s %s %s > /dev/null 2>&1 &' 
        % (path,transport_method,logfile,str(entry_node_idx), shm_string,ip_string,
          customize_string, grafana_string)
    )
    result_flesnet = subprocess.Popen(flesnet_commands, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    input_data = ''
    while input_data == '':
        input_data = sys.stdin.read().strip()
    if use_pattern_gen == '0':
        result_mstool.terminate()
        result_mstool.wait()
    result_flesnet.terminate()
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
path = arg["<path>"]
transport_method = arg["<transport_method>"]
customize_string = arg["<customize_string>"]
use_pattern_gen = arg["<use_pattern_gen>"]
use_dmsa_files = arg["<use_dmsa_files>"]
entry_nodes(input_file,ip, logfile,num_entry_nodes, entry_node_idx, influx_node_ip, influx_token, use_grafana,path, 
            transport_method, customize_string, use_pattern_gen, use_dmsa_files)



    