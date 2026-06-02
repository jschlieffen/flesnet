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
    
    def __init__(self, sender,receiver, parameters, Run_folder):    
        super().__init__()
        #self.rec2build = rec2build
        self.sender = sender
        self.receiver = receiver
        self.Par_ = parameters
        self.Run_folder = Run_folder
        self.pids = {}
        self.pids_sender = {}
        if self.Par_.use_apptainer:
            self.apptainer_command = f"--export=https_proxy,http_proxy,SSL_CERT_FILE,CURL_CA_BUNDLE --singularity-container={self.Par_.apptainer_file}"
        else:
            self.apptainer_command = ""

    def write_Params(self):
        param_names = [
            "influx_node_ip",
            "influx_token",
            "use_grafana",
            "path",
            "port",
            "write_data_to_file",
            "path_to_output_file",
            "analyze_data",
            "use_infiniband",
            "use_collectl"
        ]
        with open('tmp/receiving_nodes_params.txt', 'w') as Params_file:
            for name in param_names:
                value = getattr(self.Par_, name, None)
                Params_file.write(f"{name}: {value} \n")
        Params_file.close()   
        
    def write_Params_Sender(self):
        param_names = [
                "influx_node_ip",
                "influx_token",
                "use_grafana",
                "path",
                "port",
                "use_collectl",
                "use_flesnet",
                "use_dtsa_files",
                "use_infiniband",
                "num_components",
                "desc_size",
                "data_size",
                "malloc_size"
        ]
        with open('tmp/sender_nodes_params.txt', 'w') as Params_file:
            if self.Par_.use_flesnet:
                param_names.remove("use_collectl")
                Params_file.write("use_collectl: 0 \n")
                param_names.remove('use_dtsa_files')
                Params_file.write("use_dtsa_files: 0 \n")
            for name in param_names:
                value = getattr(self.Par_, name, None)
                Params_file.write(f"{name}: {value} \n")

        Params_file.close()   
        
        
    def start_receivers(self):
        self.write_Params()
        file = 'nodes/timeslice_forwarding.py'
        node_cnt = 0
        for node_id,node in self.receiver.items():
            sender_node = node['sender_node']
            logger.info(f"start timeslice forwarding node {node_id} for sender node {sender_node['node']}")
            logfile = '%s/logs/flesnet/tsclient/receiving_node_%s.log' % (self.Run_folder,node_id)
            logfile_collectl = '%s/logs/collectl/tsclient/receiving_node_%s.csv' % (self.Run_folder,node_id)
            
            if self.Par_.use_infiniband:
                sender_node_ip = sender_node['inf_ip']
            else:
                sender_node_ip = sender_node['eth_ip']
            command = (
                'srun --nodelist=%s %s --exclusive -N 1 -c %s %s %s %s %s'
                % (node_id, self.apptainer_command, self.Par_.num_cpus ,file,logfile, sender_node_ip, logfile_collectl)
            )
            try:
                result = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) 
            except subprocess.CalledProcessError as e:
                logger.error(f'ERROR {e} occurried in receiver node: {node_id}. Shutdown flesnet')
                return 'shutdown'
            time.sleep(1)
            self.pids[node_id] = result
            logger.status('start successful')
            node_cnt += 1
            
        logger.success('start of timeslice receivers successful')
        return None
    
    def start_Senders(self):
        self.write_Params_Sender()
        file ='nodes/timeslice_forwarding_sender.py'
        node_cnt = 0
        for node_id,node in self.sender.items():
            input_file = next((tup[1] for tup in self.Par_.input_tsa_files if tup[0] == ('input_node_' + str(node_cnt))), None)
            if input_file is None:
                input_file = next((tup[1] for tup in self.Par_.input_tsa_files if tup[0] == 'i_remaining'), None)
            logger.info(f"start timeslice sender: {node_id}")
            logfile = '%s/logs/flesnet/tsclient/sender_node_%s.log' % (self.Run_folder,node_id)
            logfile_collectl = '%s/logs/collectl/tsclient/sender_node_%s.csv' % (self.Run_folder,node_id)
            logfile_tsclient = '%s/logs/flesnet/tsclient/sender_node_%s_input_file_reader_tsclient.log' % (self.Run_folder,node_id)
            if self.Par_.use_infiniband:
                node_ip = node['inf_ip']
            else:
                node_ip = node['eth_ip']
            command = (
                'srun --nodelist=%s %s --exclusive -N 1 -c %s %s %s %s %s %s %s %s' 
                % (node_id, self.apptainer_command,self.Par_.num_cpus, file, input_file, logfile, node_cnt, logfile_collectl, node_ip, logfile_tsclient)
            )
            try: 
                result = subprocess.Popen(command,shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            except subprocess.CalledProcessError as e:
                logger.error(f'ERROR {e} occurried in GSI timesliceforwarding sender node: {node_id}. Shutdown flesnet')
                return 'shutdown'
            time.sleep(1)
            self.pids_sender[node_id] = result
            logger.status('start successful')
            node_cnt += 1
        logger.success('start of timeslice sender successful')
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
    
    def kill_process_Sender(self, kill_node):
        logger.info(f"Killing Sender node: {kill_node}")
        with open("tmp/central_manager.txt", "w") as f:
            f.write(f"Sender {kill_node}: kill")
            f.flush()
            os.fsync(f.fileno())
        msg = ""
        while msg != f"Sender {kill_node}: done killing":
            try:
                with open("tmp/nodes_response.txt", "r") as f:
                    msg = f.read().strip()
            except FileNotFoundError:
                msg = ""
            time.sleep(0.5)
        logger.status(f"Sender node: {kill_node} killed")
        
    
    def revieve_process(self, revive_node):
        logger.info(f"revieve Receiver node: {revive_node}")
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
        logger.status(f"Receiver node: {revive_node} revieved")
        
    def revieve_process_Sender(self,revive_node):
        logger.info(f"revieve Sender node: {revive_node}")
        with open("tmp/central_manager.txt", "w") as f:
            f.write(f"Sender {revive_node}: revive")
            f.flush()
            os.fsync(f.fileno())
        msg = ""
        while msg != f"Sender {revive_node}: done reviving":
            try:
                with open("tmp/nodes_response.txt", "r") as f:
                    msg = f.read().strip()
            except FileNotFoundError:
                msg = ""
            time.sleep(0.5)
        logger.status(f"Sender node: {revive_node} revieved")
    
    def stop_timeslice_forwarding(self):
        for node, node_appendix in self.receiver.items():
            logger.info(f"stopping Receiver node: {node}")
            with open("tmp/central_manager.txt", "w") as f:
                f.write(f"Receiver {node}: stop")
                f.flush()
                os.fsync(f.fileno())
            stdout, stderr = self.pids[node].communicate()
            logger.debug(f"Output from receiver node: {node} \n {stdout}")
            logger.debug(f"Error from receiver node: {node} \n {stderr}")
            
    def stop_timeslice_forwarding_sender(self):
        for node_id, node in self.sender.items():
            logger.info(f"stopping Sender node: {node_id}")
            with open("tmp/central_manager.txt", "w") as f:
                f.write(f"Sender {node_id}: stop")
                f.flush()
                os.fsync(f.fileno())
            if self.Par_.use_flesnet:
                msg = ""
                while msg != f"Sender {node_id}: done terminating":
                    try:
                        with open("tmp/nodes_response.txt", "r") as f:
                            msg = f.read().strip()
                    except FileNotFoundError:
                        msg = ""
                    time.sleep(0.5)
                logger.debug(f"TF Sender node: {node_id} stopped. See build nodes for output")
            #self.pids_sender[node_id].terminate()
            else:
                stdout, stderr = self.pids_sender[node_id].communicate()
                logger.debug(f"Output from sender node: {node_id} \n {stdout}")
                logger.debug(f"Error from sender node: {node_id} \n {stderr}")
    