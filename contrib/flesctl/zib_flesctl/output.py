#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#Created on Thu Jan  9 11:24:40 2025

#@author: jschlieffen
"""
Usage: output.py <ip> 

Arguments: 
    <ip> The ip address to use
"""


import subprocess
import time

def build_notes(ip):
    flesnet_commands = '../../../build/./flesnet -t rdma -L flesnet_output_file.log -I shm://%s/0 -o 0 -O shm:/fles_out/0 --timeslice-size 1 --processor-instances 0 -e "_" > /dev/null 2>&1 &' % (ip)
    result_flesnet = subprocess.Popen(flesnet_commands, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    print(result_flesnet)
    print(result_flesnet.poll())
    with open('flesnet_output_file.log','r') as file:
        file.seek(0,2)
        while (True):
            line = file.readline()
            if line:
                print(line.strip())
            else:
                time.sleep(0.5)

build_notes()