#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb  9 14:05:45 2026

@author: jschlieffen
"""

import time
import subprocess
import os
from logging_lib.log_msg import *

# =============================================================================
#      TODO:       Port is wrong, logfile names
# =============================================================================
class Timeslice_forwarding_ZIB:
    
    def __init__(self,central_manager, central_manager_ips, central_manager_eth_ips, output_nodes,input_nodes, parameters):
        self.central_manager = central_manager
        self.central_manager_ips = central_manager_ips
        self.central_manager_eth_ips = central_manager_eth_ips
        self.output_nodes = output_nodes
        
        self.input_nodes = input_nodes
        self.pids_cm = {}
        self.pids_o = {}
        self.pids_i = {}
        self.Par_ = parameters
        
    
    def write_params_cm(self):
        param_names = [
            "port",
            "path",
            "use_infiniband",
            "use_collectl",
        ]
        with open('tmp/tf_cm_nodes_params.txt', 'w') as Params_file:
            if self.Par_.use_infiniband:
                Params_file.write(f"cm node ips: {self.central_manager_ips} \n")
            else:
                Params_file.write(f"cm node ips: {self.central_manager_eth_ips} \n")
            for name in param_names:
                value = getattr(self.Par_, name, None)
                Params_file.write(f"{name}: {value} \n")
        Params_file.close()
        
    def write_params_output(self):
        param_names = [
                "port",
                "path",
                "use_infiniband",
                "use_collectl",
                "write_data_to_file",
                "analyze_data"
            ]   
        with open('tmp/tf_output_nodes_params.txt', 'w') as Params_file:
            if self.Par_.use_infiniband:
                Params_file.write(f"cm node ips: {self.central_manager_ips} \n")
            else:
                Params_file.write(f"cm node ips: {self.central_manager_eth_ips} \n")
            for name in param_names:
                value = getattr(self.Par_, name, None)
                Params_file.write(f"{name}: {value} \n")
        Params_file.close()
        
    def write_params_input(self):
        param_names = [
                "port",
                "path",
                "use_infiniband",
                "use_collectl",
                "use_flesnet", 
                "use_dtsa_files"
            ]   
        with open('tmp/tf_input_nodes_params.txt', 'w') as Params_file:
            if self.Par_.use_infiniband:
                Params_file.write(f"cm node ips: {self.central_manager_ips} \n")
            else:
                Params_file.write(f"cm node ips: {self.central_manager_eth_ips} \n")
            if self.Par_.use_flesnet:
                param_names.remove("use_collectl")
                Params_file.write("use_collectl: 0 \n")
            for name in param_names:
                value = getattr(self.Par_, name, None)
                Params_file.write(f"{name}: {value} \n")
        Params_file.close()
        
    def start_cm(self):
        file = 'nodes/tf_central_manager.py'
        node_cnt = 0
        self.write_params_cm()
        for node in self.central_manager.keys():
            logger.info(f'start central manager for timeslice-forwarding: {node}')
            logfile = "logs/timeslice_forwarding/central_manager/central_manager_%s.log" % node
            logfile_collectl = "logs/collectl/timeslice_forwarding/central_manager/central_manager_%s.csv" % node
            command = (
                'srun --nodelist=%s --exclusive -N 1 -c %s %s %s %s'
                % (node, self.Par_.num_cpus ,file,logfile, logfile_collectl)
            )
            try:
                #print(command)
                result = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) 
            except subprocess.CalledProcessError as e:
                logger.error(f'ERROR {e} occurried in central manager: {node}. Shutdown flesnet')
                return 'shutdown'
            time.sleep(1)
            self.pids_cm[node] = result
            logger.status('start successful')
            node_cnt += 1
        return None
     
    def start_output_nodes(self):
        file = 'nodes/tf_output_node.py'
        nodes_cnt = 0
        self.write_params_output()
        for node in self.output_nodes.keys():
            logger.info(f'start output node for timeslice-forwarding: {node}')
            logfile = "logs/timeslice_forwarding/output_nodes/output_node_%s.log" % node
            logfile_collectl = "logs/collectl/timeslice_forwarding/output_nodes/output_node_%s.csv" % node
            logfile_tsclient = "logs/timeslice_forwarding/tsclient/output_nodes/output_node_%s.log" % node
            if self.Par_.use_infiniband:
                ip = self.output_nodes[node]['inf_ip']
            else:
                ip = self.output_nodes[node]['eth_ip']
            command = (
                'srun --nodelist=%s --exclusive -N 1 -c %s %s %s %s %s %s %s'
                % (node, self.Par_.num_cpus ,file,logfile, self.output_nodes[node]['output_node_idx'], ip, logfile_collectl, logfile_tsclient)
            )
            try:
                #print(command)
                result = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) 
            except subprocess.CalledProcessError as e:
                logger.error(f'ERROR {e} occurried in tf output node: {node}. Shutdown flesnet')
                return 'shutdown'
            time.sleep(1)
            self.pids_o[node] = result
            nodes_cnt += 1
        return None
        
    def start_input_nodes(self):
        file = 'nodes/tf_input_node.py'
        nodes_cnt = 0 
        self.write_params_input()
        for node in self.input_nodes.keys():
            input_file = next((tup[1] for tup in self.Par_.input_tsa_files if tup[0] == ('input_node_' + str(nodes_cnt))), None)
            print(input_file)
            if input_file is None:
                input_file = next((tup[1] for tup in self.Par_.input_tsa_files if tup[0] == 'i_remaining'), None)
            
            logger.info(f'start input node for timeslice-forwarding: {node}')
            logfile = "logs/timeslice_forwarding/input_nodes/input_node_%s.log" % node
            logfile_collectl = "logs/collectl/timeslice_forwarding/input_nodes/input_node_%s.csv" % node
            logfile_tsclient = "logs/timeslice_forwarding/tsclient/input_nodes/input_node_%s.log" % node
            if self.Par_.use_infiniband:
                ip = self.input_nodes[node]['inf_ip']
            else:
                ip = self.input_nodes[node]['eth_ip']
            command = (
                'srun --nodelist=%s --exclusive -N 1 -c %s %s %s %s %s %s %s %s'
                % (node, self.Par_.num_cpus ,file,input_file ,logfile, self.input_nodes[node]['input_node_idx'], ip, logfile_collectl, logfile_tsclient)
            )
            try:
                #print(command)
                result = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) 
            except subprocess.CalledProcessError as e:
                logger.error(f'ERROR {e} occurried in tf input node: {node}. Shutdown flesnet')
                return 'shutdown'
            time.sleep(1)
            self.pids_i[node] = result
            nodes_cnt += 1
        return None
    
    def kill_input_node(self, kill_node):
        logger.info(f"Killing Input node: {kill_node}")
        with open("tmp/central_manager.txt","w") as f:
            f.write(f"TF Input {kill_node}: kill")
            f.flush()
            os.fsync(f.fileno())
            f.close()
        msg = ""
        while msg != f"TF Input {kill_node}: done killing":
            try:
                with open("tmp/nodes_response.txt","r") as f:
                    msg = f.read().strip()
            except FileNotFoundError:
                msg = ""
            time.sleep(0.5)
        logger.status(f"Input node {kill_node}: killed")
                      
                      
    def revieve_input_node(self, revieve_node):
        logger.info(f"revieve Input node: {revieve_node}")
        with open("tmp/central_manager.txt","w") as f:
            f.write(f"TF Input {revieve_node}: revive")
            f.flush()
            os.fsync(f.fileno())
            f.close()
        msg = ""
        while msg != f"TF Input {revieve_node}: done reviving":
            try:
                with open("tmp/nodes_response.txt","r") as f:
                    msg = f.read().strip()
            except FileNotFoundError:
                msg = ""
            time.sleep(0.5)
        logger.status(f"Input node: {revieve_node} revieve")
        
    def kill_central_manager(self, kill_node):
        logger.info(f"Killing Central Manager: {kill_node}")
        with open("tmp/central_manager.txt","w") as f:
            f.write(f"TF Central Manager {kill_node}: kill")
            f.flush()
            os.fsync(f.fileno())
            f.close()
        msg = ""
        while msg != f"TF Central Manager {kill_node}: done killing":
            try:
                with open("tmp/nodes_response.txt","r") as f:
                    msg = f.read().strip()
            except FileNotFoundError:
                msg = ""
            time.sleep(0.5)
        logger.status(f"Central Manager: {kill_node} killed")
                      
                      
    def revieve_central_manager(self, revieve_node):
        logger.info(f"revieve Central Manager: {revieve_node}")
        with open("tmp/central_manager.txt","w") as f:
            f.write(f"TF Central Manager {revieve_node}: revive")
            f.flush()
            os.fsync(f.fileno())
            f.close()
        msg = ""
        while msg != f"TF Central Manager {revieve_node}: done reviving":
            try:
                with open("tmp/nodes_response.txt","r") as f:
                    msg = f.read().strip()
            except FileNotFoundError:
                msg = ""
            time.sleep(0.5)
        logger.status(f"Central Manager: {revieve_node} revieve")
        
        
    def kill_output_node(self, kill_node):
        logger.info(f"Killing Output node: {kill_node}")
        with open("tmp/central_manager.txt","w") as f:
            f.write(f"TF Output {kill_node}: kill")
            f.flush()
            os.fsync(f.fileno())
            f.close()
        msg = ""
        while msg != f"TF Output {kill_node}: done killing":
            try:
                with open("tmp/nodes_response.txt","r") as f:
                    msg = f.read().strip()
            except FileNotFoundError:
                msg = ""
            time.sleep(0.5)
        logger.status(f"Output node: {kill_node} killed")
                      
                      
    def revieve_output_node(self, revieve_node):
        logger.info(f"revieve Output node: {revieve_node}")
        with open("tmp/central_manager.txt","w") as f:
            f.write(f"TF Output {revieve_node}: revive")
            f.flush()
            os.fsync(f.fileno())
            f.close()
        msg = ""
        while msg != f"TF Output {revieve_node}: done reviving":
            try:
                with open("tmp/nodes_response.txt","r") as f:
                    msg = f.read().strip()
            except FileNotFoundError:
                msg = ""
            time.sleep(0.5)
        logger.status(f"Output node: {revieve_node} revieve")
        
    def stop_central_manager(self):
        for node in self.central_manager.keys():
            logger.info(f"stopping central manager: {node}")
            with open("tmp/central_manager.txt", "w") as f:
                f.write(f"TF Central Manager {node}: stop")
                f.flush()
                os.fsync(f.fileno())
            stdout, stderr = self.pids_cm[node].communicate()
            logger.debug(f"Output from central manager: {node} \n {stdout}")
            logger.debug(f"Error from central manager: {node} \n {stderr}")
            
    def stop_input_nodes(self):
        for node in self.input_nodes.keys():
            logger.info(f"stopping TF input node: {node}")
            with open("tmp/central_manager.txt", "w") as f:
                f.write(f"TF Input {node}: stop")
                f.flush()
                os.fsync(f.fileno())
            if self.Par_.use_flesnet:
                msg = ""
                while msg != f"TF Input {node}: done terminating":
                    try:
                        with open("tmp/nodes_response.txt", "r") as f:
                            msg = f.read().strip()
                    except FileNotFoundError:
                        msg = ""
                    time.sleep(0.5)
                logger.debug(f"TF input node: {node} stopped. See build nodes for output")
            else:
                stdout, stderr = self.pids_i[node].communicate()
                logger.debug(f"Output from TF input node: {node} \n {stdout}")
                logger.debug(f"Error from TF input node: {node} \n {stderr}")
            
    def stop_output_nodes(self):
        for node in self.output_nodes.keys():
            logger.info(f"stopping TF output node: {node}")
            with open("tmp/central_manager.txt", "w") as f:
                f.write(f"TF Output {node}: stop")
                f.flush()
                os.fsync(f.fileno())
            stdout, stderr = self.pids_o[node].communicate()
            logger.debug(f"Output from TF output node: {node} \n {stdout}")
            logger.debug(f"Error from TF output node: {node} \n {stderr}")