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
from central_manager import super_nodes as s
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


# =============================================================================
# TODOs:                                                                            STATUS:
#        1. implement overlapping nodes timeslice-forwarding                        Prob. will not be implemented
#        2. implement nodelist timeslice-forwarding                                 DONE
#        3. implement set kill list timeslice-forwarding                            DONE
#        4. collectl for monotoring
#        5. check if weird signal handler behavior still appears now for mon.
#        6. check for bottleneck(Performance for flesnet is bad...)                 only seems to appear, when timeslice-forwarding is active. Check if there is a better way ... it is not ...
#        7. Make the node output Debug output                                       DONE
#        8. Add log level                                                           DONE
#        9. restructer input output to make it complained with libfabric
#        10. make a way to exclude nodes                                            DONE
#        11. adjust setup check to new params
#        12. clean up
#        13. full test, that EVERYTHING works as intended
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
    #print(node_id)
    command = 'srun --nodelist=%s -N 1 --ntasks 1 ip a' % (node_id)
    try:
        result = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout,stderr = result.communicate()
    except subprocess.CalledProcessError as e:
        logger.error(f'ERROR: {e} Error occurred at reading ips')
        sys.exit(1)
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
    def __init__(self, parameters):
        self.Par_ = parameters

        self.entry_nodes = {}
        self.build_nodes = {} 
        self.overlap_nodes = {}
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
            self.assemble_receiving_nodes2build_nodes()
        if self.Par_.use_flesnet:
            self.entry_nodes_cls = en.Entry_nodes(self.entry_nodes, self.entry_nodes_ips, self.entry_nodes_eth_ips ,self.build_nodes_ips,self.build_nodes_eth_ips, self.Par_)
            self.build_nodes_cls = b.Build_nodes(self.build_nodes, self.entry_nodes_ips,self.entry_nodes_eth_ips,self.build_nodes_ips,self.build_nodes_eth_ips, self.Par_)
            self.super_nodes_cls = s.Super_nodes(self.overlap_nodes, self.entry_nodes_ips,self.entry_nodes_eth_ips,self.build_nodes_ips,self.build_nodes_eth_ips, self.Par_)
        if self.Par_.ZIB_timesliceforwarding:
            self.ZIB_timeslice_forwarding_cls = ZIB_T.Timeslice_forwarding_ZIB(self.central_manager, self.central_manager_ips, self.central_manager_eth_ips, 
                                                                        self.output_nodes, self.input_nodes, self.Par_)
        if self.Par_.activate_timesliceforwarding:
            self.timeslice_forwarding_cls = T.Timeslice_forwarding(self.rec2build, self.Par_)
            
            
    # =============================================================================
    # gets the node list of the current allocations    
    # =============================================================================
    def get_node_list(self):
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
        #print(node_list)
        return node_list
    
        
    # =============================================================================
    # These two functions forms the string of the entry/build node ips 
    # Note: They don't read it out the just forms the string
    # =============================================================================
    def get_eth_ips(self):
        if self.Par_.overlap_usage_of_nodes:
            for key,val in self.overlap_nodes.items():
                self.entry_nodes_eth_ips += val['eth_ip'] + "sep"
                self.build_nodes_eth_ips += val['eth_ip'] + "sep"
        for key,val in self.entry_nodes.items():
            self.entry_nodes_eth_ips += val['eth_ip'] + "sep"
        for key,val in self.build_nodes.items():
            self.build_nodes_eth_ips += val['eth_ip'] + "sep"
        for key, val in self.central_manager.items():
            self.central_manager_eth_ips += val['eth_ip']
        
    def get_ips(self):
        if self.Par_.overlap_usage_of_nodes:
            for key,val in self.overlap_nodes.items():
                self.entry_nodes_ips += val['inf_ip'] + "sep"
                self.build_nodes_ips += val['inf_ip'] + "sep"
        for key,val in self.entry_nodes.items():
            self.entry_nodes_ips += val['inf_ip'] + "sep"
        for key,val in self.build_nodes.items():
            self.build_nodes_ips += val['inf_ip'] + "sep"
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
        Logfile.logfile.overlap_nodes_list = self.overlap_nodes
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
        if self.Par_.overlap_usage_of_nodes:
            if len(node_list) < max(self.Par_.num_entrynodes - entry_nodes_cnt, self.Par_.num_buildnodes - build_nodes_cnt):
                logger.critical(f'Incorrect Number of nodes, expected:'
                                f'{(self.Par_.num_entrynodes - entry_nodes_cnt) + (self.Par_.num_buildnodes - build_nodes_cnt)}'
                                f', got: {len(node_list)} '
                                )
                sys.exit(1)
            
            for node in node_list:
                node_ip = infiniband_ip(node)
                node_eth_ip = ethernet_ip(node)
                time.sleep(1)
                if node in Timeslice_forwarding_nodes:
                    continue
                if entry_nodes_cnt < self.Par_.num_entrynodes and build_nodes_cnt < self.Par_.num_buildnodes and node not in self.Par_.exclude_entry_nodes + self.Par_.exclude_build_nodes:
                    self.overlap_nodes[node] = {
                        'node' : node,
                        'entry_node_idx' : entry_nodes_cnt,
                        'build_node_idx' : build_nodes_cnt,
                        'inf_ip' : node_ip,
                        'eth_ip' : node_eth_ip}
                    entry_nodes_cnt += 1
                    build_nodes_cnt += 1
                elif entry_nodes_cnt < self.Par_.num_entrynodes and node not in self.Par_.exclude_entry_nodes:
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
        else:
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
                time.sleep(1)
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
        if self.Par_.overlap_usage_of_nodes:
        
            if len(node_list) < max(self.Par_.num_entrynodes, self.Par_.num_buildnodes) :
                logger.critical(f'Incorrect Number of nodes, expected: {self.Par_.num_entrynodes + self.Par_.num_buildnodes}, got: {len(node_list)} ')
                sys.exit(1)
            for node in node_list:
                node_ip = infiniband_ip(node)
                node_eth_ip = ethernet_ip(node)
                time.sleep(1)
                
                if node in self.Par_.entry_nodes_list and node in self.Par_.build_nodes_list and node not in self.Par_.exclude_entry_nodes + self.Par_.exclude_build_nodes:
                    self.overlap_nodes[node] = {
                        'node' : node,
                        'entry_node_idx' : entry_nodes_cnt,
                        'build_node_idx' : build_nodes_cnt,
                        'inf_ip' : node_ip,
                        'eth_ip' : node_eth_ip}
                    entry_nodes_cnt += 1
                    build_nodes_cnt += 1
                    node_list_remaining.remove(node)
                elif node in self.Par_.entry_nodes_list and node not in self.Par_.exclude_entry_nodes:
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
        else:
            if len(node_list) < self.Par_.num_entrynodes + self.Par_.num_buildnodes:
                logger.critical(f'Incorrect Number of nodes, expected: {self.Par_.num_entrynodes + self.Par_.num_buildnodes}, got: {len(node_list)} ')
                sys.exit(1)
            for node in node_list:
                node_ip = infiniband_ip(node)
                node_eth_ip = ethernet_ip(node)
                time.sleep(1)
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
    

    def assemble_receiving_nodes2build_nodes(self):
        node_list = self.get_node_list()
        unused_nodes = [node for node in node_list if node not in self.entry_nodes and node not in self.build_nodes and node not in self.overlap_nodes]
        used_build_nodes = []
        
        if len(unused_nodes) < self.Par_.num_buildnodes:
            logger.critical(f"Number of nodes are not sufficient for the Timeslice-forwarding. Number of nodes remaining {len(unused_nodes)}, expected: {self.Par_.num_buildnodes} Shutting down")
            sys.exit(1)
        if self.Par_.set_node_list:
            unused_nodes, used_build_nodes = self.assemble_receiving_nodes2build_nodes_customized(unused_nodes)
    
        cnt = 0
        if self.Par_.overlap_usage_of_nodes:
            for build_node_id,build_node in self.overlap_nodes.items():
                if build_node_id not in used_build_nodes:
                    
                    if unused_nodes[cnt] not in self.Par_.exclude_process_nodes:
                        self.rec2build.append((unused_nodes[cnt],build_node))
                    cnt += 1
                    if cnt > len(unused_nodes):
                        logger.critical(f'Could not assemble enough receiver nodes'
                                        f'Expected: {self.Par_.num_buildnodes}, got: {len(self.rec2build)}')
                        sys.exit(1)
        else:          
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
        build_nodes_list = list(self.overlap_nodes.items()) + list(self.build_nodes.items()) 
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
                time.sleep(1)
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
                time.sleep(1)
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
                time.sleep(1)
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
        if self.Par_.use_flesnet:
            self.input_nodes = self.build_nodes
        unused_nodes = [node for node in node_list if node not in self.entry_nodes and node not in self.build_nodes and node not in self.overlap_nodes]
        if self.Par_.set_node_list:
            unused_nodes,input_nodes_cnt,cm_nodes_cnt,output_nodes_cnt = self.assemble_timeslice_forwarding_nodes_customized(unused_nodes)
        for node in unused_nodes:
            node_ip = infiniband_ip(node)
            node_eth_ip = ethernet_ip(node)
            time.sleep(1)
            if cm_nodes_cnt < self.Par_.num_central_manager and node not in self.Par_.exclude_central_manager:
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
            if self.Par_.overlap_usage_of_nodes:
                res = self.super_nodes_cls.start_flesnet()
                if res == 'shutdown':
                    self.shutdown()
    
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
        if self.Par_.ZIB_timesliceforawrding:
            self.ZIB_timeslice_forwarding_cls.start_cm()
            
            self.ZIB_timeslice_forwarding_cls.stop_output_nodes()
            self.ZIB_timeslice_forwarding_cls.stop_input_nodes()
        if self.Par_.use_flesnet:
            if self.Par_.overlap_nodes:
                self.super_nodes_cls.stop_flesnet()
            else:
                self.entry_nodes_cls.stop_flesnet()
                self.build_nodes_cls.stop_flesnet()
        sys.exit(1)
        
                
    # =============================================================================
    # This function either starts the monotoring if activated or it just waits 
    # until the user stops the program
    # =============================================================================
    def stop_via_ctrl_c(self):
        time.sleep(2)
        logger.success('flesnet launched successfully')
        if self.Par_.show_total_data:
            #TODO: check if signal handling error still appears.
            try: 
                self.monitoring()
                while True:
                    time.sleep(1)
            except Exception as e:
                logger.critical(f'Error {e} occured during monotoring. Terminating')
        if self.Par_.kill_nodes:
            try:
                self.robustness_test()
                logger.success("Robustness test finished") 
                while True:
                    time.sleep(1)
            except Exception as e:
                logger.critical(f'Error {e} occured during robustness test. Terminating')
                self.stop_program()
               
        else:
            while True:
                time.sleep(1)
    
    
    def robustness_test(self):
        kill_dict, revieve_dict = self.create_kill_dict()      
        logger.debug("entry nodes to kill: " + "".join(f"{val[0]}; " for val in kill_dict["Entry nodes"]))
        logger.debug("build nodes to kill: " + "".join(f"{val[0]}; " for val in kill_dict["Build nodes"]))
        logger.debug("Process nodes to kill: " + "".join(f"{val}; " for val in kill_dict["Process nodes"]))
        logger.debug("Input nodes to kill: " + "".join(f"{val}; " for val in kill_dict["Input nodes"]))
        logger.debug("Central managers to kill: " + "".join(f"{val}; " for val in kill_dict["Central Manager"]))
        logger.debug("Output nodes to kill " + "".join(f"{val}; " for val in kill_dict["Output nodes"]))
        num_kills = self.Par_.num_entrynodes_kills + self.Par_.num_buildnodes_kills
        revieve_count = 0
        if self.Par_.activate_timesliceforwarding:
            num_kills += self.Par_.num_processnodes_kills
        elif self.Par_.ZIB_timesliceforwarding:
            print('test')
            num_kills += self.Par_.num_inputnodes_kills + self.Par_.num_cm_kills + self.Par_.num_outputnodes_kills
        print(num_kills)
        while num_kills != revieve_count:
            td = self.Par_.timer_for_kill.total_seconds()
            sleep_val = np.random.poisson(td)
            time.sleep(sleep_val)
            print(revieve_dict)
            weights_rc_1 = [sum(len(kill_nodes) for kill_nodes in kill_dict.values()), sum(len(revive_nodes) for revive_nodes in revieve_dict.values())]
            print(weights_rc_1)
            kill_or_revieve = random.choices(["Kill", "Revieve"], weights=weights_rc_1, k=1)[0]
            if kill_or_revieve == "Kill":
                kill_dict, revieve_dict = self.kill_nodes_fct(kill_dict,revieve_dict)
            else:
                revieve_dict = self.revieve_nodes_fct(revieve_dict)
                revieve_count += 1
                
                
                
    
    def create_kill_dict(self):
        kill_dict = {
                "Entry nodes" : [],
                "Build nodes" : [],
                "Process nodes" : [],
                "Input nodes" : [],
                "Central Manager" : [],
                "Output nodes" : []
            }
        revieve_dict = {
                "Entry nodes" : [],
                "Build nodes" : [],
                "Process nodes" : [],
                "Input nodes" : [],
                "Central Manager" : [],
                "Output nodes" : []
            }

        if self.Par_.set_kill_list == 1:
            kill_dict["Entry nodes"] = [(node, "Entry") for node in self.Par_.entry_node_kill_list]
            kill_dict["Build nodes"] = [(node, "Build") for node in self.Par_.build_node_kill_list]
            if self.Par_.activate_timesliceforwarding:
                kill_dict["Process nodes"] = [(node) for node in self.Par_.process_node_kill_list]
            elif self.Par_.ZIB_timesliceforwarding:
                kill_dict["Input nodes"] = [(node) for node in self.Par_.input_node_kill_list]
                kill_dict["Central Manager"] = [(node) for node in self.Par_.central_manager_kill_list]
                kill_dict["Output nodes"] = [(node) for node in self.Par_.output_node_kill_list]
            #logger.debug(f"Kill dict: {kill_dict}")
            #if self.Par_.activate_timesliceforwarding:
            #    kill_dict["Process nodes"] = self.Par_.process_node_kill_list
        if len(kill_dict["Entry nodes"]) < self.Par_.num_entrynodes_kills:
            entry_nodes = [(entry_node, "Entry") for entry_node in self.entry_nodes.keys() if entry_node not in self.Par_.entry_node_kill_list]
            entry_nodes += [(entry_node, "Super") for entry_node in self.overlap_nodes.keys() if entry_node not in self.Par_.entry_node_kill_list]
            kill_dict["Entry nodes"] += random.sample(entry_nodes, self.Par_.num_entrynodes_kills-len(kill_dict["Entry nodes"]) )
        if len(kill_dict["Build nodes"]) < self.Par_.num_buildnodes_kills:
            build_nodes = [(build_node, "Build") for build_node in self.build_nodes.keys() if build_node not in self.Par_.build_node_kill_list] 
            build_nodes += [(build_node, "Super") for build_node in self.overlap_nodes.keys() if build_node not in self.Par_.build_node_kill_list]
            kill_dict["Build nodes"] += random.sample(build_nodes, self.Par_.num_buildnodes_kills-len(kill_dict["Build nodes"]))
        if self.Par_.activate_timesliceforwarding:
            if len(kill_dict["Process nodes"]) < self.Par_.num_processnodes_kills:
                process_nodes = [receiving_node for receiving_node, build_node in self.rec2build if receiving_node not in self.Par_.process_node_kill_list]
                kill_dict["Process nodes"] += random.sample(process_nodes, self.Par_.num_processnodes_kills -len(kill_dict["Process nodes"]))
        elif self.Par_.ZIB_timesliceforwarding:
            if len(kill_dict["Input nodes"]) < self.Par_.num_inputnodes_kills:
                input_nodes = [input_node for input_node in self.input_nodes.keys() if input_node not in self.Par_.input_node_kill_list]
                kill_dict["Input nodes"] += random.sample(input_nodes, self.Par_.num_inputnodes_kills - len(kill_dict["Input nodes"]))
            if len(kill_dict["Central Manager"]) < self.Par_.num_cm_kills:
                central_manager = [cm for cm in self.central_manager.keys() if cm not in self.Par_.central_manager_kill_list]
                kill_dict["Central Manager"] += random.sample(central_manager, self.Par_.num_cm_kills - len(kill_dict["Central Manager"]))
            if len(kill_dict["Output nodes"]) < self.Par_.num_outputnodes_kills:
                output_nodes = [output_node for output_node in self.output_nodes.keys() if output_node not in self.Par_.output_node_kill_list]
                kill_dict["Output nodes"] += random.sample(output_nodes, self.Par_.num_outputnodes_kills - len(kill_dict["Output nodes"]))
        return kill_dict, revieve_dict
    
    
    def kill_nodes_fct(self,kill_dict,revieve_dict):
        #print('test kill nodes fct')
        weights_rc_2 = [len(kill_node) for kill_node in kill_dict.values()]
        node_type = random.choices(["Entry", "Build", "Process","Input", "CM","Output"], weights=weights_rc_2, k=1)[0]
        if node_type == "Entry":
            to_kill_node = random.choice(kill_dict["Entry nodes"])
            if to_kill_node[1] == "Entry":
                self.entry_nodes_cls.kill_process(to_kill_node[0])
            elif to_kill_node[1] == "Super":
                self.super_nodes_cls.kill_process_entry(to_kill_node[0])
            kill_dict["Entry nodes"].remove(to_kill_node)
            revieve_dict["Entry nodes"].append(to_kill_node)
        elif node_type == "Build":
            to_kill_node = random.choice(kill_dict["Build nodes"])
            if to_kill_node[1] == "Build":
                self.build_nodes_cls.kill_process(to_kill_node[0])
            elif to_kill_node[1] == "Super":
                self.super_nodes_cls.kill_process_build(to_kill_node[0])
            kill_dict["Build nodes"].remove(to_kill_node)
            revieve_dict["Build nodes"].append(to_kill_node)
        #Baustelle
        elif node_type == "Process":
            to_kill_node = random.choice(kill_dict["Process nodes"])
            self.timeslice_forwarding_cls.kill_process(to_kill_node)
            kill_dict["Process nodes"].remove(to_kill_node)
            revieve_dict["Process nodes"].append(to_kill_node)
        elif node_type == "Input":
            to_kill_node = random.choice(kill_dict["Input nodes"])
            self.ZIB_timeslice_forwarding_cls.kill_input_node(to_kill_node)
            kill_dict["Input nodes"].remove(to_kill_node)
            revieve_dict["Input nodes"].append(to_kill_node)
        elif node_type == "CM":
            to_kill_node = random.choice(kill_dict["Central Manager"])
            self.ZIB_timeslice_forwarding_cls.kill_central_manager(to_kill_node)
            kill_dict["Central Manager"].remove(to_kill_node)
            revieve_dict["Central Manager"].append(to_kill_node)
        elif node_type == "Output":
            to_kill_node = random.choice(kill_dict["Output nodes"])
            self.ZIB_timeslice_forwarding_cls.kill_output_node(to_kill_node)
            kill_dict["Output nodes"].remove(to_kill_node)
            revieve_dict["Output nodes"].append(to_kill_node)
        return kill_dict,revieve_dict
                
    def revieve_nodes_fct(self, revieve_dict):
        weights_rc_2 = [len(revieve_node) for revieve_node in revieve_dict.values()]
        node_type = random.choices(["Entry", "Build", "Process", "Input", "CM", "Output"], weights_rc_2, k=1)[0]
        if node_type == "Entry":
            to_revieve_node = random.choice(revieve_dict["Entry nodes"])
            if to_revieve_node[1] == "Entry":
                self.entry_nodes_cls.revieve_process(to_revieve_node[0])
            elif to_revieve_node[1] == "Super":
                self.super_nodes_cls.revieve_process_entry(to_revieve_node[0])
            revieve_dict["Entry nodes"].remove(to_revieve_node)
        elif node_type == "Build":
            to_revieve_node = random.choice(revieve_dict["Build nodes"])
            if to_revieve_node[1] == "Build":
                self.build_nodes_cls.revieve_process(to_revieve_node[0])
            elif to_revieve_node[1] == "Super":
                self.super_nodes_cls.revieve_process_build(to_revieve_node[0])
            revieve_dict["Build nodes"].remove(to_revieve_node)
        elif node_type == "Process":
            to_revieve_node = random.choice(revieve_dict["Process nodes"])
            self.timeslice_forwarding_cls.revieve_process(to_revieve_node)
            revieve_dict["Process nodes"].remove(to_revieve_node)
        elif node_type == "Input":
            to_revieve_node = random.choice(revieve_dict["Input nodes"])
            self.ZIB_timeslice_forwarding_cls.revieve_input_node(to_revieve_node)
            revieve_dict["Input nodes"].remove(to_revieve_node)
        elif node_type == "CM":
            to_revieve_node = random.choice(revieve_dict["Central Manager"])
            self.ZIB_timeslice_forwarding_cls.revieve_central_manager(to_revieve_node)
            revieve_dict["Central Manager"].remove(to_revieve_node)
        elif node_type == "Output":
            to_revieve_node = random.choice(revieve_dict["Output nodes"])
            self.ZIB_timeslice_forwarding_cls.revieve_output_node(to_revieve_node)
            revieve_dict["Output nodes"].remove(to_revieve_node)
        return revieve_dict
    
    
    # =============================================================================
    # Stops the experiment and kills every process connected    
    # =============================================================================
    def stop_program_V2(self):
        time.sleep(2)
        logger.info('stopping flesnet')
        total_data, avg_data_rate = 0,0
        if self.Par_.use_flesnet:
            if self.overlap_nodes:
                self.super_nodes_cls.stop_flesnet()
    
            self.build_nodes_cls.stop_flesnet()
            self.entry_nodes_cls.stop_flesnet()
            #print(self.activate_timesliceforwarding)
            if self.Par_.activate_timesliceforwarding:
                #print('test')
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
        if self.Par_.use_flesnet:
            if self.overlap_nodes:
                self.super_nodes_cls.stop_flesnet()
    
            self.build_nodes_cls.stop_flesnet()
            self.entry_nodes_cls.stop_flesnet()
            if self.Par_.show_total_data:
                total_data, avg_data_rate = self.stop_monitoring()
        return total_data, avg_data_rate
    # =============================================================================
    # Starts the monotoring. 
    # not used. outdated code snipped. For new one see monitoring function.
    # TODO: use collectl rather than flesnet logs
    # =============================================================================
    def monitoring_v2(self):
        file_names = []
        if self.overlap_nodes:
            entry_nodes_cnt = 0
            total_file_data = 0
            for super_node in self.overlap_nodes.keys():
                logfile = 'logs/flesnet/entry_nodes/entry_node_%s.log' % (super_node)
                #total_data = 1000
                file_data = 0
                file_data = next((tup[2] for tup in self.Par_.input_files if tup[0] == ('entry_node_' + str(entry_nodes_cnt))), None)
                if file_data is None:
                    file_data = next((tup[2] for tup in self.Par_.input_files if tup[0] == 'e_remaining'), None)
                
                file_names.append((logfile,file_data))
                entry_nodes_cnt += 1
                total_file_data += file_data
                
            for super_node in self.overlap_nodes.keys():
                if not self.Par_.show_only_entry_nodes:
                    logfile_build = 'logs/flesnet/build_nodes/build_node_%s.log' % (super_node)
                    total_data = total_file_data
                    file_names.append((logfile_build,total_data))
            total_data, avg_data_rate = curses.wrapper(mon.main,file_names,self.Par_.num_buildnodes, self.Par_.num_entrynodes, 
                                                       self.Par_.enable_graph, self.Par_.enable_progess_bar)

        entry_nodes_cnt = 0
        total_file_data = 0
        for entry_node in self.entry_nodes.keys():
            logfile = 'logs/flesnet/entry_nodes/entry_node_%s.log' % (entry_node)
            file_data = 0
            file_data = next((tup[2] for tup in self.Par_.input_files if tup[0] == ('entry_node_' + str(entry_nodes_cnt))), None)
            if file_data is None:
                file_data = next((tup[2] for tup in self.Par_.input_files if tup[0] == 'e_remaining'), None)
            
            file_names.append((logfile,file_data))
            entry_nodes_cnt += 1
            total_file_data += file_data
        if not self.Par_.show_only_entry_nodes:
            for build_node in self.build_nodes.keys():
                logfile = 'logs/flesnet/build_nodes/build_node_%s.log' % (build_node)
                file_data = total_file_data
                file_names.append((logfile,file_data))
        total_data, avg_data_rate = curses.wrapper(mon.main,file_names,self.Par_.num_buildnodes, self.Par_.num_entrynodes, 
                                                   self.Par_.enable_graph, self.Par_.enable_progess_bar)
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
    def monitoring(self):
        file_names = []
        if self.overlap_nodes:
            entry_nodes_cnt = 0
            total_file_data = 0
            for super_node in self.overlap_nodes.keys():
                logfile = '../logs/flesnet/entry_nodes/entry_node_%s.log' % (super_node)
                #total_data = 1000
                file_data = 0
                file_data = next((tup[2] for tup in self.Par_.input_files if tup[0] == ('entry_node_' + str(entry_nodes_cnt))), None)
                if file_data is None:
                    file_data = next((tup[2] for tup in self.Par_.input_files if tup[0] == 'e_remaining'), None)
                file_names.append((logfile,file_data))
                entry_nodes_cnt += 1
                total_file_data += file_data
            for super_node in self.overlap_nodes.keys():
                if not self.Par_.show_only_entry_nodes:
                    logfile_build = '../logs/flesnet/build_nodes/build_node_%s.log' % (super_node)
                    total_data = total_file_data
                    file_names.append((logfile_build,total_data))
        entry_nodes_cnt = 0
        total_file_data = 0
        for entry_node in self.entry_nodes.keys():
            logfile = '../logs/flesnet/entry_nodes/entry_node_%s.log' % (entry_node)
            file_data = 0
            file_data = next((tup[2] for tup in self.Par_.input_files if tup[0] == ('entry_node_' + str(entry_nodes_cnt))), None)
            if file_data is None:
                file_data = next((tup[2] for tup in self.Par_.input_files if tup[0] == 'e_remaining'), None)
            
            file_names.append((logfile,file_data))
            entry_nodes_cnt += 1
            total_file_data += file_data
        if not self.Par_.show_only_entry_nodes:
            for build_node in self.build_nodes.keys():
                logfile = '../logs/flesnet/build_nodes/build_node_%s.log' % (build_node)
                file_data = total_file_data
                file_names.append((logfile,file_data))
        with open('monitoring/mon_parameters.txt', 'w') as f:
            for logfile, file_data in file_names:
                f.write(f"file_name: {logfile}, {file_data}\n")
            f.write(f"num_buildnodes: {self.Par_.num_buildnodes}\n")
            f.write(f"num_entrynodes: {self.Par_.num_entrynodes}\n")
            f.write(f"enable_graph: {self.Par_.enable_graph}\n")
            f.write(f"enable_progess_bar: {self.Par_.enable_progress_bar}\n")
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
        

        
    # =============================================================================
    # currently not used 
    # =============================================================================
    def stop_monitoring_v2(self):
        try:
            with open("monitoring/pids_monitoring.txt", "r") as f:
                pid = int(f.read().strip())
            
            logger.info(f"killing process with Pid: {pid}")
            os.kill(pid, signal.SIGKILL)
            logger.success("Process killed")
            
            os.remove("monitoring/pids_monitoring.txt")
        except Exception as e:
            logger.error(f"Could not kill process: {e}")
    
    
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
        #print(contents)
        total_data = float(re.search(r'total_data: \s*([0-9.]+)', contents).group(1))
        avg_data_rate = float(re.search(r'avg_data_rate: \s*([0-9.]+)', contents).group(1))
        return total_data, avg_data_rate
            


    
