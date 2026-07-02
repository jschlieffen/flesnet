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
from central_manager import entry_nodes as en
from central_manager import build_nodes as b
from central_manager import Timeslice_forwarding as T
from central_manager import ZIB_Timeslice_forwarding as ZIB_T
import random
import numpy as np

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
    match2 = re.search(r'inet (.*?)/23',content,re.DOTALL)
    content2 = match2.group(1)
    return content2
    
def infiniband_ip(node_id):
    command = 'srun --nodelist=%s -N 1 --ntasks 1 ip a' % (node_id)
    
    #print(node_id)
    try:
        result = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout,stderr = result.communicate()
    except subprocess.CalledProcessError as e:
        logger.error(f'ERROR: {e} Error occurred at reading ips')
        sys.exit(1)
    #print(stdout)
    match = re.search(r'ib0:(.*?)scope global ib0',stdout,re.DOTALL)
    content = match.group(1)
    match2 = re.search(r'inet (.*?)/23',content,re.DOTALL)
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
        self.entry_nodes = {}
        self.build_nodes = {} 
        self.sender_nodes = {}
        self.receiver_nodes = {}
        self.central_manager = {}
        self.input_nodes = {}
        self.output_nodes = {}
        if self.Par_.use_flesnet:
            self.schedule_nodes()
        if self.Par_.ZIB_timesliceforwarding:
            self.assemble_timeslice_forwarding_nodes()
        self.entry_nodes_ips = ""
        self.build_nodes_ips = ""
        self.central_manager_ips = ""
        self.get_ips()
        self.entry_nodes_eth_ips = ""
        self.build_nodes_eth_ips = ""
        self.central_manager_eth_ips = ""
        self.get_eth_ips()
        if self.Par_.activate_timesliceforwarding:
            self.rec2build = []
            #self.assemble_receiving_nodes2build_nodes()
            self.assemble_GSI_timeslice_forwarding_nodes()
        if self.Par_.use_flesnet:
            self.entry_nodes_cls = en.Entry_nodes(self.entry_nodes, self.entry_nodes_ips, self.entry_nodes_eth_ips ,self.build_nodes_ips,self.build_nodes_eth_ips, self.Par_, self.Run_folder)
            self.build_nodes_cls = b.Build_nodes(self.build_nodes, self.entry_nodes_ips,self.entry_nodes_eth_ips,self.build_nodes_ips,self.build_nodes_eth_ips, self.Par_, self.Run_folder)
        if self.Par_.ZIB_timesliceforwarding:
            self.ZIB_timeslice_forwarding_cls = ZIB_T.Timeslice_forwarding_ZIB(self.central_manager, self.central_manager_ips, self.central_manager_eth_ips, 
                                                                        self.output_nodes, self.input_nodes, self.Par_, self.Run_folder)
        if self.Par_.activate_timesliceforwarding:
            self.timeslice_forwarding_cls = T.Timeslice_forwarding(self.sender_nodes, self.receiver_nodes, self.Par_, self.Run_folder)
            
            
    # =============================================================================
    # gets the node list of the current allocations    
    # =============================================================================
    def get_node_list_V2(self):
        node_str = os.environ.get('SLURM_NODELIST')
        node_list = []
        if node_str is None:
            logger.critical('SLURM_NODELIST is not set, Maybe you forget to allocate the nodes')
            sys.exit(1)
        range_pattern = re.findall(r'(.*?)(\d+)-(\d+)', node_str)
        list_pattern = re.findall(r'(.*?)(\d+(?:,\d+)*)', node_str)
        for base, start, end in range_pattern:
            start, end = int(start), int(end)
            if start < 10:
                node_list.extend([f"htc-cmp00{i}" for i in range(start, end + 1)])
            elif start < 100:    
                node_list.extend([f"htc-cmp0{i}" for i in range(start, end + 1)])
            else:
                node_list.extend([f"htc-cmp{i}" for i in range(start, end + 1)])
        for base, numbers in list_pattern:
            num_list = numbers.split(",")
            node_list.extend([f"htc-cmp{num.strip()}" for num in num_list])
        node_list = sorted(set(node_list))
        return node_list
    
    
    def get_node_list_V3(self):
        node_str = os.environ.get('SLURM_NODELIST')
        node_list = []
    
        if node_str is None:
            logger.critical(
                'SLURM_NODELIST is not set, maybe you forgot to allocate the nodes'
            )
            sys.exit(1)
    
        # Match:
        # htc-cmp[001-004]
        # htc-cmp[001,005,010]
        # ccexe0001
        parts = re.findall(r'([a-zA-Z\-]+)(?:\[(.*?)\]|(\d+))', node_str)
    
        for prefix, bracket_content, single_number in parts:
    
            if single_number:
                node_list.append(f"{prefix}{single_number}")
                continue
    
            for item in bracket_content.split(','):
                if '-' in item:
                    start, end = item.split('-')
    
                    width = max(len(start), len(end))
                    start, end = int(start), int(end)
    
                    for i in range(start, end + 1):
                        if prefix == "ccexe" and i > 369:
                            continue
    
                        node_list.append(f"{prefix}{i:0{width}d}")
    
                else:
                    i = int(item)
                    width = len(item)
    
                    if prefix == "ccexe" and i > 369:
                        continue
    
                    node_list.append(f"{prefix}{i:0{width}d}")
        return sorted(set(node_list))
        
    
    def get_node_list(self):
        node_str = os.environ.get("SLURM_NODELIST")
        node_list = []
    
        if node_str is None:
            logger.critical(
                "SLURM_NODELIST is not set, maybe you forgot to allocate the nodes"
            )
            sys.exit(1)
    
        # Matches:
        # htc-cmp[001-004]
        # htc-cmp[001,005,010]
        # ccexe0001
        # en[01-16]
        # en01
        # node[1-8]
        # node01
        parts = re.findall(r"([a-zA-Z\-]+)(?:\[(.*?)\]|(\d+))", node_str)
    
        for prefix, bracket_content, single_number in parts:
    
            if single_number:
                node_list.append(f"{prefix}{single_number}")
                continue
    
            for item in bracket_content.split(","):
                if "-" in item:
                    start, end = item.split("-")
    
                    width = max(len(start), len(end))
                    start, end = int(start), int(end)
    
                    for i in range(start, end + 1):
                        node_list.append(f"{prefix}{i:0{width}d}")
    
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
        for key,val in self.entry_nodes.items():
            self.entry_nodes_eth_ips += val['eth_ip'] + "sep"
        for key,val in self.build_nodes.items():
            self.build_nodes_eth_ips += val['eth_ip'] + "sep"
        for key, val in self.central_manager.items():
            self.central_manager_eth_ips += val['eth_ip']
        
    def get_ips(self):
        for key,val in self.entry_nodes.items():
            self.entry_nodes_ips += val['inf_ip'] + "sep"
        for key,val in self.build_nodes.items():
            self.build_nodes_ips += val['inf_ip'] + "sep"
        if self.use_flescluster and self.is_flescluster:
            self.central_manager_ips += self.Par_.cm_ip
        else:
            for key,val in self.central_manager.items():
                self.central_manager_ips += val['inf_ip']
            
            
    # =============================================================================
    # This function divides the nodes into entry/build and if activated super nodes
    # Furthermore the dict consisting the nodes also contains the index, of the nodes
    # and their ips
    # =============================================================================
    def schedule_nodes(self):
        node_list = self.get_node_list()
        entry_nodes_cnt = 0
        build_nodes_cnt = 0
        if self.Par_.set_node_list == 1:
            self.schedule_nodes_customized(node_list,entry_nodes_cnt, build_nodes_cnt)
        else:
            self.schedule_nodes_randomly(node_list,entry_nodes_cnt, build_nodes_cnt)
        
        Logfile.logfile.entry_nodes_list = self.entry_nodes
        Logfile.logfile.build_nodes_list = self.build_nodes
        #if self.activate_timesliceforwarding:
            
    
        
    # =============================================================================
    # Help function for schedule nodes. Used if the user does not want to set the 
    # entry and build nodes or the given entry and build nodes does not suffices
    # to get the given number of entry and build nodes
    # =============================================================================
    def schedule_nodes_randomly(self,node_list,entry_nodes_cnt, build_nodes_cnt):
        if self.Par_.set_node_list:
            if self.Par_.activate_timesliceforwarding:
                Timeslice_forwarding_nodes = self.Par_.process_nodes_list
            elif self.Par_.ZIB_timesliceforwarding:
                Timeslice_forwarding_nodes = self.Par_.input_node_list + self.Par_.central_manager_list + self.Par_.output_node_list
            else:
                Timeslice_forwarding_nodes = []
        else:
            Timeslice_forwarding_nodes = []
        if len(node_list) < (self.Par_.num_entrynodes - entry_nodes_cnt) + (self.Par_.num_buildnodes - build_nodes_cnt):
            logger.critical(f'Incorrect Number of nodes, expected: '
                            f'{(self.Par_.num_entrynodes - entry_nodes_cnt) + (self.Par_.num_buildnodes - build_nodes_cnt)} '
                            f', got: {len(node_list)} '
                            )
            sys.exit(1)
        for node in node_list:
            if node in Timeslice_forwarding_nodes:
                continue
            node_ip = infiniband_ip(node)
            node_eth_ip = ethernet_ip(node)
            #time.sleep(1)
            if self.Par_.use_infiniband and node_ip is None:
                logger.critical(f'node: {node} does not have infiniband')
                sys.exit(1)
            if entry_nodes_cnt < self.Par_.num_entrynodes and node not in self.Par_.exclude_entry_nodes:
                self.entry_nodes[node] = {
                    'node' : node,
                    'entry_node_idx' : entry_nodes_cnt,
                    'inf_ip' : node_ip,
                    'eth_ip' : node_eth_ip}
                entry_nodes_cnt += 1
            elif build_nodes_cnt < self.Par_.num_buildnodes and node not in self.Par_.exclude_build_nodes:
                self.build_nodes[node] = {
                    'node' : node,
                    'build_node_idx' : build_nodes_cnt,
                    'inf_ip' : node_ip,
                    'eth_ip' : node_eth_ip}
                build_nodes_cnt += 1
        if entry_nodes_cnt < self.Par_.num_entrynodes or build_nodes_cnt < self.Par_.num_buildnodes:
            logger.critical(f'Could not assemble enough entry/build nodes: '
                            f'Expected num. build nodes: {self.Par_.num_buildnodes} got: {build_nodes_cnt} '
                            f'Expected num. entry nodes: {self.Par_.num_entrynodes} got : {entry_nodes_cnt} ' )
            sys.exit(1)
            
            
    # =============================================================================
    # Help function for schedule nodes. Used if the user wants to set the
    # entry nodes and build nodes manually
    # =============================================================================
    def schedule_nodes_customized(self,node_list,entry_nodes_cnt, build_nodes_cnt):
        node_list_remaining = node_list[: ]

        if len(node_list) < self.Par_.num_entrynodes + self.Par_.num_buildnodes:
            logger.critical(f'Incorrect Number of nodes, expected: {self.Par_.num_entrynodes + self.Par_.num_buildnodes}, got: {len(node_list)} ')
            sys.exit(1)
        for node in node_list:
            node_ip = infiniband_ip(node)
            node_eth_ip = ethernet_ip(node)
            #time.sleep(1)
            if self.Par_.use_infiniband and node_ip is None:
                logger.critical(f'node: {node} does not have infiniband')
                sys.exit(1)
            if node in self.Par_.entry_nodes_list and node not in self.Par_.exclude_entry_nodes:
                self.entry_nodes[node] = {
                    'node' : node,
                    'entry_node_idx' : entry_nodes_cnt,
                    'inf_ip' : node_ip,
                    'eth_ip' : node_eth_ip}
                entry_nodes_cnt += 1
                node_list_remaining.remove(node)
            elif node in self.Par_.build_nodes_list and node not in self.Par_.exclude_build_nodes:
                self.build_nodes[node] = {
                    'node' : node,
                    'build_node_idx' : build_nodes_cnt,
                    'inf_ip' : node_ip,
                    'eth_ip' : node_eth_ip}
                build_nodes_cnt += 1
                node_list_remaining.remove(node)
        if entry_nodes_cnt < self.Par_.num_entrynodes or build_nodes_cnt < self.Par_.num_buildnodes:
            logger.warning(
                f'The number of nodes assigned for the entry/build nodes does not match the number '
                f'of entry/build nodes. Expected {self.Par_.num_entrynodes}, got {entry_nodes_cnt} for the ' 
                f'entry nodes. Expected {self.Par_.num_buildnodes}, got {build_nodes_cnt} for the '
                f'build nodes. Proceed by assembling the missing entry/build nodes randomly'
            )
            self.schedule_nodes_randomly(node_list_remaining, entry_nodes_cnt, build_nodes_cnt)
    

    def assemble_GSI_timeslice_forwarding_nodes(self):
        node_list = self.get_node_list()
        unused_nodes = [node for node in node_list if node not in self.entry_nodes and node not in self.build_nodes]

        if self.Par_.use_flesnet:
            self.sender_nodes = self.build_nodes 
        else:
             unused_nodes = self.assemble_GSI_timeslice_forwarding_sender_nodes(unused_nodes)   
        self.assemble_GSI_timeslice_forwarding_receiver_nodes(unused_nodes)
        if not self.Par_.use_flesnet:
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
                if self.Par_.use_flesnet:    
                    sender_node_id = self.Par_.build_nodes_list[idx]
                    sender_node = self.sender_node_id[sender_node_id]
                    used_build_nodes.append(node)
                else:
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

    
    # =============================================================================
    #  will be changed due to changes in the GSI Timeslice-forwarding structures   
    # =============================================================================
    def assemble_receiving_nodes2build_nodes(self):
        node_list = self.get_node_list()
        unused_nodes = [node for node in node_list if node not in self.entry_nodes and node not in self.build_nodes]
        used_build_nodes = []
        
        if len(unused_nodes) < self.Par_.num_buildnodes:
            logger.critical(f"Number of nodes are not sufficient for the Timeslice-forwarding. Number of nodes remaining {len(unused_nodes)}, expected: {self.Par_.num_buildnodes} Shutting down")
            sys.exit(1)
        if self.Par_.set_node_list:
            unused_nodes, used_build_nodes = self.assemble_receiving_nodes2build_nodes_customized(unused_nodes)
    
        cnt = 0
       
        for build_node_id,build_node in self.build_nodes.items():
            if build_node_id not in used_build_nodes:
                if unused_nodes[cnt] not in self.Par_.exclude_process_nodes:
                    self.rec2build.append((unused_nodes[cnt],build_node))
                cnt += 1
                if cnt > len(unused_nodes):
                    logger.critical(f'Could not assemble enough receiver nodes '
                                    f'Expected: {self.Par_.num_buildnodes}, got: {len(self.rec2build)} ')
                    sys.exit(1)
        Logfile.logfile.receiving_node_list = self.rec2build
        if cnt < len(unused_nodes):
            logger.warning(f"There are {len(unused_nodes) - cnt} nodes without any task.")
        if len(self.rec2build) < self.Par_.num_buildnodes:
            logger.critical(f'Could not assemble enough receiver nodes '
                            f'Expected: {self.Par_.num_buildnodes}, got: {len(self.rec2build)} ')
            sys.exit(1)
            
            
    def assemble_receiving_nodes2build_nodes_customized(self,unused_nodes):
        used_build_nodes = []
        unused_nodes_iter = unused_nodes[ :]
        for node in unused_nodes_iter:
            if node not in self.Par_.process_nodes_list or node in self.Par_.exclude_process_nodes:
                continue
            idx = self.Par_.process_nodes_list.index(node)
            self.rec2build.append((node, build_nodes_list[idx][1]) )
            used_build_nodes.append(build_nodes_list[idx][0])
            unused_nodes.remove(node)
        if len(unused_nodes) > 0:
            logger.warning(
                f"They are still remaining build nodes with no receivers. Assign the missing nodes radomly"
            )
        return unused_nodes, used_build_nodes    
            
    def assemble_timeslice_forwarding_nodes_customized(self,unused_nodes):
        unused_nodes_iter = unused_nodes[ :]
        node_list = self.get_node_list()
        input_nodes_cnt = 0
        output_nodes_cnt = 0
        cm_nodes_cnt = 0
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
            elif input_nodes_cnt < self.Par_.num_input_nodes and not self.Par_.use_flesnet and node in self.Par_.input_node_list:
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
                cm_nodes_cnt = self.Par_.num_central_manager
                output_nodes_cnt = self.Par_.num_output_nodes
            else:
                input_nodes_cnt = self.Par_.num_input_nodes
        if self.Par_.use_flesnet:
            self.input_nodes = self.build_nodes 
        unused_nodes = [node for node in node_list if node not in self.entry_nodes and node not in self.build_nodes]
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
        if self.Par_.activate_timesliceforwarding:
            res = self.timeslice_forwarding_cls.start_receivers()
            if res == 'shutdown':
                self.shutdown()
            if not self.Par_.use_flesnet:
                res = self.timeslice_forwarding_cls.start_Senders()
                if res == 'shutdown':
                    self.shutdown()
            else:
                self.timeslice_forwarding_cls.write_Params_Sender()
        elif self.Par_.ZIB_timesliceforwarding:
            res = self.ZIB_timeslice_forwarding_cls.start_cm()

            res = self.ZIB_timeslice_forwarding_cls.start_output_nodes()
            if not self.Par_.use_flesnet:
                res = self.ZIB_timeslice_forwarding_cls.start_input_nodes()
            else:
                self.ZIB_timeslice_forwarding_cls.write_params_input()
            if res == 'shutdown':
                self.shutdown()
        if self.Par_.use_flesnet:
            res = self.entry_nodes_cls.start_flesnet()
            if res == 'shutdown':
                self.shutdown()
            else:    
                res = self.build_nodes_cls.start_flesnet()
                if res == 'shutdown':
                    self.shutdown()


    def shutdown(self):
        if self.Par_.activate_timesliceforwarding:
            self.timeslice_forwarding_cls.stop_timeslice_forwarding()
            if not self.Par_.use_flesnet:
                self.timeslice_forwarding_cls.stop_timeslice_forwarding_sender()
        if self.Par_.ZIB_timesliceforawrding:
            self.ZIB_timeslice_forwarding_cls.start_cm()
            
            self.ZIB_timeslice_forwarding_cls.stop_output_nodes()
            self.ZIB_timeslice_forwarding_cls.stop_input_nodes()
        if self.Par_.use_flesnet:
            self.entry_nodes_cls.stop_flesnet()
            self.build_nodes_cls.stop_flesnet()
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
                self.stop_program()
                sys.exit(1)
        while True:
            time.sleep(1)
    
    
    def robustness_test(self):
        alive_dict = {}
        dead_dict = {}
        if self.Par_.use_flesnet:
            alive_dict['Entry nodes'] = (self.entry_nodes).copy()
            alive_dict['Build nodes'] = (self.build_nodes).copy()
        
        if self.Par_.activate_timesliceforwarding:
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
            alive_dict, dead_dict = self.revieve_nodes_fct_V2(alive_dict, dead_dict)
            return alive_dict,dead_dict
        Node_type = random.choices(keys, weights=weights, k=1)[0]
        to_kill_node = random.choice(list(alive_dict[Node_type].keys()))
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
            'Sender nodes': (self.Par_.num_min_sender_nodes_alive,self.Par_.num_receivers if not self.Par_.use_flesnet else self.Par_.num_buildnodes),
            'Receiver nodes': (self.Par_.num_min_process_nodes_alive,self.Par_.num_receivers if not self.Par_.use_flesnet else self.Par_.num_buildnodes),
            'Input nodes': (self.Par_.num_min_input_nodes_alive,self.Par_.num_input_nodes if not self.Par_.use_flesnet else self.Par_.num_buildnodes),
            'Central Manager': (self.Par_.num_min_central_manager_alive,self.Par_.num_central_manager),
            'Output nodes': (self.Par_.num_min_output_nodes_alive,self.Par_.num_output_nodes),
        }
        weights = []
        keys = []
        for k, (min_needed, _) in custom_adjustments.items():
            subdict = alive_dict.get(k, {})
            if not subdict:
                continue  # skip empty subdicts, weight = 0
            
            current_alive = len(subdict)
            if current_alive >= min_needed and dead_dict.get(k):
                # The closer to the minimum, the higher the weight
                weight = 1 / (current_alive - min_needed + 1)
                weights.append(weight)
                keys.append(k)
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
    # =============================================================================
    def stop_program(self):
        time.sleep(2)
        logger.info('stopping flesnet')
        total_data, avg_data_rate = 0,0
        if self.Par_.use_flesnet:
    
            self.build_nodes_cls.stop_flesnet()
            self.entry_nodes_cls.stop_flesnet()
            if self.Par_.activate_timesliceforwarding:
                self.timeslice_forwarding_cls.stop_timeslice_forwarding()
            if self.Par_.show_total_data:
                total_data, avg_data_rate = self.stop_monitoring()
        else:
            self.ZIB_timeslice_forwarding_cls.stop_central_manager()
            self.ZIB_timeslice_forwarding_cls.stop_input_nodes()
            self.ZIB_timeslice_forwarding_cls.stop_output_nodes()
        return total_data, avg_data_rate
            

    def stop_program(self):
        time.sleep(2)
        logger.info('stopping flesnet')
        total_data, avg_data_rate = 0,0
        if self.Par_.ZIB_timesliceforwarding:
            self.ZIB_timeslice_forwarding_cls.stop_central_manager()
            
            self.ZIB_timeslice_forwarding_cls.stop_output_nodes()
            self.ZIB_timeslice_forwarding_cls.stop_input_nodes()
        elif self.Par_.activate_timesliceforwarding:
            self.timeslice_forwarding_cls.stop_timeslice_forwarding()
            self.timeslice_forwarding_cls.stop_timeslice_forwarding_sender()
        if self.Par_.use_flesnet:
    
            self.build_nodes_cls.stop_flesnet()
            self.entry_nodes_cls.stop_flesnet()
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
            f.write(f"use_flesnet: {self.Par_.use_flesnet}\n")
            f.write(f"use_GSI_TS_forwarding: {self.Par_.activate_timesliceforwarding}\n")
            f.write(f"use_ZIB_TS_forwarding: {self.Par_.ZIB_timesliceforwarding}\n")
            f.write(f"num_entrynodes: {self.Par_.num_entrynodes}\n")
            f.write(f"num_buildnodes: {self.Par_.num_buildnodes}\n")
            f.write(f"num_receivers: {self.Par_.num_receivers}\n")
            f.write(f"num_inputnodes: {self.Par_.num_input_nodes}\n")
            f.write(f"num_outputnodes: {self.Par_.num_output_nodes}\n")
            f.write(f"enable_progess_bar: {self.Par_.enable_progress_bar}\n")
            f.write(f"enable_graph: {self.Par_.enable_graph}\n")

            
            f.close()
        if self.Par_.use_flesnet:
            self.get_monitoring_flesnet_parameters()
        if self.Par_.activate_timesliceforwarding:
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
            
        
    def get_monitoring_flesnet_parameters(self):
        file_names = []
        num_buildnodes = self.Par_.num_buildnodes
        entry_nodes_cnt = 0
        total_file_data = 0
        for entry_node in self.entry_nodes.keys():
            logfile = '../%s/logs/collectl/entry_nodes/entry_node_%s.csv' % (self.Run_folder,entry_node)
            file_data = 0
            file_data = next((tup[2] for tup in self.Par_.input_files if tup[0] == ('entry_node_' + str(entry_nodes_cnt))), None)
            if file_data is None:
                file_data = next((tup[2] for tup in self.Par_.input_files if tup[0] == 'e_default'), None)
            
            file_names.append((logfile,file_data))
            entry_nodes_cnt += 1
            total_file_data += file_data
        if not self.Par_.show_only_entry_nodes:
            for build_node in self.build_nodes.keys():
                logfile = '../%s/logs/collectl/build_nodes/build_node_%s.csv' % (self.Run_folder, build_node)
                file_data = total_file_data/num_buildnodes
                file_names.append((logfile,file_data))
        with open('monitoring/mon_parameters.txt', 'a') as f:
            for logfile, file_data in file_names:
                f.write(f"file_name: {logfile}, {file_data}\n")
                    
    def get_monitoring_GSI_TS_parameters(self):
        filenames = []
        sender_nodes_cnt = 0
        total_file_data = 0
        num_receivers_nodes = self.Par_.num_receivers
        if not self.Par_.use_flesnet:
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
        if not self.Par_.use_flesnet:
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
        print('test')
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
            


    
