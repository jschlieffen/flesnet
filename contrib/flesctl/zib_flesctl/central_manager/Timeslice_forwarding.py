#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug 11 16:02:18 2026

@author: jschlieffen
"""

import time
import subprocess
import os
from logging_lib.log_msg import *

class Timeslice_forwarding:
    
    def __init__(self,sender,receiver,parameters,Run_folder,Slurm_starter):
        self.sender = sender
        self.receiver = receiver
        self.Par_ = parameters
        self.Run_folder = Run_folder
        self.Slurm_starter = Slurm_starter
        self.commands_r = {}
        self.commands_s = {}
        
        
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
    
    def define_sender_commands(self,node_name,collectl_logfile,logfile,logfile_tsclient,input_file,idx):
        commands = {}
        shm_str = f"fles_out_b{idx}"
        if self.Par_.use_collectl:
            commands['1'],commands['2'] = self.define_collectl_commands(collectl_logfile)
        file_reader_tsclient_command = (
            f"{self.Par_.path}./tsclient "
            f"-L {logfile_tsclient} "
            f"-l 1 "
            f"-i file:\"{input_file}\" "
            f"-o shm:{shm_str}?n={self.Par_.num_components}\\&descsize={self.Par_.desc_size}\\&datasize={self.Par_.data_size}"
        )
        if self.Par_.use_dtsa_files:
            file_reader_tsclient_command += " -D 1"
        input_tsclient_command = (
            f"{self.Par_.path}./tsclient "
            f"-L logfile "
            f"-i shm:{shm_str} "
            f"-o tcp://*:{self.Par_.port} "
        )
        if self.Par_.use_grafana:
            file_reader_tsclient_command += f" -m influx2:{self.Par_.influx_node_ip}:tsclient_status:{self.Par_.influx_token}"
            input_tsclient_command += f" -m influx2:{self.Par_.influx_node_ip}:tsclient_status:{self.Par_.influx_token}"
        commands['3'] = file_reader_tsclient_command
        commands['4'] = input_tsclient_command
        return commands 
    
    def define_receiver_commands(self,node_name, collectl_logfile,logfile,logfile_tsclient, idx,sender_node_ip):
        commands = {}
        shm_str = f"fles_out_b{idx}"
        if self.Par_.use_collectl:
            commands['1'], commands['2'] = self.define_collectl_commands(collectl_logfile)
        shm_tsclient_command = (
            f"{self.Par_.path}./tsclient "
            f"-l 1 "
            f"-L {logfile_tsclient} "
            f"-i shm:{shm_str}"
        )
        if self.Par_.analyze_data:
            shm_tsclient_command += " -a"
        output_tsclient_command = (
            f"{self.Par_.path}./tsclient "
            f"-l 1 "
            f"-L {logfile} "
            f"-i tcp://{sender_node_ip}:{self.Par_.port} "
            f"-o shm:{shm_str}?n={self.Par_.num_components}\\&descsize={self.Par_.desc_size}\\&datasize={self.Par_.data_size}"
        )            
        if self.Par_.use_grafana:
            shm_tsclient_command += f" -m influx2:{self.Par_.influx_node_ip}:tsclient_status:{self.Par_.influx_token}"
            output_tsclient_command += f" -m influx2:{self.Par_.influx_node_ip}:tsclient_status:{self.Par_.influx_token}"
        commands['3'] = shm_tsclient_command
        commands['4'] = output_tsclient_command
        return commands
    
    def start_Senders(self):
        node_cnt = 0
        for node_id,node in self.sender.items():
            input_file = next((tup[1] for tup in self.Par_.input_tsa_files if tup[0] == ('input_node_' + str(node_cnt))), None)
            if input_file is None:
                input_file = next((tup[1] for tup in self.Par_.input_tsa_files if tup[0] == 'i_default'), None)
            logger.info(f"start timeslice sender: {node_id} with input file: {input_file}")
            logfile = '%s/logs/flesnet/tsclient/sender_node_%s.log' % (self.Run_folder,node_id)
            logfile_collectl = '%s/logs/collectl/tsclient/sender_node_%s.csv' % (self.Run_folder,node_id)
            logfile_tsclient = '%s/logs/flesnet/tsclient/sender_node_%s_input_file_reader_tsclient.log' % (self.Run_folder,node_id)
            if self.Par_.use_infiniband:
                node_ip = node['inf_ip']
            else:
                node_ip = node['eth_ip']
            self.commands_s[node_id] = self.define_sender_commands(node_id, logfile_collectl, logfile, logfile_tsclient, input_file, node_cnt)
            self.write_commands(node_id,self.commands_s[node_id])
            start_successfull = self.Slurm_starter.start_process(node_id,self.Par_.num_cpus,"16GB")
            if not start_successfull:
                logger.error(f'ERROR occurried in sender node: {node}. Shutdown flesnet')
                return 'shutdown'
            time.sleep(1)
            logger.status('start successful')
            node_cnt += 1
        return None
            
    def start_receivers(self):
        node_cnt = 0
        for node_id,node in self.receiver.items():
            sender_node = node['sender_node']
            logger.info(f"start timeslice forwarding node {node_id} for sender node {sender_node['node']}")
            logfile = '%s/logs/flesnet/tsclient/receiving_node_%s.log' % (self.Run_folder,node_id)
            logfile_collectl = '%s/logs/collectl/tsclient/receiving_node_%s.csv' % (self.Run_folder,node_id)
            logfile_tsclient = '%s/logs/flesnet/tsclient/receiver_node_%s_shm_tsclient.log' % (self.Run_folder,node_id)
                        
            if self.Par_.use_infiniband:
                sender_node_ip = sender_node['inf_ip']
            else:
                sender_node_ip = sender_node['eth_ip']
            self.commands_r[node_id] = self.define_receiver_commands(node_id, logfile_collectl, logfile, logfile_tsclient, node_cnt, sender_node_ip)
            self.write_commands(node_id,self.commands_r[node_id])
            start_successfull = self.Slurm_starter.start_process(node_id,self.Par_.num_cpus,"16GB")
            if not start_successfull:
                logger.error(f'ERROR occurried in sender node: {node}. Shutdown flesnet')
                return 'shutdown'
            time.sleep(1)
            logger.status('start successful')
            node_cnt += 1
        return None
    
    def stop_timeslice_forwarding(self):
        for node in self.receiver.keys():
            logger.info(f"stopping Receiver node: {node}")
            stdout,stderr = self.Slurm_starter.stop_process(node, False)
            if stdout != "":
                logger.debug(f"Output from Receiver node: {node} \n {stdout}")
                logger.debug(f"Error from Receiver node: {node} \n {stderr}")
                
                
    def stop_timeslice_forwarding_sender(self):
        
        for node in self.sender.keys():
            logger.info(f"stopping Sender: {node}")
            stdout,stderr = self.Slurm_starter.stop_process(node, False)
            if stdout != "":
                logger.debug(f"Output from Sender node: {node} \n {stdout}")
                logger.debug(f"Error from Sender node: {node} \n {stderr}")
        