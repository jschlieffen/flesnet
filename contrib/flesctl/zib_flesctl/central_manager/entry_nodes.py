#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb  9 14:04:20 2026

@author: jschlieffen
"""

import time
import subprocess
import os
from logging_lib.log_msg import *

# =============================================================================
# This class is used to start and stop flesnet/mstool for the entry nodes
# It gets as input the entry node list, the build_node ips and the specifc 
# attributes for the start of flesnet (e.g. rmda/zeromq)
# =============================================================================
class Entry_nodes:
    def __init__(self, node_list,entry_nodes_ips, entry_nodes_eth_ips,build_nodes_ips,build_nodes_eth_ips,parameters, Run_folder, Slurm_starter):
        super().__init__()
        self.node_list = node_list
        self.entry_nodes_ips = entry_nodes_ips
        self.entry_node_eth_ips = entry_nodes_eth_ips
        self.build_nodes_ips = build_nodes_ips
        self.build_nodes_eth_ips = build_nodes_eth_ips
        self.Run_folder = Run_folder
        self.Par_ = parameters
        self.Slurm_starter = Slurm_starter
        self.pids = {}
        if self.Par_.use_apptainer:
            self.apptainer_command = f"--export=https_proxy,http_proxy,SSL_CERT_FILE,CURL_CA_BUNDLE --singularity-container={self.Par_.apptainer_file}"
        else:
            self.apptainer_command = ""
    
    
    def write_Params(self):
        param_names = [
            "num_entrynodes",
            "influx_node_ip",
            "influx_token",
            "use_grafana",
            "path",
            "transport_method",
            "customize_string",
            "use_pattern_gen",
            "use_dmsa_files",
            "use_infiniband",
            "use_collectl",
            "mean",
            "size_var",
            "pattern",
            "overlap"
        ]
        with open('tmp/entry_nodes_params.txt', 'w') as Params_file:
            if self.Par_.use_infiniband:
                Params_file.write(f"entry node ips: {self.entry_nodes_ips} \n")
                Params_file.write(f"build node ips: {self.build_nodes_ips} \n")
            else:
                Params_file.write(f"entry node ips: {self.entry_nodes_eth_ips} \n")
                Params_file.write(f"build node ips: {self.build_nodes_eth_ips} \n")

            for name in param_names:
                value = getattr(self.Par_, name, None)
                Params_file.write(f"{name}: {value} \n")
        Params_file.close()
    
    def start_flesnet(self):
        self.write_Params()
        file = 'nodes/input.py'
        node_cnt = 0
        for node in self.node_list.keys():
            input_file = next((tup[1] for tup in self.Par_.input_files if tup[0] == ('entry_node_' + str(node_cnt))), None)
            if input_file is None:
                input_file = next((tup[1] for tup in self.Par_.input_files if tup[0] == 'e_default'), None)
            if not self.Par_.use_pattern_gen:
                logger.info(f'start entry node: {node}, with input file {input_file}')
            else:
                logger.info(f'start entry node: {node} with pattern generator')
            logfile = "%s/logs/flesnet/entry_nodes/entry_node_%s.log" % (self.Run_folder,node)
            logfile_collectl = "%s/logs/collectl/entry_nodes/entry_node_%s.csv" % (self.Run_folder,node)
            params = f"\"{input_file}\" {logfile} {self.node_list[node]['entry_node_idx']} {logfile_collectl}"
            start_successfull = self.Slurm_starter.start_process("Entry",node,self.Par_.num_cpus, "16GB",file,params)
            time.sleep(1)
            if not start_successfull:
                logger.error(f'ERROR occurried in entry node: {node}. Shutdown flesnet')
                return 'shutdown'
            node_cnt += 1
        return None
    
    
    

    def kill_process(self,kill_node):
        logger.info(f"Killing entry node: {kill_node}")
        if self.Slurm_starter.kill_process("Entry", kill_node):
            logger.status(f"Entry node: {kill_node} killed")
           
 
    def revieve_process(self,revieve_node):
        logger.info(f"revieve entry node: {revieve_node}")
        if self.Slurm_starter.revieve_process("Entry", revieve_node):
            logger.status(f"Entry node: {revieve_node} revieved")
    
    def stop_flesnet(self):
        for node in self.node_list.keys():
            logger.info(f"stopping entry node: {node}")
            stdout,stderr = self.Slurm_starter.stop_process("Entry", node, False)
            if stdout != "":
                logger.debug(f"Output from entry node: {node} \n {stdout}")
                logger.debug(f"Error from entry node: {node} \n {stderr}")
    