#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#Created on Wed Jan  8 16:54:02 2025

#@author: jschlieffen

"""
Usage: input.py <input_file> <logfile> <ip> <num_entry_nodes> <entry_node_idx>

Arguments: 
    <input_file> The input dmsa file for the mstool
    <ip> The ip address to use
    <logfile> The Logfile to use
    <num_entry_nodes> The number of entry nodes
    <entry_node_idx> The index of the current entry node
"""
import subprocess
import time
import docopt
import sys

def calc_str(ip,num_entry_nodes):
    ip_string = ""
    parts = ip.split('sep')
    for part in parts:
        if part != "":
            ip_string += "tcp://" + part + '/0 '
    shm_string = ""
    for i in range(0,int(num_entry_nodes)):
        shm_string += "shm:/fles_in_e%s/0 " % (str(i))
    print(shm_string)
    print(ip_string)
    return ip_string, shm_string


# =============================================================================
# TODO: Get better variable names for the commands done
# TODO: make the log file name depend on the node_id done
# =============================================================================
def entry_nodes(dmsa_file,ip,logfile, num_entry_nodes, entry_node_idx):
    #ip_string = "shm://" + ip.replace("sep", "/0 shm://") + "/0"
    #print(ip_string)
    #ip_string = ""
    #print(ip)
    #i = 0
    #parts = ip.split('sep')
    #for part in parts:
    #    if part != "":
    #        ip_string += "shm://" + part + '/%s ' % (i)
    #        i += 1
    #print(ip_string)
    print(dmsa_file)
    ip_string, shm_string = calc_str(ip, num_entry_nodes)
    mstool_commands = '../../../build/./mstool -L logs/mstool_input_file.log -i %s -O fles_in_e%s -D 1 > /dev/null 2>&1 &' % (dmsa_file, str(entry_node_idx))
    flesnet_commands = '../../../build/./flesnet -t rdma -L %s -l 2 -i %s -I %s -O %s --timeslice-size 1 --processor-instances 0 -e "_" > /dev/null 2>&1 &' % (logfile,str(entry_node_idx), shm_string,ip_string)
    #flesnet_commands = '../../../build/./flesnet -t rdma -L logs/flesnet_input_file.log -i 0 -I shm:/fles_in/0 -o 0 -O shm:/fles_out/0 --timeslice-size 1 --processor-instances 0 -e "_" > /dev/null 2>&1 &' 
    result_mstool = subprocess.Popen(mstool_commands, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    time.sleep(1)
    result_flesnet = subprocess.Popen(flesnet_commands, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    #for stdout_line in iter(result_flesnet.stdout.readline, ''):
        #print(stdout_line, end='')
        #print('test')
    '''
    print('result:')
    print(result_mstool)
    print(result_flesnet)
    print('result.poll:')
    print(result_mstool.poll())
    print(result_flesnet.poll())
    time.sleep(1)
    with open('logs/mstool_input_file.log', 'r') as file:
        print(file.read())
    with open('logs/flesnet_input_file.log','r') as file:
        print(file.read())
        file.seek(0,2)
        while(True):
            line = file.readline()
            if line:
                print(line.strip())
            else:
                time.sleep(0.5)
    '''
    input_data = ''
    while input_data == '':
        input_data = sys.stdin.read().strip()
    result_mstool.terminate()
    result_flesnet.terminate()
    result_mstool.wait()
    result_flesnet.wait()
    

#print('iuwefbbwe')
print('test123')
arg = docopt.docopt(__doc__, version='0.2')
input_file = arg["<input_file>"]
ip = arg["<ip>"]
logfile = arg["<logfile>"]
num_entry_nodes = arg["<num_entry_nodes>"]
entry_node_idx = arg["<entry_node_idx>"]
#print(ip)
#entry_nodes('../../../build/500GB.dmsa',ip, logfile,num_entry_nodes, entry_node_idx)
entry_nodes(input_file,ip, logfile,num_entry_nodes, entry_node_idx)
#print('iuefbuiweb')
'''
input_data = ''
while input_data == '': 
    input_data = sys.stdin.read().strip()
with open('test.txt', 'w') as f:
    f.write(input_data)
'''


    