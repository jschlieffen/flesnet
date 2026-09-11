#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep 10 13:51:50 2026

@author: jschlieffen
"""

from logging_lib.log_msg import *
import time
from central_manager import ZIB_Timeslice_forwarding as ZIB_T

class flesnet:
    
    def __init__(self,tsmanager, tsmanager_ip, tsbuilders,stservers,ZIB_timeslice_forwarding_cls,parameters,Run_folder,Slurm_starter):
        self.tsmanager = tsmanager
        self.tsmanager_ip = tsmanager_ip
        self.tsbuilders = tsbuilders
        self.stservers = stservers
        self.commands_tsm = {}
        self.commands_tsb = {}
        self.commands_sts = {}
        self.ZIB_timeslice_forwarding_cls = ZIB_timeslice_forwarding_cls
        self.Par_ = parameters
        self.Run_folder = Run_folder
        self.Slurm_starter = Slurm_starter
        
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
    
    def define_commands_tsm(self,node_name,collectl_logfile,logfile):
        commands = {}
        if self.Par_.use_collectl:
            commands['1'], commands['2'] = self.define_collectl_commands(collectl_logfile)
        tsm_command = f"{self.Par_.path}./tsmanager -l 2 -L {logfile} -p {self.Par_.port} {self.Par_.custom_str_tsmanager} "
        if self.Par_.use_grafana:
            tsm_command += f"--monitor influx2:{self.Par_.influx_node_ip}:flesnet_status:{self.Par_.influx_token}"
        commands['3'] = tsm_command
        return commands
    
    def define_commands_sts(self,node_name,collectl_logfile,logfile,node_ip):
        commands = {}
        if self.Par_.use_collectl:
            commands['1'], commands['2'] = self.define_collectl_commands(collectl_logfile)
        sts_command = (
            f"{self.Par_.path}./stserver -l 2 -L {logfile} "
            f"--tsmanager-address {self.tsmanager_ip}:{self.Par_.port} "
            f"--advertise-host {node_ip}:{self.Par_.port} "
            f"{self.Par_.custom_str_stserver} "
        )
        if self.Par_.use_grafana:
            sts_command += f"--monitor influx2:{self.Par_.influx_node_ip}:flesnet_status:{self.Par_.influx_token}"
        commands['3'] = sts_command
        return commands
    
    def define_commands_tsb(self,node_name,collectl_logfile,logfile,node_ip,idx,logfile_input=''):
        commands = {}
        if self.Par_.use_collectl:
            commands['1'], commands['2'] = self.define_collectl_commands(collectl_logfile)
        shm_str = f"fles_out_b{idx}_1"
        tsb_command = (
            f"{self.Par_.path}./tsbuilder -l 2 -L {logfile} "
            f"--shm-id {shm_str} "
            f"--tsmanager-address {self.tsmanager_ip}:{self.Par_.port} "
            f"{self.Par_.custom_str_tsbuilder} "
        )
        if self.Par_.use_grafana:
            tsb_command  += f"--monitor influx2:{self.Par_.influx_node_ip}:flesnet_status:{self.Par_.influx_token}"
        commands['3'] = tsb_command
        if self.Par_.ZIB_timesliceforwarding:
            commands_input = self.ZIB_timeslice_forwarding_cls.define_commands_input(node_name,collectl_logfile,logfile_input,"","",idx,node_ip,is_subprocess=True,use_tsclient=False)
            commands.update(commands_input)
        return commands
    
    def start_tsm(self):
        node_cnt = 0
        for node in self.tsmanager.keys():
            logger.info(f'starting tsmanager: {node}')
            logfile_collectl = "%s/logs/collectl/flesnet/tsmanager/tsmanager_%s.csv" % (self.Run_folder,node)
            logfile = "%s/logs/flesnet/tsmanager/tsmanager_%s.log" % (self.Run_folder,node)
            self.commands_tsm[node] = self.define_commands_tsm(node, logfile_collectl, logfile)
            self.write_commands(node,self.commands_tsm[node])
            start_successfull = self.Slurm_starter.start_process(node,self.Par_.num_cpus,self.Par_.mem)
            if not start_successfull:
                logger.error(f'ERROR occurried in central manager: {node}. Shutdown flesnet')
                return 'shutdown'
            time.sleep(1)
            logger.status('start successful')
            node_cnt += 1
        return None
    
    
    def start_sts(self):
        node_cnt = 0
        for node in self.stservers.keys():
            logger.info(f'starting stserver: {node}')
            logfile_collectl = "%s/logs/collectl/flesnet/stserver/stserver_%s.csv" % (self.Run_folder,node)
            logfile = "%s/logs/flesnet/stserver/stserver_%s.log" % (self.Run_folder,node)
            if self.Par_.use_infiniband:
                  ip = self.stservers[node]['inf_ip']
            else:
                  ip = self.stservers[node]['eth_ip']
            self.commands_sts[node] = self.define_commands_sts(node,logfile_collectl,logfile,ip)
            self.write_commands(node,self.commands_sts[node])
            start_successfull = self.Slurm_starter.start_process(node,self.Par_.num_cpus,self.Par_.mem)
            if not start_successfull:
                logger.error(f'ERROR occurried in central manager: {node}. Shutdown flesnet')
                return 'shutdown'
            time.sleep(1)
            logger.status('start successful')
            node_cnt += 1
        return None
    
    def start_tsb(self):
        node_cnt = 0
        for node in self.tsbuilders.keys():
            logger.info(f'starting tsbuilder: {node}')
            logfile_collectl = "%s/logs/collectl/flesnet/tsbuilder/tsbuilder_%s.csv" % (self.Run_folder,node)
            logfile = "%s/logs/flesnet/tsbuilder/tsbuilder_%s.log" % (self.Run_folder,node)
            if self.Par_.use_infiniband:
                ip = self.tsbuilders[node]['inf_ip']
            else:
                ip = self.tsbuilders[node]['eth_ip']
            if self.Par_.ZIB_timesliceforwarding:
                logfile_input = "%s/logs/timeslice_forwarding/input_nodes/input_node_%s" % (self.Run_folder,node)
                self.commands_tsb[node] = self.define_commands_tsb(node,logfile_collectl,logfile,ip,node_cnt,logfile_input)
            else:
                self.commands_tsb[node] = self.define_commands_tsb(node,logfile_collectl,logfile,ip,node_cnt)
            self.write_commands(node,self.commands_tsb[node])
            start_successfull = self.Slurm_starter.start_process(node,self.Par_.num_cpus,self.Par_.mem)
            if not start_successfull:
                logger.error(f'ERROR occurried in central manager: {node}. Shutdown flesnet')
                return 'shutdown'
            time.sleep(1)
            logger.status('start successful')
            node_cnt += 1
        return None
        
    def stop_tsm(self):
        for node in self.tsmanager.keys():
            logger.info(f'stopping tsmanager: {node}')
            stdout,stderr = self.Slurm_starter.stop_process(node,False)
            if stdout != "":
                logger.debug(f'Output from tsmanager: {node} \n {stdout}')
                logger.debug(f'Error from tsmanager: {node} \n {stderr}')
                
    def stop_sts(self):
        for node in self.stservers.keys():
            logger.info(f'stopping stserver: {node}')
            stdout,stderr = self.Slurm_starter.stop_process(node,False)
            if stdout != "":
                logger.debug(f'Output from stserver: {node} \n {stdout}')
                logger.debug(f'Error from stserver: {node} \n {stderr}')
                
    def stop_tsb(self):
        for node in self.tsbuilders.keys():
            logger.info(f'stopping tsbuilder: {node}')
            stdout,stderr = self.Slurm_starter.stop_process(node,False)
            if stdout != "":
                logger.debug(f'Output from tsbuilder: {node} \n {stdout}')
                logger.debug(f'Error from tsbuilder: {node} \n {stderr}')