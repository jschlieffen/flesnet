#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb  9 14:05:17 2026

@author: jschlieffen
"""


import time
import subprocess
import os
from logging_lib.log_msg import *

#TODO: make port depended on node
class Timeslice_forwarding:
    
    def __init__(self, rec2build, parameters):    
        super().__init__()
        self.rec2build = rec2build
        self.Par_ = parameters
        self.pids = {}


    def write_Params(self):
        param_names = [
            "influx_node_ip",
            "influx_token",
            "use_grafana",
            "path",
            "port",
            "write_data_to_file",
            "analyze_data",
            "use_infiniband",
            "use_collectl"
        ]
        with open('tmp/receiving_nodes_params.txt', 'w') as Params_file:
            for name in param_names:
                value = getattr(self.Par_, name, None)
                Params_file.write(f"{name}: {value} \n")
        Params_file.close()   
        
    def start_receivers(self):
        self.write_Params()
        file = 'nodes/timeslice_forwarding.py'
        node_cnt = 0
        for receiving_node,build_node in self.rec2build:
            logger.info(f"start timeslice forwarding node {receiving_node} for build node {build_node['node']}")
            logfile = 'logs/flesnet/tsclient/receiving_node_%s.log' % (receiving_node)
            #print(build_node)
            logfile_collectl = 'logs/collectl/tsclient/receiving_node_%s.csv' % (receiving_node)
            if self.Par_.use_infiniband:
                build_node_ip = build_node['inf_ip']
            else:
                build_node_ip = build_node['eth_ip']
            command = (
                'srun --nodelist=%s --exclusive -N 1 -c %s %s %s %s %s'
                % (receiving_node, self.Par_.num_cpus ,file,logfile, build_node_ip, logfile_collectl)
            )
            try:
                #print(command)
                result = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) 
            except subprocess.CalledProcessError as e:
                logger.error(f'ERROR {e} occurried in entry node: {node}. Shutdown flesnet')
                return 'shutdown'
            time.sleep(1)
            self.pids[receiving_node] = result
            logger.status('start successful')
            node_cnt += 1
            
        logger.success('start of timeslice receivers successful')
        return None
    
    def kill_process(self, kill_node):
        logger.info(f"Killing Receiver node: {kill_node}")
        with open("tmp/central_manager.txt", "w") as f:
            f.write(f"Receiver {kill_node}: kill")
            f.flush()
            os.fsync(f.fileno())
        msg = ""
        while msg != f"Receiver {kill_node}: done killing":
            try:
                with open("tmp/nodes_response.txt", "r") as f:
                    msg = f.read().strip()
            except FileNotFoundError:
                msg = ""
            time.sleep(0.5)
        logger.status(f"Receiver node: {kill_node} killed")
    
    def revieve_process(self, revive_node):
        logger.info(f"revive Receiver node: {revive_node}")
        with open("tmp/central_manager.txt", "w") as f:
            f.write(f"Receiver {revive_node}: revive")
            f.flush()
            os.fsync(f.fileno())
        msg = ""
        while msg != f"Receiver {revive_node}: done reviving":
            try:
                with open("tmp/nodes_response.txt", "r") as f:
                    msg = f.read().strip()
            except FileNotFoundError:
                msg = ""
            time.sleep(0.5)
        logger.status(f"Receiver node: {revive_node} revive")
        
    def stop_timeslice_forwarding(self):
        for node, build_node in self.rec2build:
            logger.info(f"stopping Receiver node: {node}")
            with open("tmp/central_manager.txt", "w") as f:
                f.write(f"Receiver {node}: stop")
                f.flush()
                os.fsync(f.fileno())
            stdout, stderr = self.pids[node].communicate()
            logger.debug(f"Output from receiver node: {node} \n {stdout}")
            logger.debug(f"Error from receiver node: {node} \n {stderr}")