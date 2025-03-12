#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#Created on Wed Jan  8 16:54:02 2025

#@author: jschlieffen

"""
Usage: input.py <logfile> <ip> 

Arguments: 
    <ip> The ip address to use
    <logfile> The Logfile to use
"""
import subprocess
import time
import docopt
import sys



# =============================================================================
# TODO: Get better variable names for the commands
# TODO: make the log file name depend on the node_id
# =============================================================================
def entry_nodes(dmsa_file,ip,logfile):
    #ip_string = "shm://" + ip.replace("sep", "/0 shm://") + "/0"
    #print(ip_string)
    ip_string = ""
    print(ip)
    i = 0
    parts = ip.split('sep')
    for part in parts:
        if part != "":
            ip_string += "shm://" + part + '/%s ' % (i)
            i += 1
    print(ip_string)
    mstool_commands = '../../../build/./mstool -L logs/mstool_input_file.log -i %s -O fles_in -D 1 > /dev/null 2>&1 &' % (dmsa_file)
    flesnet_commands = '../../../build/./flesnet -t rdma -L %s -l 2 -i 0 -I shm:/fles_in/0 -O %s --timeslice-size 1 --processor-instances 0 -e "_" > /dev/null 2>&1 &' % (logfile,ip_string)
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

ip = arg["<ip>"]
logfile = arg["<logfile>"]
#print(ip)
entry_nodes('../../../build/500GB.dmsa',ip, logfile)
#print('iuefbuiweb')
'''
input_data = ''
while input_data == '': 
    input_data = sys.stdin.read().strip()
with open('test.txt', 'w') as f:
    f.write(input_data)
'''


    