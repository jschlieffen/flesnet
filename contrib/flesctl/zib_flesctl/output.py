#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#Created on Thu Jan  9 11:24:40 2025

#@author: jschlieffen
"""
Usage: output.py <logfile> <ip> <num_build_nodes> <build_node_idx>

Arguments: 
    <ip> The ip address to use
    <logfile> The Logfile to use
    <num_build_nodes> The number of build nodes
    <build_node_idx> The index of the current build node
"""


import subprocess
import time
import docopt
import sys

def calc_str(ip,num_build_nodes):
    ip_string = ""
    parts = ip.split('sep')
    for part in parts:
        if part != "":
            ip_string += "tcp://" + part + '/0'
    shm_string = ""
    for i in range(0,num_build_nodes):
        shm_string += "shm:/fles_out_b%s" % (str(i))
    return ip_string, shm_string

def build_nodes(ip,logfile, num_build_nodes, build_node_idx):
    #print(ip)
    #ip_string = "shm://" + ip.replace("sep", "/0 shm://") + "/0"
    #ip_string = ""
    #print(ip_string)
    print(ip)
    #i = 0
    #parts = ip.split('sep')
    #for part in parts:
        #if part != "":
            #ip_string += "tcp://" + part + '/0'
    ip_string, shm_string = calc_str(ip, num_build_nodes)
    print(ip_string)
    flesnet_commands = '../../../build/./flesnet -t rdma -L %s -l 2 -I %s -o %s -O %s --timeslice-size 1 --processor-instances 0 -e "_" > /dev/null 2>&1 &' % (logfile,ip_string, build_node_idx, shm_string)
    result_flesnet = subprocess.Popen(flesnet_commands, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    print(result_flesnet)
    print(result_flesnet.poll())
    '''
    with open('logs/flesnet_output_file.log','r') as file:
        file.seek(0,2)
        while (True):
            line = file.readline()
            if line:
                print(line.strip())
            else:
                time.sleep(0.5)
    '''
    input_data = ''
    while input_data == '':
        input_data = sys.stdin.read().strip()
    #result_mstool.terminate()
    result_flesnet.terminate()
    #result_mstool.wait()
    result_flesnet.wait()

print('test')
arg = docopt.docopt(__doc__, version='0.2')

ip = arg["<ip>"]
logfile = arg["<logfile>"]
num_build_nodes = arg["<num_build_nodes>"]
build_node_idx = arg["<build_node_idx>"]
#print(ip)
#entry_nodes('../../../build/500GB.dmsa',ip)
build_nodes(ip,logfile, num_build_nodes, build_node_idx)
print('iuefbuiweb')