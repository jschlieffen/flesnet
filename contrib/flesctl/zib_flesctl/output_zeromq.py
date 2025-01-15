#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#Created on Wed Jan 15 16:03:07 2025

#@author: jschlieffen

"""
Usage: output_zeromq.py <ip> 

Arguments: 
    <ip> The ip address to use
"""

import subprocess
import time
import docopt

def build_nodes(ip):
    flesnet_commands = '../../../build/./flesnet -t zeromq -L logs/flesnet_zeromq_output_file.log -l 3 -I %s -o 0 -O shm:/fles_out/0 --timeslice-size 1 --processor-instances 0 -e "_" > /dev/null 2>&1 &' % (ip)
    result_flesnet = subprocess.Popen(flesnet_commands, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    print(result_flesnet)
    print(result_flesnet.poll())
    with open('logs/flesnet_output_file.log','r') as file:
        file.seek(0,2)
        while (True):
            line = file.readline()
            if line:
                print(line.strip())
            else:
                time.sleep(0.5)

print('test')
arg = docopt.docopt(__doc__, version='0.2')

ip = arg["<ip>"]
#print(ip)
#entry_nodes('../../../build/500GB.dmsa',ip)
build_nodes(ip)
print('iuefbuiweb')