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
    def __init__(self, node_list,entry_nodes_ips, entry_nodes_eth_ips,build_nodes_ips,build_nodes_eth_ips,parameters, Run_folder):
        super().__init__()
        self.node_list = node_list
        self.entry_nodes_ips = entry_nodes_ips
        self.entry_node_eth_ips = entry_nodes_eth_ips
        self.build_nodes_ips = build_nodes_ips
        self.build_nodes_eth_ips = build_nodes_eth_ips
        self.Run_folder = Run_folder
        self.Par_ = parameters
        self.pids = {}
    
    
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
                input_file = next((tup[1] for tup in self.Par_.input_files if tup[0] == 'e_remaining'), None)
            if not self.Par_.use_pattern_gen:
                logger.info(f'start entry node: {node}, with input file {input_file}')
            else:
                logger.info(f'start entry node: {node} with pattern generator')
            logfile = "%s/logs/flesnet/entry_nodes/entry_node_%s.log" % (self.Run_folder,node)
            logfile_collectl = "%s/logs/collectl/entry_nodes/entry_node_%s.csv" % (self.Run_folder,node)
            command = (
                'srun --nodelist=%s --exclusive -N 1 -c %s %s %s %s %s %s'
                % (node, self.Par_.num_cpus ,file,input_file,logfile, self.node_list[node]['entry_node_idx'], logfile_collectl)
            )
            try:
                result = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) 
            except subprocess.CalledProcessError as e:
                logger.error(f'ERROR {e} occurried in entry node: {node}. Shutdown flesnet')
                return 'shutdown'
            time.sleep(1)
            self.pids[node] = result
            logger.status('start successful')
            node_cnt += 1
        return None
    
    def kill_process(self, kill_node):
        logger.info(f"Killing entry node: {kill_node}")
        with open("tmp/central_manager.txt", "w") as f:
            f.write(f"Entry {kill_node}: kill")
            f.flush()
            os.fsync(f.fileno())
        msg = ""
        while msg != f"Entry {kill_node}: done killing":
            try:
                with open("tmp/nodes_response.txt", "r") as f:
                    msg = f.read().strip()
            except FileNotFoundError:
                msg = ""
            time.sleep(0.5)
        logger.status(f"Entry node: {kill_node} killed")
                
    
    #TODO: Tippfehler, es heisst revive
    def revieve_process(self, revive_node):
        logger.info(f"revive entry node: {revive_node}")
        with open("tmp/central_manager.txt", "w") as f:
            f.write(f"Entry {revive_node}: revive")
            f.flush()
            os.fsync(f.fileno())
        msg = ""
        while msg != f"Entry {revive_node}: done reviving":
            try:
                with open("tmp/nodes_response.txt", "r") as f:
                    msg = f.read().strip()
            except FileNotFoundError:
                msg = ""
            time.sleep(0.5)
        logger.status(f"Entry node: {revive_node} revive")
        
 
    
    def stop_flesnet(self):
        for node in self.node_list.keys():
            logger.info(f"stopping super node: {node}")
            with open("tmp/central_manager.txt", "w") as f:
                f.write(f"Entry {node}: stop")
                f.flush()
                os.fsync(f.fileno())
            stdout, stderr = self.pids[node].communicate()
            logger.debug(f"Output from entry node: {node} \n {stdout}")
            logger.debug(f"Error from entry node: {node} \n {stderr}")
    
    