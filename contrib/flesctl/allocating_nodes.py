#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#Created on Thu Dec 19 15:04:17 2024

#@author: jschlieffen


"""Usage:
    allocating_nodes.py <allocating_nodes>
    allocating_nodes.py (-h | --help)

Options:
    -h --help  Show this message.
"""


import subprocess
import sys
import os
import time
import docopt
import re

class slurm_commands:
    
    def __init__(self):
        None
        
    def alloc_nodes(self,node_numbers):
        #command = ['srun', 
        #           '--nodelist=%s'%(node_list),
        #           '--time-min=00:15:00',
        #           '--time=00:30:00',
        #           'ip a']
        #command = ['salloc',
        #           '--nodes=%s'%(node_numbers),
        #           '--time=00:05:00',
        #           '--ntasks=1',
        #           '&']
        command = 'salloc --nodes=%s --time=00:20:00'%(node_numbers)
        allocation = subprocess.run(command,shell=True)
        print(allocation.returncode)
        return allocation.returncode
    
    #Todo: try-except for all slurm-commands
    def pids(self,node_id):
        command = 'ps aux | grep %s' % (node_id) 
        try:
            #result = subprocess.Popen(command, capture_output=True, text=True, check=True, shell=True)
            #result = subprocess.run(command, capture_output=True, text=True, check=True, shell=True)
            result = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout,stderr = result.communicate()
            return stdout
        except subprocess.CalledProcessError as e:
            print('Error')
            sys.exit(1)
        return 
    
    def kill_process(self,pid):
        return None
    
    def ethernet_ip(self,node_id):
        command = 'srun --nodelist=%s ip a' % (node_id)
        result = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout,stderr = result.communicate()
        match = re.search(r'eth0:(.*?)7: net0912@eth0:',stdout,re.DOTALL)
        content = match.group(1)
        match2 = re.search(r'inet (.*?)/23',content,re.DOTALL)
        #print(repr(content))
        content2 = match2.group(1)
        #print(repr(content2))
        #print(type(content))
        #print(result.stdout)
        return content2
    
    def infiniband_ip(self,node_id):
        command = 'srun --nodelist=%s ip a' % (node_id)
        print('test_inf_id')
        result = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print('test_inf_id2')
        stdout,stderr = result.communicate()
        print('test_inf_id3')
        match = re.search(r'ib0:(.*?)7: net0912@eth0:',stdout,re.DOTALL)
        content = match.group(1)
        match2 = re.search(r'inet (.*?)/23',content,re.DOTALL)
        #print(repr(content))
        content2 = match2.group(1)
        #print(repr(content2))
        #print(type(content))
        #print(result.stdout)
        return content2
    
    def start_customize_program(self,program_name,node_id):
        command = 'srun --nodelist=%s %s &> /dev/null &' %(node_id,program_name)
        #result = subprocess.run(command,capture_output=True, text=True, check=True, shell=True)
        result = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        #try:
            #print('test')
            #result = subprocess.Popen(command, capture_output=True, text=True, check=True, shell=True)
            #return result.stdout
        #except subprocess.CalledProcessError as e:
            #print('Error')
            #sys.exit(1)
        print('test1')
        #print(result.stdout)
        print('test2')
        #print(result.stderr)
        print(result)
        #stdout, stderr = result.communicate()
        print('test3')
        #print(stderr)
        print(result.poll())
        return None

class Entry_nodes(slurm_commands):
    
    def __init__(self,number_nodes,use_infini_band):
        super().__init__()
        self.node_list = []
    
    def start_mstool(self):
        return None
    
    def start_flesnet(self):
        return None
    
class Build_nodes(slurm_commands):
    
    def __init__(self,number_nodes,use_infini_band):
        super().__init__()
        self.node_lits
        
    def start_flesnet(self):
        return None
     
    
def main():
    arg = docopt.docopt(__doc__, version='0.2')
    
    allocating_nodes = arg["<allocating_nodes>"]
    
    s = slurm_commands()
    print(type(allocating_nodes))
    #s.alloc_nodes('htc-cmp507')
    #print('test3')
    if allocating_nodes == '1':
        s.alloc_nodes(1)
    else:
        node = os.environ.get('SLURM_NODELIST')
        #print(node)
        if node is None:
            print("Error: SLURM_NODELIST is not set. Did you run this within a SLURM job allocation?")
        else:
            print(f"Allocated node: {node}")
        print('test1')
        print(s.pids(node))
        print('test2')
        inf_id = s.infiniband_ip(node)
        print(inf_id)
        eth_id = s.ethernet_ip(node)
        print(eth_id)
        program_string = '../../build/./mstool -i ../../build/500GB.dmsa -O fles_in -D 1'
        s.start_customize_program(program_string, node)
        print(s.pids(node))
    #print('test5')

    
if __name__ == '__main__':
    main()
        
    
    