#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 19 15:04:17 2024

@author: jschlieffen
"""

import subprocess
import sys

class slurm_commands:
    
    def __init__(self):
        None
        
    def alloc_nodes(self,node_list):
        command = ['srun', 
                   '--nodelist=%s'%(node_list),
                   '--time-min=00:15:00',
                   '--time=00:30:00',
                   '--pty-bash']
        exit_code = subprocess.call(command)
        return exit_code
    
    #Todo: try-except for all slurm-commands
    def pids(self,process_id):
        command = ['ip a']
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True, shell=True)
            return result.stdout
        except subprocess.CallesProcessError as e:
            print('Error')
            sys.exit(1)
        return 
    
    def kill_process(self,pid):
        return None
    
    def ethernet_ip(self,node_id):
        return None
    
    def infiniband_ip(self,node_id):
        return None
    
    def start_customize_program(self,program_name,node_id):
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
    s = slurm_commands()
    s.alloc_nodes('htc-cmp501')

if __name__ == '__main__':
    main()
        
    
    