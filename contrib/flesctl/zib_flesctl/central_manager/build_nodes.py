#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb  9 14:04:28 2026

@author: jschlieffen
"""

import time
import subprocess
import os
from logging_lib.log_msg import *

# =============================================================================
# This class is used to start and stop flesnet for the build nodes
# It gets as input the build node list, the entry node ips and the specifc 
# attributes for the start of flesnet (e.g. rmda/zeromq)
# =============================================================================
class Build_nodes:
    
    def __init__(self,node_list,entry_nodes_ips,entry_nodes_eth_ips, build_nodes_ips, build_nodes_eth_ips,parameters, Run_folder, Slurm_starter):
        super().__init__()
        self.node_list = node_list
        #self.num_build_nodes = num_build_nodes
        self.entry_node_ips = entry_nodes_ips
        self.entry_node_eth_ips = entry_nodes_eth_ips
        self.build_node_ips = build_nodes_ips
        self.build_nodes_eth_ips = build_nodes_eth_ips
        #self.central_manager_ips = central_manager_ips, 
        #self.central_manager_eth_ips = central_ma´nager_eth_ips
        self.Par_ = parameters
        self.Run_folder = Run_folder 
        self.Slurm_starter = Slurm_starter
        self.pids = {}
        if self.Par_.use_apptainer:
            self.apptainer_command = f"--export=https_proxy,http_proxy,SSL_CERT_FILE,CURL_CA_BUNDLE --singularity-container={self.Par_.apptainer_file}"
        else:
            self.apptainer_command = ""
    

    def write_Params(self):
        param_names = [
            "num_buildnodes",
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
            "desc_size",
            "data_size",
            "ZIB_timesliceforwarding", 
            "activate_timesliceforwarding"
        ]
        with open('tmp/build_nodes_params.txt', 'w') as Params_file:
            if self.Par_.use_infiniband:
                Params_file.write(f"entry node ips: {self.entry_node_ips} \n")
                Params_file.write(f"build node ips: {self.build_node_ips} \n")
            else:
                Params_file.write(f"entry node ips: {self.entry_node_eth_ips} \n")
                Params_file.write(f"build node ips: {self.build_node_eth_ips} \n")
            for name in param_names:
                value = getattr(self.Par_, name, None)
                Params_file.write(f"{name}: {value} \n")
        Params_file.close()


    def start_flesnet(self):
        self.write_Params()
        file = 'nodes/output.py'
        node_cnt = 0
        for node in self.node_list.keys():
            logger.info(f'start build node: {node}')
            logfile = '%s/logs/flesnet/build_nodes/build_node_%s.log' % (self.Run_folder,node)
            if self.Par_.ZIB_timesliceforwarding:
                logfile_tf = '%s/logs/timeslice_forwarding/input_nodes/input_node_%s.log' % (self.Run_folder,node)
            else:
                logfile_tf = '%s/logs/flesnet/tsclient/sender_node_%s.log' % (self.Run_folder,node)
            logfile_collectl = '%s/logs/collectl/build_nodes/build_node_%s.csv' % (self.Run_folder,node)
            params = f"{logfile} {self.node_list[node]['build_node_idx']} {logfile_collectl} {logfile_tf}"
            start_successfull = self.Slurm_starter.start_process("Build",node,self.Par_.num_cpus,"16GB", file, params)
            if not start_successfull:
                logger.error(f'ERROR occurried in build node: {node}. Shutdown flesnet')
                return 'shutdown'
            time.sleep(1)
            node_cnt += 1
        return None


    def kill_process(self,kill_node):
        logger.info(f"Killing build node: {kill_node}")
        if self.Slurm_starter.kill_process("Build",kill_node):
            logger.status(f"Build node: {kill_node} killed")
        
    def revieve_process(self,revieve_node):
        logger.info(f"revieve build node: {revieve_node}")
        if self.Slurm_starter.revieve_process("Build", revieve_node):
            logger.status(f"build node: {revieve_node} revieve") 
            
    def stop_flesnet(self):
        for node in self.node_list:
            logger.info(f"stopping build node: {node}")
            stdout,stderr = self.Slurm_starter.stop_process("Build", node, False)
            if stdout != "":
                logger.debug(f"Output from build node: {node} \n {stdout}")
                logger.debug(f"Error from build node: {node} \n {stderr}")