#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#Created on Thu Dec 19 15:04:17 2024
"""
@author: jschlieffen
"""
import subprocess
import sys
import os
import time
import docopt
import re
import monitoring as mon
import curses
import signal
from logging_lib.log_msg import *
from logging_lib import logfile_gen as Logfile
from central_manager import Timeslice_forwarding as T
from central_manager import ZIB_Timeslice_forwarding as ZIB_T
from central_manager import flesnet as F
import central_manager.Slurm_starter as ss
import random
import numpy as np
import traceback
# =============================================================================
# This file deals with scheduling the nodes and starting the import processes.
# It deals with starting an experiment and clean up after the end of the experiment
# Note: it is the only file where you can communicate with the different nodes 
#       Thus for debugging purposes it is recommended to look at this file
# =============================================================================

def ethernet_ip(node_id):
    command = 'srun --nodelist=%s -N 1 --ntasks 1 ip a' % (node_id)
    try:
        result = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)    
        stdout,stderr = result.communicate()
    except subprocess.CalledProcessError as e:
        logger.error(f'ERROR: {e} Error occurred at reading ips')
        sys.exit(1)
    match = re.search(r'eth0:(.*?)scope global eth0',stdout,re.DOTALL)
    content = match.group(1)
    match2 = re.search(r'inet (.*?)/',content,re.DOTALL)
    content2 = match2.group(1)
    return content2
    
def infiniband_ip(node_id):
    command = 'srun --nodelist=%s -N 1 --ntasks 1 ip a' % (node_id)
    
    try:
        result = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout,stderr = result.communicate()
    except subprocess.CalledProcessError as e:
        logger.error(f'ERROR: {e} Error occurred at reading ips')
        sys.exit(1)
    match = re.search(r'ib0:(.*?)scope global ib0',stdout,re.DOTALL)
    content = match.group(1)
    match2 = re.search(r'inet (.*?)/',content,re.DOTALL)
    content2 = match2.group(1)
    return content2
            
            
# =============================================================================
# This class is used to firstly schedule the nodes into entry/build nodes, read 
# the ips and then start flesnet on the entry/build nodes via the classes 
# entry_nodes, build_nodes, super_nodes. After doing that it starts the
# either the monotoring if activated or wait until the user says that the 
# experiment is finished.
# =============================================================================
class execution:
    def __init__(self, parameters, Run_folder):
        self.Par_ = parameters
        self.Run_folder = Run_folder
        self.sender_nodes = {}
        self.receiver_nodes = {}
        self.central_manager = {}
        self.input_nodes = {}
        self.output_nodes = {}
        self.tsmanager = {}
        self.stserver = {}
        self.tsbuilder = {}
        self.tsmanager_ip = ""
        if self.Par_.use_flesnet:
            
            self.assemble_flesnet_nodes()
        if self.Par_.ZIB_timesliceforwarding:
            self.assemble_timeslice_forwarding_nodes()
        self.central_manager_ips = ""
        self.get_ips()
        self.central_manager_eth_ips = ""
        self.get_eth_ips()
        self.Slurm_starter = ss.Slurm_starter() 
        if self.Par_.GSI_Timesliceforwarding:
            self.rec2build = []
            #self.assemble_receiving_nodes2build_nodes()
            self.assemble_GSI_timeslice_forwarding_nodes()
        self.ZIB_timeslice_forwarding_cls = None
        if self.Par_.ZIB_timesliceforwarding:
            self.ZIB_timeslice_forwarding_cls = ZIB_T.Timeslice_forwarding_ZIB(self.central_manager, self.central_manager_ips, self.central_manager_eth_ips, 
                                                                        self.output_nodes, self.input_nodes, self.Par_, self.Run_folder, self.Slurm_starter)
        if self.Par_.GSI_Timesliceforwarding:
            self.timeslice_forwarding_cls = T.Timeslice_forwarding(self.sender_nodes, self.receiver_nodes, self.Par_, self.Run_folder, self.Slurm_starter)
        if self.Par_.use_flesnet:
            self.flesnet_cls = F.flesnet(self.tsmanager, self.tsmanager_ip, self.tsbuilder,self.stserver,
                                          self.ZIB_timeslice_forwarding_cls,self.Par_,self.Run_folder, self.Slurm_starter)
    
    def get_node_list(self):
        node_str = os.environ.get("SLURM_NODELIST")
        node_list = []
        if node_str is None:
            logger.critical("SLURM_NODELIST is not set, maybe you forgot to allocate the nodes")
            sys.exit(1)
        parts = re.findall(r"([a-zA-Z\-]+)(?:\[(.*?)\]|(\d+))", node_str)
        for prefix, bracket_content, single_number in parts:
            if single_number:
                node_list.append(f"{prefix}{single_number}")
                continue
            for item in bracket_content.split(","):
                if "-" in item:
                    start, end = item.split("-")
                    width = len(start)
                    start, end = int(start), int(end)
                    for i in range(start, end + 1):
                        if width > 1:
                            node_list.append(f"{prefix}{i:0{width}d}")
                        else:
                            node_list.append(f"{prefix}{i}")
                else:
                    i = int(item)
                    width = len(item)
                    node_list.append(f"{prefix}{i:0{width}d}")
    
        return sorted(set(node_list))
    
    
    # =============================================================================
    # These two functions forms the string of the entry/build node ips 
    # Note: They don't read it out the just forms the string
    # =============================================================================
    def get_eth_ips(self):
        for key, val in self.central_manager.items():
            self.central_manager_eth_ips += val['eth_ip']
        
    def get_ips(self):
        if self.Par_.use_flesnet:
            for key,val in self.tsmanager.items():
                self.tsmanager_ip += val['inf_ip']
        if self.Par_.use_flescluster:
            if self.Par_.is_flescluster and not self.Par_.central_manager_on_flescluster:
                self.central_manager_ips += self.Par_.cm_ip
            elif not self.Par_.is_flescluster and self.Par_.central_manager_on_flescluster:
                self.central_manager_ips += self.Par_.cm_ip
            else:
                for key,val in self.central_manager.items():
                    self.central_manager_ips += val['inf_ip']
        else:
            for key,val in self.central_manager.items():
                self.central_manager_ips += val['inf_ip']
    
    
    def assemble_flesnet_nodes_customized(self,unused_nodes):
        unused_nodes_iter = unused_nodes[ :]
        node_list = self.get_node_list()
        tsm_cnt= 0
        sts_cnt = 0
        tsb_cnt = 0
        for node in unused_nodes_iter:
            node_ip = infiniband_ip(node)
            node_eth_ip = ethernet_ip(node)
            if self.Par_.use_infiniband and node_ip is None:
                logger.critical(f'node: {node} does not have infiniband')
                sys.exit(1)
            if tsm_cnt < self.Par_.num_tsmanager and node in self.Par_.tsmanager_list:
                self.tsmanager[node] = {
                    'node' : node,
                    'tsm_idx' : tsm_cnt,
                    'inf_ip' : node_ip,
                    'eth_ip' : node_eth_ip
                }
                tsm_cnt += 1
                unused_nodes.remove(node)
            elif sts_cnt < self.Par_.num_stserver and node in self.Par_.stserver_list:
                self.stserver[node] = {
                        'node' : node,
                        'sts_idx' : sts_cnt,
                        'inf_ip' : node_ip,
                        'eth_ip' : node_eth_ip
                    }
                sts_cnt += 1
                unused_nodes.remove(node)
            elif tsb_cnt < self.Par_.num_tsbuilder and node in self.Par_.tsbuilder_list:
                self.tsbuilder[node] = {
                        'node' : node,
                        'tsb_idx' : tsb_cnt,
                        'inf_ip' : node_ip,
                        'eth_ip' : node_eth_ip
                    }
                tsb_cnt += 1
                unused_nodes.remove(node)
        return unused_nodes, tsm_cnt, sts_cnt, tsb_cnt
    
    def assemble_flesnet_nodes(self):
        node_list = self.get_node_list()
        tsm_cnt= 0
        sts_cnt = 0
        tsb_cnt = 0
        Timeslice_forwarding_nodes = []
        if self.Par_.set_node_list:
            if self.Par_.GSI_Timesliceforwarding:
                Timeslice_forwarding_nodes = self.Par_.process_nodes_list
            elif self.Par_.ZIB_timesliceforwarding:
                Timeslice_forwarding_nodes = self.Par_.central_manager_list + self.Par_.output_node_list
        unused_nodes = [node for node in node_list]
        if self.Par_.set_node_list:
            unused_nodes,tsm_cnt,sts_cnt,tsb_cnt = self.assemble_flesnet_nodes_customized(unused_nodes)
        for node in unused_nodes:
            if node in Timeslice_forwarding_nodes:
                continue
            node_ip = infiniband_ip(node)
            node_eth_ip = ethernet_ip(node)
            if self.Par_.use_infiniband and node_ip is None:
                logger.critical(f'node: {node} does not have infiniband')
                sys.exit(1)
            if tsm_cnt < self.Par_.num_tsmanager and node not in self.Par_.exclude_tsmanager:
                self.tsmanager[node] = {
                    'node' : node,
                    'tsm_idx' : tsm_cnt,
                    'inf_ip' : node_ip,
                    'eth_ip' : node_eth_ip
                }
                tsm_cnt += 1
            elif sts_cnt < self.Par_.num_stserver and node not in self.Par_.exclude_stserver:
                self.stserver[node] = {
                        'node' : node,
                        'sts_idx' : sts_cnt,
                        'inf_ip' : node_ip,
                        'eth_ip' : node_eth_ip
                    }
                sts_cnt += 1
            elif tsb_cnt < self.Par_.num_tsbuilder and node not in self.Par_.exclude_tsbuilder:
                self.tsbuilder[node] = {
                        'node' : node,
                        'tsb_idx' : tsb_cnt,
                        'inf_ip' : node_ip,
                        'eth_ip' : node_eth_ip
                    }
                tsb_cnt += 1
        Logfile.logfile.stserver_list = self.stserver
        Logfile.logfile.tsmanager_list = self.tsmanager
        Logfile.logfile.tsbuilder_list = self.tsbuilder        
        
    def assemble_GSI_timeslice_forwarding_nodes(self):
        node_list = self.get_node_list()

        unused_nodes = self.assemble_GSI_timeslice_forwarding_sender_nodes(node_list)   
        self.assemble_GSI_timeslice_forwarding_receiver_nodes(unused_nodes)
        Logfile.logfile.sender_node_list = self.sender_nodes
        Logfile.logfile.receiving_node_list = self.receiver_nodes
                    
    def assemble_GSI_timeslice_forwarding_sender_nodes(self,unused_nodes):
        sender_cnt = 0
        unused_nodes_iter = unused_nodes[ :]
        if self.Par_.set_node_list:
            for node in unused_nodes_iter:
                if sender_cnt < self.Par_.num_receivers and node in self.Par_.sender_node_list:
                    node_ip = infiniband_ip(node)
                    node_eth_ip = ethernet_ip(node)
                    #time.sleep(1)
                    if self.Par_.use_infiniband and node_ip is None:
                        logger.critical(f'node: {node} does not have infiniband')
                        sys.exit(1)
                    self.sender_nodes[node] = {
                        'node' : node,
                        'sender_idx' : sender_cnt,
                        'inf_ip' : node_ip,
                        'eth_ip' : node_eth_ip}
                    sender_cnt += 1
                    unused_nodes.remove(node)
        if sender_cnt < self.Par_.num_receivers:
            if self.Par_.set_node_list:
                logger.warning(f'The number of nodes assigned for the sender nodes does not match the number '
                                f'of sender nodes. Expected {self.Par_.num_receivers}, got {sender_cnt}'
                                f'Proceed by assembling the missing entry/build nodes randomly'
                            )
            unused_nodes_iter = unused_nodes[ :]
            for node in unused_nodes_iter: 
                if sender_cnt < self.Par_.num_receivers:
                    node_ip = infiniband_ip(node)
                    node_eth_ip = ethernet_ip(node)
                    #time.sleep(1)
                    if self.Par_.use_infiniband and node_ip is None:
                        logger.critical(f'node: {node} does not have infiniband')
                        sys.exit(1)
                    self.sender_nodes[node] = {
                        'node' : node,
                        'sender_idx' : sender_cnt,
                        'inf_ip' : node_ip,
                        'eth_ip' : node_eth_ip}
                    sender_cnt += 1
                    unused_nodes.remove(node)
        return unused_nodes
    
    
    def assemble_GSI_timeslice_forwarding_receiver_nodes(self,unused_nodes):
        receiver_cnt = 0
        unused_nodes_iter = unused_nodes [ :]
        used_build_nodes = []
        if self.Par_.set_node_list:
            for node in unused_nodes_iter:
                if node not in self.Par_.process_nodes_list or node in self.Par_.exclude_process_nodes:
                    continue
                idx = self.Par_.process_nodes_list.index(node)
                sender_node_id = self.sender_node_list[idx]
                sender_node = self.sender_node_id[sender_node_id]
                self.receiver_nodes[node] = {
                        'node' : rec_node,
                        'sender_node' : node
                    }
                receiver_cnt += 1
                unused_nodes.remove(node)
        for node_id, node in self.sender_nodes.items():
            rec_node = unused_nodes[receiver_cnt]
            if rec_node not in self.Par_.exclude_process_nodes or node_id not in used_build_nodes:
                self.receiver_nodes[rec_node] = {
                        'node' : rec_node,
                        'sender_node' : node
                    }
                receiver_cnt += 1
                if receiver_cnt > len(unused_nodes):
                    logger.critical(f'Could not assemble enough receiver nodes'
                                    f'Expected: {self.Par_.num_buildnodes}, got: {len(self.rec2build)}')
                    sys.exit(1)

    
    def assemble_timeslice_forwarding_nodes_customized(self,unused_nodes):
        unused_nodes_iter = unused_nodes[ :]
        node_list = self.get_node_list()
        input_nodes_cnt = 0
        output_nodes_cnt = 0
        cm_nodes_cnt = 0
        if self.Par_.use_flescluster:
            if self.Par_.is_flescluster:
                output_nodes_cnt = self.Par_.num_output_nodes
                if not self.Par_.central_manager_on_flescluster:
                    cm_nodes_cnt = self.Par_.num_central_manager
            else:
                input_nodes_cnt = self.Par_.num_input_nodes
                if self.Par_.central_manager_on_flescluster:
                    cm_nodes_cnt = self.Par_.num_central_manager
        for node in unused_nodes_iter:

            if cm_nodes_cnt < self.Par_.num_central_manager and node in self.Par_.central_manager_list:            
                node_ip = infiniband_ip(node)
                node_eth_ip = ethernet_ip(node)
                #time.sleep(1)
                if self.Par_.use_infiniband and node_ip is None:
                    logger.critical(f'node: {node} does not have infiniband')
                    sys.exit(1)
                self.central_manager[node] = {
                        'node' : node, 
                        'cm_idx' : cm_nodes_cnt,
                        'inf_ip' : node_ip,
                        'eth_ip' : node_eth_ip
                    }
                cm_nodes_cnt += 1                
                unused_nodes.remove(node)
            elif input_nodes_cnt < self.Par_.num_input_nodes and node in self.Par_.input_node_list:
                node_ip = infiniband_ip(node)
                node_eth_ip = ethernet_ip(node)
                #time.sleep(1)
                if self.Par_.use_infiniband and node_ip is None:
                    logger.critical(f'node: {node} does not have infiniband')
                    sys.exit(1)
                self.input_nodes[node] = {
                        'node' : node,
                        'input_node_idx' : input_nodes_cnt,
                        'inf_ip' : node_ip,
                        'eth_ip' : node_eth_ip
                    }
                input_nodes_cnt += 1
                unused_nodes.remove(node)
            elif output_nodes_cnt < self.Par_.num_output_nodes and node in self.Par_.output_node_list:
                node_ip = infiniband_ip(node)
                node_eth_ip = ethernet_ip(node)
                #time.sleep(1)
                if self.Par_.use_infiniband and node_ip is None:
                    logger.critical(f'node: {node} does not have infiniband')
                    sys.exit(1)
                self.output_nodes[node] = {
                        'node' : node,
                        'output_node_idx' : output_nodes_cnt,
                        'inf_ip' : node_ip,
                        'eth_ip' : node_eth_ip
                    }
                output_nodes_cnt += 1
                unused_nodes.remove(node)
        return unused_nodes,input_nodes_cnt,cm_nodes_cnt,output_nodes_cnt
        
    def assemble_timeslice_forwarding_nodes(self):
        node_list = self.get_node_list()
        input_nodes_cnt = 0
        output_nodes_cnt = 0
        cm_nodes_cnt = 0
        if self.Par_.use_flescluster:
            if self.Par_.is_flescluster:
                output_nodes_cnt = self.Par_.num_output_nodes
                if not self.Par_.central_manager_on_flescluster:
                    cm_nodes_cnt = self.Par_.num_central_manager
            else:
                input_nodes_cnt = self.Par_.num_input_nodes
                if self.Par_.central_manager_on_flescluster:
                    cm_nodes_cnt = self.Par_.num_central_manager
        unused_nodes = [node for node in node_list if node not in self.tsmanager and node not in self.stserver and node not in self.tsbuilder]
        if self.Par_.set_node_list:
            unused_nodes,input_nodes_cnt,cm_nodes_cnt,output_nodes_cnt = self.assemble_timeslice_forwarding_nodes_customized(unused_nodes)
        for node in unused_nodes:
            node_ip = infiniband_ip(node)
            node_eth_ip = ethernet_ip(node)
            #time.sleep(1)
            if self.Par_.use_infiniband and node_ip is None:
                logger.critical(f'node: {node} does not have infiniband')
                sys.exit(1)
            if cm_nodes_cnt < self.Par_.num_central_manager and node not in self.Par_.exclude_central_manager:
                if self.Par_.use_flescluster:
                    logger.info(f"central manager: {node} has ip: {node_ip}")
                self.central_manager[node] = {
                        'node' : node,
                        'cm_idx' : cm_nodes_cnt,
                        'inf_ip' : node_ip,
                        'eth_ip' : node_eth_ip
                    }
                cm_nodes_cnt += 1
            elif input_nodes_cnt < self.Par_.num_input_nodes and not self.Par_.use_flesnet and node not in self.Par_.exclude_input_nodes: 
                self.input_nodes[node] = {
                        'node' : node,
                        'input_node_idx' : input_nodes_cnt,
                        'inf_ip' : node_ip,
                        'eth_ip' : node_eth_ip
                    }
                input_nodes_cnt += 1
            elif output_nodes_cnt < self.Par_.num_output_nodes and node not in self.Par_.exclude_output_nodes:
                self.output_nodes[node] = {
                        'node' : node,
                        'output_node_idx' : output_nodes_cnt,
                        'inf_ip' : node_ip,
                        'eth_ip' : node_eth_ip
                    }
                output_nodes_cnt += 1
        Logfile.logfile.input_node_list = self.input_nodes
        Logfile.logfile.cm_list = self.central_manager
        Logfile.logfile.output_node_list = self.output_nodes
                
    # =============================================================================
    # This function starts flesnet and partly checks if the start was successful  
    # =============================================================================
    def start_Flesnet(self):
        if self.Par_.use_flesnet:
            res = self.flesnet_cls.start_tsm()
            if res == 'shutdown':
                self.shutdown()
            res = self.flesnet_cls.start_sts()
            if res == 'shutdown':
                self.shutdown()
            res = self.flesnet_cls.start_tsb()
            if res == 'shutdown':
                self.shutdown()
        if self.Par_.GSI_Timesliceforwarding:
            res = self.timeslice_forwarding_cls.start_receivers()
            if res == 'shutdown':
                self.shutdown()
            res = self.timeslice_forwarding_cls.start_Senders()
            if res == 'shutdown':
                self.shutdown()
        elif self.Par_.ZIB_timesliceforwarding:
            res = self.ZIB_timeslice_forwarding_cls.start_cm()
            if res == 'shutdown':
                self.shutdown()
            res = self.ZIB_timeslice_forwarding_cls.start_output_nodes()
            if res == 'shutdown':
                self.shutdown()
            if not self.Par_.use_flesnet:
                res = self.ZIB_timeslice_forwarding_cls.start_input_nodes()
                if res == 'shutdown':
                    self.shutdown()


    def shutdown(self):
        if self.Par_.use_flesnet:
            self.flesnet_cls.stop_tsm()
            self.flesnet_cls.stop_sts()
            self.flesnet_cls.stop_tsb()
        if self.Par_.GSI_Timesliceforwarding:
            self.timeslice_forwarding_cls.stop_timeslice_forwarding()
            self.timeslice_forwarding_cls.stop_timeslice_forwarding_sender()
        if self.Par_.ZIB_timesliceforawrding:
            self.ZIB_timeslice_forwarding_cls.start_cm()
            
            self.ZIB_timeslice_forwarding_cls.stop_output_nodes()
            if not self.Par_.use_flesnet:
                self.ZIB_timeslice_forwarding_cls.stop_input_nodes()
        sys.exit(1)
        
                
    # =============================================================================
    # This function either starts the monotoring if activated or it just waits 
    # until the user stops the program
    # TODO: rename function
    # =============================================================================
    def stop_via_ctrl_c(self):
        time.sleep(2)
        logger.success('flesnet launched successfully')
        if self.Par_.show_total_data:
            #TODO: check if signal handling error still appears.
            try: 
                self.monitoring()
            except Exception as e:
                logger.critical(f'Error {e} occured during monotoring. Terminating',exc_info=True)
                self.stop_program()
                sys.exit(1)
        if self.Par_.activate_robustness_test:
            try:
                self.robustness_test()
            except Exception as e:
                logger.critical(f'Error {e} occured during robustness test V2. Terminating')
                logger.debug(f'expanded debug message: {traceback.format_exc()}')
                self.stop_program()
                sys.exit(1)
        while True:
            time.sleep(1)
            
    def write_interface_params(self):
        with open('tmp/interface/interface_params.txt','w') as f:
            f.write(f"use_GSI_TS_forwarding: {self.Par_.GSI_Timesliceforwarding}\n")
            f.write(f"use_ZIB_TS_forwarding: {self.Par_.ZIB_timesliceforwarding}\n")
            f.write(f"num_receivers: {self.Par_.num_receivers}\n")
            f.write(f"num_inputnodes: {self.Par_.num_input_nodes*self.Par_.num_sender_per_node}\n")
            f.write(f"num_outputnodes: {self.Par_.num_output_nodes}\n")
            f.write(f"num_cm: {self.Par_.num_central_manager}\n")
            f.close()
        if self.Par_.GSI_Timesliceforwarding:
            self.get_interface_GSI_TS_parameters()
        if self.Par_.ZIB_timesliceforwarding:
            self.get_interface_ZIB_TS_parameters()
            
            
    def get_interface_GSI_TS_parameters(self):
        filenames = []
        sender_nodes_cnt = 0
        total_file_data = 0
        num_receivers_nodes = self.Par_.num_receivers
        for sender_node in self.sender_nodes.keys():
            logfile = '../%s/logs/tsclient/sender_node_%s.log' % (self.Run_folder,sender_node)
            file_data = 0
            #file_data = next((tup))
            file_data = next((tup[2] for tup in self.Par_.input_tsa_files if tup[0] == ('input_node_' + str(sender_nodes_cnt))), None)
            if file_data is None:
                file_data = next((tup[2] for tup in self.Par_.input_tsa_files if tup[0] == 'i_default'), None)
            filenames.append((logfile,file_data))
            sender_nodes_cnt += 1
            total_file_data += file_data
        for receiver_node in self.receiver_nodes.keys():
            logfile = '../%s/logs/tsclient/receiving_node_%s.log' % (self.Run_folder,receiver_node)
            filenames.append((logfile,total_file_data/num_receivers_nodes))
        with open('tmp/interface/interface_params.txt','a') as f:
            for logfile, file_data in filenames:
                f.write(f"file_name: {logfile}, {file_data}\n")
    
    #TODO:fix file data
    #TODO:fix filename input nodes
    def get_interface_ZIB_TS_parameters(self):
        filenames = []
        input_nodes_cnt = 0
        total_file_data = 0
        for input_node in self.input_nodes.keys():
            for i in range(1,self.Par_.num_sender_per_node+1):
                logfile = "%s/logs/timeslice_forwarding/input_nodes/input_node_%s_%s.log" % (self.Run_folder,input_node,i)
                file_data = 0
                print(self.Par_.input_tsa_files)
                #file_data = next((tup[2] for tup in self.Par_.input_tsa_files if tup[0] == ('input_node_' + str(input_nodes_cnt))), None)
                input_file = next(
                    (tup[1] for tup in self.Par_.input_tsa_files
                     if tup[0] == 'input_node_0'),
                    []
                )
            
                input_by_index = {item[0]: item for item in input_file}
            
                # Fill missing sender indices with the default
                input_file = [
                    input_by_index.get(
                        index,
                        (index, self.Par_.default_path, self.Par_.default_data_size)
                    )
                    for index in range(1, self.Par_.num_sender_per_node + 1)
                ]
                if file_data is None:
                    file_data = next((tup[2] for tup in self.Par_.input_tsa_files if tup[0] == 'i_default'), None)
                filenames.append((logfile,file_data))
                input_nodes_cnt += 1
                total_file_data += file_data
        for output_node in self.output_nodes.keys():
            logfile = "%s/logs/timeslice_forwarding/output_nodes/output_node_%s.log" % (self.Run_folder,output_node)
            filenames.append((logfile,total_file_data/self.Par_.num_output_nodes))
        for cm in self.central_manager.keys():
            logfile = "%s/logs/timeslice_forwarding/central_manager/central_manager_%s.log" % (self.Run_folder,cm)
            filenames.append((logfile,total_file_data/self.Par_.num_central_manager))
        with open('tmp/interface/interface_params.txt','a') as f:
            for logfile,file_data in filenames:
                f.write(f'file_name: {logfile}, {file_data}\n')
            
    def wait_for_commands(self):
        try:
            self.write_interface_params()
            self.write_response('0', 'starting')
            msg = ''
            prev_msg = ''
            while True:
                time.sleep(0.1)
                
                try:
                    with open('tmp/interface/interface_commands.txt','r') as f:
                        msg = f.read().strip()
                        #ode, action = line.split(": ")
                        f.close()
                except FileNotFoundError:
                    msg = ""
                if not ':' in msg:
                    continue
                node_type, node,process,action = msg.split(': ')
                if msg == prev_msg:
                    continue
                if action == 'kill':
                    logger.info(f'killing node: {node_type} {node}')
                    self.kill_node(node_type, node, process)
                    self.write_response(node, action)
                    prev_msg = msg
                    logger.info('done kill')
                elif action == 'revive':
                    logger.info(f'revive node: {node_type} {node}')
                    self.revive_node(node_type,node, process)
                    self.write_response(node,action)
                    prev_msg = msg
                    logger.info('done revive')
        except Exception as e:
            logger.critical(f'Error {e} occured during interface comm. Terminating')
            logger.debug(f'expanded debug message: {traceback.format_exc()}')
            self.stop_program()
            sys.exit(1)

    def write_response(self,node,action):
        with open('tmp/interface/interface_response.txt','w') as f:
            f.write(f'{node}: done {action}')
            f.close()    
            
            
    def kill_node(self,Node_type,to_kill_node,process):
        if Node_type == 'Central manager':
            self.Slurm_starter.kill_process(to_kill_node,process)
        else:
            self.Slurm_starter.kill_process(to_kill_node,process)

    def revive_node(self,Node_type,to_revive_node,process):
        if Node_type == 'Central manager':
            self.Slurm_starter.revieve_process(to_revive_node,process)
        else:
            self.Slurm_starter.revieve_process(to_revive_node,process)
                        
            
            
    def robustness_test(self):
        alive_dict = {}
        dead_dict = {}
        
        if self.Par_.GSI_Timesliceforwarding:
            alive_dict['Sender nodes'] = self.sender_nodes.copy()
            alive_dict['Receiver nodes'] = self.receiver_nodes.copy()
        
        if self.Par_.ZIB_timesliceforwarding:
            alive_dict['Input nodes'] = self.input_nodes.copy()
            alive_dict['Central Manager'] = self.central_manager.copy()
            alive_dict['Output nodes'] = self.output_nodes.copy()
        dead_dict = {key: {} for key in alive_dict}
        while True:
            td = self.Par_.timer_for_kills.total_seconds()
            sleep_val = np.random.poisson(td)
            time.sleep(sleep_val)
            kill_or_revive = random.choice([True,False])
            if kill_or_revive:
                alive_dict,dead_dict = self.kill_nodes_fct(alive_dict,dead_dict)
            else:
                alive_dict,dead_dict = self.revieve_nodes_fct(alive_dict, dead_dict)
                
    def kill_nodes_fct(self,alive_dict,dead_dict):
        custom_adjustments = {
            'Entry nodes': self.Par_.num_min_entry_nodes_alive,
            'Build nodes': self.Par_.num_min_build_nodes_alive,
            'Sender nodes': self.Par_.num_min_sender_nodes_alive,
            'Receiver nodes': self.Par_.num_min_process_nodes_alive,  
            'Input nodes': self.Par_.num_min_input_nodes_alive,
            'Central Manager': self.Par_.num_min_central_manager_alive,
            'Output nodes': self.Par_.num_min_output_nodes_alive
        }

        weights = [max(len(alive_dict[k]) - custom_adjustments.get(k, 0), 0) for k in alive_dict]
        keys = list(alive_dict.keys())
        if all(w == 0 for w in weights):
            alive_dict, dead_dict = self.revieve_nodes_fct(alive_dict, dead_dict)
            return alive_dict,dead_dict
        Node_type = random.choices(keys, weights=weights, k=1)[0]
        to_kill_node = random.choice(list(alive_dict[Node_type].keys()))
        self.kill_node(Node_type,to_kill_node)
        if Node_type == 'Entry nodes':
            self.entry_nodes_cls.kill_process(to_kill_node)
        elif Node_type == 'Build nodes':
            self.build_nodes_cls.kill_process(to_kill_node)
        elif Node_type == 'Sender nodes':
            self.timeslice_forwarding_cls.kill_process_Sender(to_kill_node)
        elif Node_type == 'Receiver nodes':
            self.timeslice_forwarding_cls.kill_process(to_kill_node)
        elif Node_type == 'Input nodes':
            self.ZIB_timeslice_forwarding_cls.kill_input_node(to_kill_node)
        elif Node_type == 'Central Manager':
            self.ZIB_timeslice_forwarding_cls.kill_central_manager(to_kill_node)
        elif Node_type == 'Output nodes':
            self.ZIB_timeslice_forwarding_cls.kill_output_node(to_kill_node)   
        dead_dict[Node_type][to_kill_node] = alive_dict[Node_type][to_kill_node]
        alive_dict[Node_type].pop(to_kill_node)
        return alive_dict,dead_dict

 
        
    def revieve_nodes_fct(self,alive_dict,dead_dict):
        custom_adjustments = {
            'Entry nodes': (self.Par_.num_min_entry_nodes_alive,self.Par_.num_entrynodes),
            'Build nodes': (self.Par_.num_min_build_nodes_alive,self.Par_.num_buildnodes),
            'Sender nodes': (self.Par_.num_min_sender_nodes_alive,self.Par_.num_receivers),
            'Receiver nodes': (self.Par_.num_min_process_nodes_alive,self.Par_.num_receivers),
            'Input nodes': (self.Par_.num_min_input_nodes_alive,self.Par_.num_input_nodes),
            'Central Manager': (self.Par_.num_min_central_manager_alive,self.Par_.num_central_manager),
            'Output nodes': (self.Par_.num_min_output_nodes_alive,self.Par_.num_output_nodes),
        }
        weights = []
        keys = []
        print('dead dict: ',dead_dict)
        print('custom adjustments: ',custom_adjustments)
        for k, (min_needed, _) in custom_adjustments.items():
            subdict = alive_dict.get(k, {})

            
            current_alive = len(subdict)
            print('current_alive: ', current_alive)
            if dead_dict.get(k):
                print('test123')
                # The closer to the minimum, the higher the weight
                weight = 1 / (current_alive - min_needed + 1)
                weights.append(weight)
                keys.append(k)
                print(k)
        print(keys)
        if not keys:
            alive_dict,dead_dict = self.kill_nodes_fct(alive_dict, dead_dict)
            return alive_dict,dead_dict
        Node_type = random.choices(keys, weights=weights, k=1)[0]
        to_revive_node = random.choice(list(dead_dict[Node_type].keys()))
        if Node_type == 'Entry nodes':
            self.entry_nodes_cls.revieve_process(to_revive_node)
        elif Node_type == 'Build nodes':
            self.build_nodes_cls.revieve_process(to_revive_node)
        elif Node_type == 'Sender nodes':
            self.timeslice_forwarding_cls.revieve_process_Sender(to_revive_node)
        elif Node_type == 'Receiver nodes':
            self.timeslice_forwarding_cls.revieve_process(to_revive_node)
        elif Node_type == 'Input nodes':
            self.ZIB_timeslice_forwarding_cls.revieve_input_node(to_revive_node)
        elif Node_type == 'Central Manager':
            self.ZIB_timeslice_forwarding_cls.revieve_central_manager(to_revive_node)
        elif Node_type == 'Output nodes':
            self.ZIB_timeslice_forwarding_cls.revieve_output_node(to_revive_node)
        alive_dict[Node_type][to_revive_node] = dead_dict[Node_type][to_revive_node]
        dead_dict[Node_type].pop(to_revive_node)
        return alive_dict,dead_dict
    
    

            
    # =============================================================================
    # Stops the experiment and kills every process connected    
    # ============================================================================
            

    def stop_program(self):
        time.sleep(2)
        logger.info('stopping flesnet')
        total_data, avg_data_rate = 0,0
        if self.Par_.use_flesnet:
            self.flesnet_cls.stop_tsm()
            self.flesnet_cls.stop_sts()
            self.flesnet_cls.stop_tsb()
        if self.Par_.GSI_Timesliceforwarding:
            self.timeslice_forwarding_cls.stop_timeslice_forwarding()
            self.timeslice_forwarding_cls.stop_timeslice_forwarding_sender()
        if self.Par_.ZIB_timesliceforwarding:
            self.ZIB_timeslice_forwarding_cls.stop_central_manager()
            
            self.ZIB_timeslice_forwarding_cls.stop_output_nodes()
            if not self.Par_.use_flesnet:
                self.ZIB_timeslice_forwarding_cls.stop_input_nodes()
        if self.Par_.show_total_data:
            total_data, avg_data_rate = self.stop_monitoring()
        return total_data, avg_data_rate


    # =============================================================================
    # Starts the monotoring. The monitoring is started inside a tmux session.
    # If one wants to access it, open a new terminal and go into the login node.
    # Then execute
    #   tmux attach-session -t monitoring
    # If the session is no longer needed, execute
    #   tmux kill-session -t monitoring
    # TODO: use collectl rather than flesnet logs...
    # =============================================================================
        
# =============================================================================
# =============================================================================
# #     BAUSTELLE
# =============================================================================
# =============================================================================
    def monitoring(self):
        file_names = []
        nodes_cnt = {}
        with open('monitoring/mon_parameters.txt','w') as f:
            f.write(f"use_GSI_TS_forwarding: {self.Par_.GSI_Timesliceforwarding}\n")
            f.write(f"use_ZIB_TS_forwarding: {self.Par_.ZIB_timesliceforwarding}\n")
            f.write(f"num_entrynodes: 0\n")
            f.write(f"num_buildnodes: 0\n")
            f.write(f"num_receivers: {self.Par_.num_receivers}\n")
            f.write(f"num_inputnodes: {self.Par_.num_input_nodes}\n")
            f.write(f"num_outputnodes: {self.Par_.num_output_nodes}\n")
            f.write(f"enable_progess_bar: {self.Par_.enable_progress_bar}\n")
            f.write(f"enable_graph: {self.Par_.enable_graph}\n")

            
            f.close()
        if self.Par_.GSI_Timesliceforwarding:
            self.get_monitoring_GSI_TS_parameters()
        if self.Par_.ZIB_timesliceforwarding:
            self.get_monitoring_ZIB_TS_parameters()
        logger.info('starting monitoring')
        session_name = 'monitoring'
        session_exists = subprocess.run(
            ['tmux', 'has-session', '-t', session_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        if session_exists.returncode != 0:
            subprocess.run(['tmux', 'new-session', '-d', '-s', session_name])
        cmd = "monitoring/monitoring_launcher.sh"
        subprocess.run(['tmux', 'send-keys', '-t', session_name, cmd,'Enter'])   
            
                    
    def get_monitoring_GSI_TS_parameters(self):
        filenames = []
        sender_nodes_cnt = 0
        total_file_data = 0
        num_receivers_nodes = self.Par_.num_receivers
        for sender_node in self.sender_nodes.keys():
            logfile = '../%s/logs/collectl/tsclient/sender_node_%s.csv' % (self.Run_folder,sender_node)
            file_data = 0
            #file_data = next((tup))
            file_data = next((tup[2] for tup in self.Par_.input_tsa_files if tup[0] == ('input_node_' + str(sender_nodes_cnt))), None)
            if file_data is None:
                file_data = next((tup[2] for tup in self.Par_.input_tsa_files if tup[0] == 'i_default'), None)
            filenames.append((logfile,file_data))
            sender_nodes_cnt += 1
            total_file_data += file_data
        for receiver_node in self.receiver_nodes.keys():
            logfile = '../%s/logs/collectl/tsclient/receiving_node_%s.csv' % (self.Run_folder,receiver_node)
            filenames.append((logfile,total_file_data/num_receivers_nodes))
        with open('monitoring/mon_parameters.txt','a') as f:
            for logfile, file_data in filenames:
                f.write(f"file_name: {logfile}, {file_data}\n")
            
        
    def get_monitoring_ZIB_TS_parameters(self):
        filenames = []
        input_nodes_cnt = 0
        total_file_data = 0
        for input_node in self.input_nodes.keys():
            logfile = "../%s/logs/collectl/timeslice_forwarding/input_nodes/input_node_%s.csv" % (self.Run_folder,input_node)
            file_data = 0
            file_data = next((tup[2] for tup in self.Par_.input_tsa_files if tup[0] == ('input_node_' + str(input_nodes_cnt))), None)
            if file_data is None:
                file_data = next((tup[2] for tup in self.Par_.input_tsa_files if tup[0] == 'i_default'), None)
            filenames.append((logfile,file_data))
            input_nodes_cnt += 1
            total_file_data += file_data
        for output_node in self.output_nodes.keys():
            logfile = "../%s/logs/collectl/timeslice_forwarding/output_nodes/output_node_%s.csv" % (self.Run_folder,output_node)
            filenames.append((logfile,total_file_data/self.Par_.num_output_nodes))
        with open('monitoring/mon_parameters.txt','a') as f:
            for logfile,file_data in filenames:
                f.write(f'file_name: {logfile}, {file_data}\n')

    
    # =============================================================================
    # stops the monitoring inside the tmux session. The session itself is not 
    # killed. So one can stay inside the session for future test runs.
    # =============================================================================
    def stop_monitoring(self):
        try:
            logger.info(f"killing monitoring process")
            session_name = 'monitoring'
            cmd = 'C-c'
            subprocess.run(['tmux', 'send-keys', '-t', session_name, cmd,'Enter'])
            logger.success("Process killed")
        except Exception as e:
            logger.error(f"Could not kill process: {e}")
        time.sleep(1)
        with open('monitoring/monitoring.log', 'r') as log_file:
            contents = log_file.read()
        total_data = float(re.search(r'total_data: \s*([0-9.]+)', contents).group(1))
        avg_data_rate = float(re.search(r'avg_data_rate: \s*([0-9.]+)', contents).group(1))
        return total_data, avg_data_rate
            


    
