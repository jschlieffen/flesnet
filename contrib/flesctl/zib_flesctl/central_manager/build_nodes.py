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
    
    def __init__(self,node_list,entry_nodes_ips,entry_nodes_eth_ips, build_nodes_ips, build_nodes_eth_ips,parameters, Run_folder):
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
        self.pids = {}
    
    

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
            command = (
                'srun --nodelist=%s --exclusive -N 1 -c %s %s %s %s %s %s'
                % (node, self.Par_.num_cpus ,file,logfile, self.node_list[node]['build_node_idx'], logfile_collectl, logfile_tf)
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

        
    #TODO: Tippfehler, es heisst revive
    def revieve_process(self, revive_node):
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
            
            if self.Par_.ZIB_timesliceforwarding:
                with open("tmp/central_manager.txt", "w") as f:
                    f.write(f"TF Input {node}: stop")
                    f.flush()
                    os.fsync(f.fileno())
                    f.close()
            time.sleep(1)
            logger.info(f"stopping build node: {node}")
            with open("tmp/central_manager.txt", "w") as f:
                f.write(f"Build {node}: stop")
                f.flush()
                os.fsync(f.fileno())
                f.close()

            stdout, stderr = self.pids[node].communicate()
            logger.debug(f"Output from build node: {node} \n {stdout}")
            logger.debug(f"Error from build node: {node} \n {stderr}")
    