#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#Created on Wed Jan  8 16:54:02 2025

#@author: jschlieffen

"""
Usage: input.py <input_file> <logfile_entry_node> <logfile_build_node> <build_nodes_ip> <entry_nodes_ip> <num_entry_nodes> <num_build_nodes> <entry_node_idx> <build_node_idx> <influx_node_ip> <influx_token> <use_grafana> <path> <transport_method> <customize_string> <use_pattern_gen> <use_dmsa_files>  <use_infiniband> <use_collectl> <logfile_collectl>

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
    <path> The path to flesnet/mstool
    <transport_method> The transport method (rdma/zeromq, libfabric currently not implemented)
    <customize_string> The remaining params for flesnet
    <use_pattern_gen> enables/disables usage of the pattern generator
    <use_dmsa_files> Decides if the input files are dmsa files
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
# This file starts mstool and flesnet on a super node. It is started with 
#   srun nodelist=node super.py -N 1 <params>  
# After flesnet is started the program waits for a signal from the 
# central manager. If it receives a signal it will shut down flesnet and the 
# mstool. 
# NOTE: If the program does not terminate correctly, it completly suffices 
#       to just kill the srun process. One does not have to kill mstool and 
#       flesnet manually
# =============================================================================

def start_collectl(use_infiniband, csvfile_name):
    if use_infiniband == '1':
        collectl_command = f"sudo collectl --plot --sep , -i 1 -sx > {csvfile_name}"
    else:
        collectl_command = f"collectl --plot --sep , -i 1 -sn > {csvfile_name}"
    result_collectl = subprocess.Popen(collectl_command,shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    time.sleep(1)
    return result_collectl

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


def entry_nodes(dmsa_file,build_nodes_ip,entry_nodes_ip,logfile_entry_node, logfile_build_nodes, num_entry_nodes, num_build_nodes, entry_node_idx, build_node_idx,
                influx_node_ip, influx_token, use_grafana ,path, transport_method, customize_string, use_pattern_gen, use_dmsa_files,use_infininband, use_collectl, logfile_collectl):

    ip_string, shm_string = calc_str(build_nodes_ip, num_entry_nodes, use_pattern_gen)
    if use_collectl == '1':
        result_collectl = start_collectl(use_infiniband, logfile_collectl)
    grafana_string = ''
    if use_grafana:
        os.environ['CBM_INFLUX_TOKEN'] = influx_token
        grafana_string = '-m influx2:%s:8086:flesnet_status:' % (influx_node_ip) 
    D_flag = ""
    if use_dmsa_files == '1':
        D_flag = "-D 1"
    if use_pattern_gen == '0':
        mstool_commands = '%s./mstool -L test.log -i %s -O fles_in_e%s %s > /dev/null 2>&1 &' % (path,dmsa_file, str(entry_node_idx), D_flag)
        result_mstool = subprocess.Popen(mstool_commands, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        time.sleep(1)
    flesnet_commands = (
        '%s./flesnet -t %s -L %s -l 1 -i %s -I %s -O %s %s %s > /dev/null 2>&1 &'
        % (path, transport_method, logfile_entry_node,str(entry_node_idx), shm_string,
           ip_string, customize_string, grafana_string)
    )
    result_flesnet = subprocess.Popen(flesnet_commands, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    build_nodes(entry_nodes_ip,logfile_build_nodes, num_build_nodes, build_node_idx, influx_node_ip, influx_token, use_grafana,path, 
                    transport_method, customize_string)

    if use_collectl == '1':
        result_collectl.terminate()
        result_collectl.wait()
    if use_pattern_gen == '0':
        result_mstool.terminate()
        result_mstool.wait()
    result_flesnet.terminate()
    result_flesnet.wait()

def calc_str_output(ip,num_build_nodes):
    ip_string = ""
    parts = ip.split('sep')
    for part in parts:
        if part != "":
            ip_string += "tcp://" + part + '/0 '
    shm_string = ""
    for i in range(0,int(num_build_nodes)):
        shm_string += "shm:/fles_out_b%s/0 " % (str(i))
    return ip_string, shm_string




def build_nodes(entry_nodes_ip,logfile_build_nodes, num_build_nodes, build_node_idx, influx_node_ip, influx_token, use_grafana, path, 
                transport_method, customize_string):
    ip_string, shm_string = calc_str_output(entry_nodes_ip, num_build_nodes)
    os.environ['CBM_INFLUX_TOKEN'] = influx_token
    grafana_string = ''
    if use_grafana:
        grafana_string = '-m influx2:%s:8086:flesnet_status: ' % (influx_node_ip)
    flesnet_commands = (
        '%s./flesnet -t %s -L %s -l 1 -I %s -o %s -O %s %s %s > /dev/null 2>&1 &' 
        % (path, transport_method,logfile_build_nodes,ip_string, build_node_idx,
           shm_string, customize_string, grafana_string)
    )
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
path = arg["<path>"]
transport_method = arg["<transport_method>"]
customize_string = arg["<customize_string>"]
use_pattern_gen = arg["<use_pattern_gen>"]
use_dmsa_files = arg["<use_dmsa_files>"]
use_infiniband = arg['<use_infiniband>']
use_collectl = arg['<use_collectl>']
logfile_collectl = arg['<logfile_collectl>']

entry_nodes(input_file,build_nodes_ip, entry_nodes_ip, logfile_entry_node, logfile_build_node, num_entry_nodes, num_build_nodes, entry_node_idx, build_node_idx,
            influx_node_ip, influx_token, use_grafana,path,transport_method, customize_string, use_pattern_gen, use_dmsa_files, use_infiniband, use_collectl,
            logfile_collectl)