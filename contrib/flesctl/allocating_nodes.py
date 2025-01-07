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
    
    # =============================================================================
    #  TODO:
    #       1. take care that the message may change
    # =============================================================================
    def ethernet_ip(self,node_id):
        command = 'srun --nodelist=%s ip a' % (node_id)
        result = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout,stderr = result.communicate()
        match = re.search(r'eth0:(.*?)scope global eth0',stdout,re.DOTALL)
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
        #print('test_inf_id')
        result = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        #print('test_inf_id2')
        stdout,stderr = result.communicate()
        #print('test_inf_id3')
        #print(stdout)
        match = re.search(r'ib0:(.*?)scope global ib0',stdout,re.DOTALL)
        #print(match)
        content = match.group(1)
        match2 = re.search(r'inet (.*?)/23',content,re.DOTALL)
        #print(repr(content))
        content2 = match2.group(1)
        #print(repr(content2))
        #print(type(content))
        #print(result.stdout)
        return content2
        
    # =============================================================================
    #  TODOs:
    #   1. get the log message.
    #   2. make this a parallel process.
    # =============================================================================
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
        #log_variable = ""
        #print(result.stdout)
        print('test2')
        #print(result.stderr)
        print(result)
        #stdout, stderr = result.communicate()
        print('test3')
        #print(stderr)
        print(result.poll())
        return None
    
    #Funktioniert nicht wie es soll.
    def exit_node(self,node_id):
        command = 'exit'
        subprocess.run(command, shell=True)
        

class Entry_nodes(slurm_commands):
    
    def __init__(self,number_nodes,use_infini_band):
        super().__init__()
        self.node_list = []
    
    #TODO: remove node id from the functioninput
    def start_mstool(self,node_id):
        program_string = '../../build/./mstool -i ../../build/500GB.dmsa -O fles_in -D 1 -L mstool.log'
        self.start_customize_program(program_string, node_id)
    
    def start_flesnet(self,node_id):
        program_string = '../../build/./flesnet -L flesnet.log -t zeromq -i 0 -I shm:/fles_in/0 -o 0 -O shm:/fles_out/0 --timeslice-size 1 --processor-instances 0 -e "_"'
        self.start_customize_program(program_string, node_id)
        #time.sleep(1)
        with open('flesnet.log', 'r') as file:
            print(file.read())
            file.seek(0,2)
            while(True):
                line = file.readline()
                if line:
                    print(line.strip())
                else:
                    #print('test')
                    time.sleep(0.1)
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
        #s.exit_node('jsdfbjkwebf')
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
        program_string = '../../build/./mstool -i ../../build/500GB.dmsa -O fles_in -D 1 -L test.log'
        #s.start_customize_program(program_string, node)
        print(s.pids(node))
        e = Entry_nodes(1, 1)
        e.start_mstool(node)
        e.start_flesnet(node)
       # s.exit_node('jkfeb')
    #print('test5')

    
if __name__ == '__main__':
    main()
        
    
    