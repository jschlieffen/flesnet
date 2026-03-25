#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb  9 14:05:02 2026

@author: jschlieffen
"""

import time
import subprocess
import os
from logging_lib.log_msg import *

# =============================================================================
# This class is used to start and stop flesnet on nodes that are used for both 
# entry nodes and build nodes. It gets as input the node list, the 
# entry node ips, build node ips and the specifc 
# attributes for the start of flesnet (e.g. rmda/zeromq)
# =============================================================================
class Super_nodes:
    def __init__(self,node_list,entry_nodes_ips,entry_nodes_eth_ips,build_nodes_ips,build_nodes_eth_ips,parameters, Run_folder):
        super().__init__()
        self.node_list = node_list
        #self.num_build_nodes = num_build_nodes
        self.entry_node_ips = entry_nodes_ips
        self.entry_node_eth_ips = entry_nodes_eth_ips
        self.build_nodes_ips = build_nodes_ips
        self.build_nodes_eth_ips = build_nodes_eth_ips
        self.Par_ = parameters
        self.Run_folder = Run_folder 
        self.pids = {}
        
    
    def write_Params(self):
        param_names = [
            "num_buildnodes",
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
            "overlap",
            "desc_size",
            "data_size", 
            "activate_timesliceforwarding",
            "ZIB_timesliceforwarding"
        ]
        with open('tmp/super_nodes_params.txt', 'w') as Params_file:
            if self.Par_.use_infiniband:
                Params_file.write(f"entry node ips: {self.entry_node_ips} \n")
                Params_file.write(f"build node ips: {self.build_nodes_ips} \n")
            else:
                Params_file.write(f"entry node ips: {self.entry_node_eth_ips} \n")
                Params_file.write(f"build node ips: {self.build_nodes_eth_ips} \n")
            for name in param_names:
                value = getattr(self.Par_, name, None)
                Params_file.write(f"{name}: {value} \n")
        Params_file.close()
        
    
    def start_flesnet(self):
        self.write_Params()
        file = 'nodes/super_nodes.py'
        node_cnt = 0
        for node in self.node_list.keys():
            input_file = next((tup[1] for tup in self.Par_.input_files if tup[0] == ('entry_node_' + str(node_cnt))), None)
            if input_file is None:
                input_file = next((tup[1] for tup in self.Par_.input_files if tup[0] == 'e_remaining'), None)
            if not self.Par_.use_pattern_gen:
                logger.info(f'start super node: {node}, with input file {input_file}')
            else:
                logger.info(f'start super node: {node}, with pattern generator')
            logger.status(f'start super node')
            logfile_entry_node = "%s/logs/flesnet/entry_nodes/entry_node_%s.log" % (self.Run_folder,node)
            logfile_build_node = "%s/logs/flesnet/build_nodes/build_node_%s.log" % (self.Run_folder,node)
            logfile_collectl_entry_node = "%s/logs/collectl/entry_nodes/entry_node_%s.csv" % (self.Run_folder,node)
            logfile_collectl_build_node = "%s/logs/collectl/build_nodes/build_node_%s.csv" % (self.Run_folder,node)
            if self.Par_.ZIB_timesliceforwarding:
                logfile_tf = '%s/logs/timeslice_forwarding/input_nodes/input_node_%s.log' % (self.Run_folder,node)
            else:
                logfile_tf = '%s/logs/flesnet/tsclient/sender_node_%s.log' % (self.Run_folder,node)
            command = (
                'srun --nodelist=%s --exclusive -N 1 -c %s %s %s %s %s %s %s %s %s %s'
                % (node, self.Par_.num_cpus ,file,input_file,logfile_entry_node, logfile_build_node, self.node_list[node]['entry_node_idx'],
                   self.node_list[node]['build_node_idx'], logfile_collectl_entry_node, logfile_collectl_build_node, logfile_tf)
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
    
    
    def kill_process_entry(self, kill_node):
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

    def kill_process_build(self, kill_node):
        logger.info(f"Killing build node: {kill_node}")
        with open("tmp/central_manager.txt", "w") as f:
            f.write(f"Build {kill_node}: kill")
            f.flush()
            os.fsync(f.fileno())
        msg = ""
        while msg != f"Build {kill_node}: done killing":
            try:
                with open("tmp/nodes_response.txt", "r") as f:
                    msg = f.read().strip()
            except FileNotFoundError:
                msg = ""
            time.sleep(0.5)
        logger.status(f"Build node: {kill_node} killed")

    def revieve_process_entry(self, revive_node):
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
        
    def revieve_process_build(self, revive_node):
        logger.info(f"revive build node: {revive_node}")
        with open("tmp/central_manager.txt", "w") as f:
            f.write(f"Build {revive_node}: revive")
            f.flush()
            os.fsync(f.fileno())
        msg = ""
        while msg != f"Build {revive_node}: done reviving":
            try:
                with open("tmp/nodes_response.txt", "r") as f:
                    msg = f.read().strip()
            except FileNotFoundError:
                msg = ""
            time.sleep(0.5)
        logger.status(f"build node: {revive_node} revive")     
        
    def stop_flesnet(self):
        for node in self.node_list.keys():
            logger.info(f"stopping entry node: {node}")
            with open("tmp/central_manager.txt", "w") as f:
                f.write(f"Entry {node}: stop")
                f.flush()
                os.fsync(f.fileno())
            stdout, stderr = self.pids[node].communicate()
            logger.debug(f"Output from super node: {node} \n {stdout}")
            logger.debug(f"Error from super node: {node} \n {stderr}")

