#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr  7 15:36:20 2025

@author: jschlieffen
"""

from datetime import datetime
import configparser
import os

# =============================================================================
# This file creates the flesctrl logfile that can be found in 
# logs/general/
# =============================================================================

class Logfile:
    def __init__(self):
        self.num_nodes = 0
        self.Par_ = None
        self.entry_nodes_list = {}
        self.build_nodes_list = {}
        self.overlap_nodes_list = {}
        self.sender_node_list = {}
        self.receiving_node_list = {}
        self.input_node_list = {}
        self.cm_list = {}
        self.output_node_list = {}
        self.avg_data_rate = 0
        self.exec_time = 0
        self.transport_method = ''
        self.use_flesnet = 0
        self.infiniband_used = False
        
    def write(self):
        '''
        config = configparser.ConfigParser()
        config.read('setup/config.cfg')
        run_id = config.getint('general', 'run_id')
        config['general']['run_id'] = str(run_id+1)
        with open('setup/config.cfg', 'w') as configfile:
            config.write(configfile, space_around_delimiters=False)
        '''
        
        with open("tmp/run_id.txt", "r") as f:
            run_id = int(f.read().strip())
        run_id += 1
        with open("tmp/run_id.txt", "w") as f:
            f.write(str(run_id))
        timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        logfile_name = f'logs/general/Run_{str(run_id+1)}_{timestamp}.log'
        dir = os.path.dirname(__file__)
        path = os.path.join(dir,'../tmp')
        if not os.path.exists(path):
            os.makedirs(path)
        #os.environ['flesctl_logfile_name'] = logfile_name
        tmp_file_name = f"{path}/file_name.txt"
        with open(tmp_file_name, "w") as f:
            f.write(logfile_name)
        with open(logfile_name, 'w') as file:
            file.write(f'The total number of nodes allocated: {self.num_nodes} \n')
            if self.overlap_nodes_list:
                file.write('Super nodes: \n')
                for key, val in self.overlap_nodes_list.items():
                    entry_node_idx = val['entry_node_idx']
                    build_node_idx = val['build_node_idx']
                    file.write(f'   {key} with entry node index {entry_node_idx} and build node index {build_node_idx} \n')
            if self.entry_nodes_list:
                file.write('Entry nodes: \n')
                for key,val in self.entry_nodes_list.items():
                    idx = val['entry_node_idx']
                    file.write(f'    {key} as index {idx}\n')
            if self.build_nodes_list:
                file.write('Build nodes: \n')
                for key,val in self.build_nodes_list.items():
                    idx = val['build_node_idx']
                    file.write(f'   {key} as index {idx} \n')
            if self.sender_node_list:
                file.write('Sender nodes: \n')
                for key,val in self.sender_nodes_list.items():
                    idx = val['sender_node_idx']
                    file.write(f'   {key} as index {idx} \n')
            if self.receiving_node_list:
                file.write('receiving nodes: \n')
                for key,val in self.receiving_node_list.items():
                    #idx = val['receiving_node_idx']
                    sender = val['sender_node']
                    file.write(f'   {sender} was connected to {key} \n')
            if self.input_node_list:
                file.write('Input nodes: \n')
                for key,val in self.input_node_list.items():
                    if self.use_flesnet:
                        idx = val['build_node_idx']
                    else:
                        idx = val['input_node_idx']
                    file.write(f'   {key} as index {idx} \n')
            if self.cm_list:
                file.write('central_manager: \n')
                for key,val in self.cm_list.items():
                    idx = val['cm_idx']
                    file.write(f'   {key} as index {idx} \n')
            if self.output_node_list:
                file.write('Output nodes: \n')
                for key,val in self.output_node_list.items():
                    idx = val['output_node_idx']
                    file.write(f'   {key} as index {idx} \n')

            file.write(f'The average data rate of this run was: {self.avg_data_rate}\n')
            file.write(f'The execution time of this run was: {self.exec_time}\n')
            file.write(f'The used transport method was: {self.transport_method}\n')
            if self.infiniband_used:
                file.write('Infiniband was used \n')
            else: 
                file.write('Ethernet was used \n')

logfile = Logfile()