#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 10 18:04:43 2026

@author: jschlieffen
"""

import time
import subprocess
import os
from logging_lib.log_msg import *
import central_manager.Slurm_starter as ss

class Timeslice_forwarding_ZIB:
    
    def __init__(self, central_manager, central_manager_ips, central_manager_eth_ips, output_nodes,input_nodes, parameters,  Run_folder, Slurm_starter):
        self.central_manager = central_manager
        self.central_manager_ips = central_manager_ips
        self.central_manager_eth_ips = central_manager_eth_ips
        self.output_nodes = output_nodes
        self.Slurm_starter = Slurm_starter
        self.input_nodes = input_nodes
        self.commands_cm = {}
        self.commands_o = {}
        self.commands_i = {}
        self.Par_ = parameters
        self.Run_folder = Run_folder 
        
    def write_commands(self,node_name,commands):
        with open(f'tmp/params/{node_name}.txt','w') as f:
            for command_idx,command in commands.items():
                f.write(f"command_{command_idx}: {command} \n")
        f.close()
        
    def define_collectl_commands(self,collectl_logfile):    
        if self.Par_.use_infiniband:
            collectl_network_command = f"sudo collectl --plot --sep , -i 1 -sx > {collectl_logfile}"
        else:
            collectl_network_command = f"collectl --plot --sep , -i 1 -sn > {collectl_logfile}"
        cpu_collectl_logfile = collectl_logfile.replace(".csv", "_cpu_usage.csv")
        collectl_cpu_command = f"collectl --plot --sep , -i 1 -sC > {cpu_collectl_logfile}"
        return collectl_network_command, collectl_cpu_command
        
    def define_commands_cm(self,node_name,collectl_logfile, logfile):
        commands = {}
        if self.Par_.use_collectl:
            commands['1'], commands['2'] = self.define_collectl_commands(collectl_logfile)
        cm_command = f"{self.Par_.path}./timeslice_forwarder -l 1 -c {self.central_manager_ips}:{self.Par_.port}"
        if self.Par_.use_grafana:
            cm_command += f" -m influx2:{self.Par_.influx_node_ip}:timeslice_forwarder_state:{self.Par_.influx_token}"
        commands['3'] = cm_command
        return commands
        
    def define_commands_input(self,node_name,collectl_logfile,logfile,logfile_tsclient,input_file,idx,node_ip):
        commands = {}
        shm_str = "fles_out_b{idx}"
        if self.Par_.use_collectl:
            commands['1'], commands['2'] = self.define_collectl_commands(collectl_logfile)
        #tsclient_command = f"{self.Par_.path}./timeslice_forwarder -l 1 -i file:\"{input_file}\" -o {shm_str}?n={self.Par_.num_components}\\&descsize={self.Par_.desc_size}\\&datasize={self.Par_.data_size}"
        tsclient_command = (
            f"{self.Par_.path}./tsclient "
            f"-L {logfile_tsclient} "
            f"-l 1 "
            f"-i file:\"{input_file}\" "
            f"-o shm:{shm_str}?n={self.Par_.num_components}\\&descsize={self.Par_.desc_size}\\&datasize={self.Par_.data_size}"
        )
        if self.Par_.use_dtsa_files:
            tsclient_command += " -D 1"
        input_command = (
            f"{self.Par_.path}./timeslice_forwarder "
            f"-l 1 "
            f"-c {self.central_manager_ips}:{self.Par_.port} "
            f"-A {node_ip}:{self.Par_.port} "
            f"-N {idx} "
            f"-i {shm_str}"
        )
        if self.Par_.use_grafana:
            tsclient_command +=  f" -m influx2:{self.Par_.influx_node_ip}:tsclient_status:{self.Par_.influx_token}"
            input_command +=  f" -m influx2:{self.Par_.influx_node_ip}:timeslice_forwarder_state:{self.Par_.influx_token}"
        commands['3'] = tsclient_command
        commands['4'] = input_command
        return commands
    
    def define_commands_output(self,node_name,collectl_logfile,logfile, logfile_tsclient,idx,node_ip):
        commands = {}
        shm_str = "fles_out_b{idx}"
        if self.Par_.use_collectl:
            commands['1'], commands['2'] = self.define_collectl_commands(collectl_logfile)
        tsclient_command = (
            f"{self.Par_.path}./tsclient "
            f"-l 1 "
            f"-L {logfile_tsclient} "
            f"-i shm:{shm_str}"
        )
        if self.Par_.analyze_data:
            tsclient_command += " -a"
        if self.Par_.write_data_to_file:
            with open('tmp/Run_folder_name.txt','r') as file:
                run_id = file.read().strip()
                file.close()
            tsclient_command += f"-o file:{self.Par_.path_to_output_file}/{run_id}/tsa_files/output_node_{node_name}.tsa"
        output_command = (
            f"{self.Par_.path}./timeslice_forwarder "
            f"-l 1 "
            f"-c {self.central_manager_ips}:{self.Par_.port} "
            f"-A {node_ip}:{self.Par_.port} "
            f"-N {idx} "
            f"-o {shm_str}?n={self.Par_.num_components}\\&descsize={self.Par_.desc_size}\\&datasize={self.Par_.data_size}"
        )
        if self.Par_.use_grafana:
            tsclient_command +=  f" -m influx2:{self.Par_.influx_node_ip}:tsclient_status:{self.Par_.influx_token}"
            output_command +=  f" -m influx2:{self.Par_.influx_node_ip}:timeslice_forwarder_state:{self.Par_.influx_token}"
        commands['3'] = tsclient_command
        commands['4'] = output_command
        return commands
    
    
    def start_cm(self):
        node_cnt = 0
        for node in self.central_manager.keys():
            logger.info(f'start central manager for timeslice-forwarding: {node}')
            logfile = "%s/logs/timeslice_forwarding/central_manager/central_manager_%s.log" % (self.Run_folder,node)
            logfile_collectl = "%s/logs/collectl/timeslice_forwarding/central_manager/central_manager_%s.csv" % (self.Run_folder,node)
            self.commands_cm[node] = self.define_commands_cm(node, logfile_collectl, logfile)
            self.write_commands(node,self.commands_cm[node])
            start_successfull = self.Slurm_starter.start_process(node,self.Par_.num_cpus,"16GB")
            if not start_successfull:
                logger.error(f'ERROR occurried in central manager: {node}. Shutdown flesnet')
                return 'shutdown'
            time.sleep(1)
            logger.status('start successful')
            node_cnt += 1
        return None
    
    def start_input_nodes(self):
        node_cnt = 0
        for node in self.input_nodes.keys():
            input_file = next((tup[1] for tup in self.Par_.input_tsa_files if tup[0] == ('input_node_' + str(node_cnt))), None)
            if input_file is None:
                input_file = next((tup[1] for tup in self.Par_.input_tsa_files if tup[0] == 'i_default'), None)
            
            logger.info(f'start input node for timeslice-forwarding: {node} with input file: {input_file}')
            logfile = "%s/logs/timeslice_forwarding/input_nodes/input_node_%s.log" % (self.Run_folder,node)
            logfile_collectl = "%s/logs/collectl/timeslice_forwarding/input_nodes/input_node_%s.csv" % (self.Run_folder,node)
            logfile_tsclient = "%s/logs/timeslice_forwarding/tsclient/input_nodes/input_node_%s.log" % (self.Run_folder,node)
            if self.Par_.use_infiniband:
                ip = self.input_nodes[node]['inf_ip']
            else:
                ip = self.input_nodes[node]['eth_ip']
            self.commands_i[node] = self.define_commands_input(node, logfile_collectl, logfile, logfile_tsclient, input_file, node_cnt, ip)
            self.write_commands(node, self.commands_i[node])
            start_successfull = self.Slurm_starter.start_process(node,self.Par_.num_cpus,"16GB")
            if not start_successfull:
                logger.error(f'ERROR occurried in central manager: {node}. Shutdown flesnet')
                return 'shutdown'
            time.sleep(1)
            logger.status('start successful')
            node_cnt += 1
        return None
            
    def start_output_nodes(self):
        node_cnt = 0
        for node in self.output_nodes.keys():
            logger.info(f'start output node for timeslice-forwarding: {node}')
            logfile = "%s/logs/timeslice_forwarding/output_nodes/output_node_%s.log" % (self.Run_folder,node)
            logfile_collectl = "%s/logs/collectl/timeslice_forwarding/output_nodes/output_node_%s.csv" % (self.Run_folder,node)
            logfile_tsclient = "%s/logs/timeslice_forwarding/tsclient/output_nodes/output_node_%s.log" % (self.Run_folder,node)
            if self.Par_.use_infiniband:
                ip = self.output_nodes[node]['inf_ip']
            else:
                ip = self.output_nodes[node]['eth_ip']
            self.commands_o[node] = self.define_commands_output(node, logfile_collectl, logfile, logfile_tsclient, node_cnt, ip)
            self.write_commands(node, self.commands_o[node])
            start_successfull = self.Slurm_starter.start_process(node,self.Par_.num_cpus,"16GB")
            if not start_successfull:
                logger.error(f'ERROR occurried in central manager: {node}. Shutdown flesnet')
                return 'shutdown'
            time.sleep(1)
            logger.status('start successful')
            node_cnt += 1
        return None
    
    def stop_central_manager(self):
        for node in self.central_manager.keys():
            logger.info(f"stopping central manager: {node}")
            stdout,stderr = self.Slurm_starter.stop_process( node, False)
            if stdout != "":
                logger.debug(f"Output from central manager: {node} \n {stdout}")
                logger.debug(f"Error from central manager: {node} \n {stderr}")
                
    def stop_input_nodes(self):
        for node in self.input_nodes.keys():
            logger.info(f"stopping TF Input node: {node}")
            if self.Par_.use_flesnet:
                stdout,stderr = self.Slurm_starter.stop_process(node, True)
                if stdout == "1":
                    logger.debug(f"TF input node: {node} stopped. See build nodes for output")
            else:
                stdout,stderr = self.Slurm_starter.stop_process(node, False)
                if stdout != "":
                    logger.debug(f"Output from TF input node: {node} \n {stdout}")
                    logger.debug(f"Error from TF input node: {node} \n {stderr}")
                    
    def stop_output_nodes(self):
        for node in self.output_nodes.keys():
            logger.info(f"stopping TF output node: {node}")
            stdout,stderr = self.Slurm_starter.stop_process(node, False)
            if stdout != "":
                logger.debug(f"Output from TF output node: {node} \n {stdout}")