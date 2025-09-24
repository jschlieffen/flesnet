#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#Created on Thu Dec 19 15:04:17 2024

#@author: jschlieffen


"""Usage:
    allocating_nodes.py <allocating_nodes>
    allocating_nodes.py (-h | --help)

Options:
    -h --help  Show this message.
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
from log_msg import *
import logfile_gen as Logfile


# =============================================================================
# This file deals with scheduling the nodes and starting the import processes.
# It deals with starting an experiment and clean up after the end of the experiment
# Note: it is the only file where you can communicate with the different nodes 
#       Thus for debugging purposes it is recommended to look at this file
# =============================================================================

# =============================================================================
# This class deals with the reading of the ips of a node. May be extended in 
# furture
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
# This class is used to start and stop flesnet/mstool for the entry nodes
# It gets as input the entry node list, the build_node ips and the specifc 
# attributes for the start of flesnet (e.g. rmda/zeromq)
# =============================================================================
class Entry_nodes:
    def __init__(self, node_list,build_nodes_ips,build_nodes_eth_ips,parameters):
        super().__init__()
        self.node_list = node_list
        self.build_nodes_ips = build_nodes_ips
        self.build_nodes_eth_ips = build_nodes_eth_ips
        self.Par_ = parameters
        self.pids = []
    

    #TODO: make cpu param
    def start_flesnet(self):
        file = 'input.py'
        node_cnt = 0
        for node in self.node_list.keys():
            input_file = next((tup[1] for tup in self.Par_.input_files if tup[0] == ('entry_node_' + str(node_cnt))), None)
            if input_file is None:
                input_file = next((tup[1] for tup in self.Par_.input_files if tup[0] == 'e_remaining'), None)
            
            logger.info(f'start entry node: {node}, with input file {input_file}')
            logfile = "logs/flesnet/entry_nodes/entry_node_%s.log" % node
            logfile_collectl = "logs/collectl/entry_nodes/entry_node_%s.csv" % node
            if self.Par_.use_infiniband:
                command = (
                    'srun --nodelist=%s --exclusive -N 1 -c 5 %s %s %s %s %s %s %s %s %s %s %s " %s" %s %s %s %s %s' 
                    % (node,file,input_file,logfile,self.build_nodes_ips, 
                    self.Par_.num_entrynodes ,self.node_list[node]['entry_node_idx'],
                     self.Par_.influx_node_ip, self.Par_.influx_token, self.Par_.use_grafana, self.Par_.path,
                     self.Par_.transport_method, self.Par_.customize_string,
                     self.Par_.use_pattern_gen, self.Par_.use_dmsa_files, self.Par_.use_infiniband,
                     self.Par_.use_collectl, logfile_collectl)
                )
            else:
                command = (
                    'srun --nodelist=%s --exclusive -N 1 %s %s %s %s %s %s %s %s %s %s %s " %s" %s %s %s %s %s' 
                    % (node,file,input_file,logfile,self.build_nodes_eth_ips, 
                    self.Par_.num_entrynodes ,self.node_list[node]['entry_node_idx'],
                     self.Par_.influx_node_ip, self.Par_.influx_token, self.Par_.use_grafana, self.Par_.path,
                     self.Par_.transport_method, self.Par_.customize_string,
                     self.Par_.use_pattern_gen, self.Par_.use_dmsa_files, self.Par_.use_infiniband,
                     self.Par_.use_collectl, logfile_collectl)
                )
            try:
                #print(command)
                result = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) 
            except subprocess.CalledProcessError as e:
                logger.error(f'ERROR {e} occurried in entry node: {node}. Shutdown flesnet')
                return 'shutdown'
            time.sleep(1)
            self.pids += [result]
            logger.success('start successful')
            node_cnt += 1
        return None
    
    
    def stop_flesnet(self):
        for pid in self.pids:
            pid.stdin.write('stop')
            stdout, stderr = pid.communicate()
            print('Output: ',stdout)
            print('Error: ', stderr)
            print('\n')
    

# =============================================================================
# This class is used to start and stop flesnet for the build nodes
# It gets as input the build node list, the entry node ips and the specifc 
# attributes for the start of flesnet (e.g. rmda/zeromq)
# =============================================================================
class Build_nodes:
    
    def __init__(self,node_list,entry_nodes_ips,entry_nodes_eth_ips,parameters):
        super().__init__()
        self.node_list = node_list
        #self.num_build_nodes = num_build_nodes
        self.entry_node_ips = entry_nodes_ips
        self.entry_node_eth_ips = entry_nodes_eth_ips
        self.Par_ = parameters
        self.pids = []
        
    def start_flesnet(self):
        file = 'output.py'
        for node in self.node_list.keys():
            logger.info(f'start build node: {node}')
            logfile = 'logs/flesnet/build_nodes/build_node_%s.log' % (node)
            logfile_collectl = 'logs/collectl/build_nodes/build_node_%s.csv' % (node)
            if self.Par_.use_infiniband == 1:
                command = (
                    'srun --nodelist=%s --exclusive -N 1 -c 5 %s %s %s %s %s %s %s %s %s %s " %s" %s %s %s'
                    % (node,file,logfile, self.entry_node_ips, self.Par_.num_buildnodes ,
                       self.node_list[node]['build_node_idx'], self.Par_.influx_node_ip, 
                       self.Par_.influx_token, self.Par_.use_grafana, self.Par_.path,
                       self.Par_.transport_method,self.Par_.customize_string,self.Par_.use_infiniband,
                       self.Par_.use_collectl, logfile_collectl)
                )
            else: 
                command = (
                    'srun --nodelist=%s --exclusive -N 1 %s %s %s %s %s %s %s %s %s %s " %s" %s %s %s'
                    % (node,file,logfile, self.entry_node_eth_ips, self.Par_.num_buildnodes ,
                       self.node_list[node]['build_node_idx'], self.Par_.influx_node_ip, 
                       self.Par_.influx_token, self.Par_.use_grafana, self.Par_.path,
                       self.Par_.transport_method,self.Par_.customize_string,self.Par_.use_infiniband,
                       self.Par_.use_collectl, logfile_collectl)
                )
            try:
               
                result = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) 
            except subprocess.CalledProcessError as e:
                logger.error('ERROR {e} occurried in build node: {node}. Shutdown flesnet')
                return 'shutdown'            
            self.pids += [result]
        #print(command)
        logger.success(f'start of build nodes successful')
        return None
    

    def stop_flesnet(self):
        for pid in self.pids:
            pid.stdin.write('stop')
            stdout, stderr = pid.communicate()
            print('Output: ',stdout)
            print('Error: ', stderr)
            print('\n')

# =============================================================================
# This class is used to start and stop flesnet on nodes that are used for both 
# entry nodes and build nodes. It gets as input the node list, the 
# entry node ips, build node ips and the specifc 
# attributes for the start of flesnet (e.g. rmda/zeromq)
# =============================================================================
class Super_nodes:
    def __init__(self,node_list,entry_nodes_ips,entry_nodes_eth_ips,build_nodes_ips,build_nodes_eth_ips,parameters):
        super().__init__()
        self.node_list = node_list
        #self.num_build_nodes = num_build_nodes
        self.entry_node_ips = entry_nodes_ips
        self.entry_node_eth_ips = entry_nodes_eth_ips
        self.build_nodes_ips = build_nodes_ips
        self.build_nodes_eth_ips = build_nodes_eth_ips
        self.Par_ = parameters
        self.pids = []
        
    def start_flesnet(self):
        file = 'super_nodes.py'
        node_cnt = 0
        for node in self.node_list.keys():
            input_file = next((tup[1] for tup in self.Par_.input_files if tup[0] == ('entry_node_' + str(node_cnt))), None)
            if input_file is None:
                input_file = next((tup[1] for tup in self.Par_.input_files if tup[0] == 'e_remaining'), None)
            
            logger.info(f'start entry node: {node}, with input file {input_file}')
            logfile_entry_node = "logs/flesnet/entry_nodes/entry_node_%s.log" % node
            logfile_build_node = "logs/flesnet/build_nodes/build_node_%s.log" % node
            logfile_collectl_entry_node = "logs/collectl/entry_nodes/entry_node_%s.csv" % node
            logfile_collectl_build_node = "logs/collectl/build_nodes/build_node_%s.csv" % node
            if self.Par_.use_infiniband:
                command = (
                    'srun --nodelist=%s --exclusive -N 1 -c 5 %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s " %s" %s %s %s %s %s %s'
                    % (node,file,input_file,logfile_entry_node, logfile_build_node,
                       self.build_nodes_ips, self.entry_node_ips, 
                       self.Par_.num_entrynodes , self.Par_.num_buildnodes,
                       self.node_list[node]['entry_node_idx'], self.node_list[node]['build_node_idx'],
                       self.Par_.influx_node_ip, self.Par_.influx_token, self.Par_.use_grafana, self.Par_.path,
                       self.Par_.transport_method, self.Par_.customize_string,
                       self.Par_.use_pattern_gen, self.Par_.use_dmsa_files,self.Par_.use_infiniband,
                       self.Par_.use_collectl, logfile_collectl_entry_node, logfile_collectl_build_node)
                )
            else:
                command = (
                    'srun --nodelist=%s --exclusive -N 1 -c 5 %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s " %s" %s %s %s %s %s %s'
                    % (node,file,input_file,logfile_entry_node, logfile_build_node,
                       self.build_nodes_eth_ips, self.entry_node_eth_ips, 
                       self.Par_.num_entrynodes , self.Par_.num_buildnodes,
                       self.node_list[node]['entry_node_idx'], self.node_list[node]['build_node_idx'],
                       self.Par_.influx_node_ip, self.Par_.influx_token, self.Par_.use_grafana, self.Par_.path,
                       self.Par_.transport_method, self.Par_.customize_string,
                       self.Par_.use_pattern_gen, self.Par_.use_dmsa_files,self.Par_.use_infiniband,
                       self.Par_.use_collectl, logfile_collectl_entry_node, logfile_collectl_build_node)
                )
            try:
                result = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) 
            except subprocess.CalledProcessError as e:
                logger.error(f'ERROR {e} occurried in super node: {node}. Shutdown flesnet')
                return 'shutdown'
            time.sleep(1)
            self.pids += [result]
            logger.success('start successful')
            node_cnt += 1
        return None
    

    def stop_flesnet(self):
        for pid in self.pids:
            pid.stdin.write('stop')
            stdout, stderr = pid.communicate()
            print('Output: ',stdout)
            print('Error: ', stderr)
            print('\n')


#TODO: make port depended on node
class Timeslice_forwarding:
    
    def __init__(self, rec2build, parameters):    
        super().__init__()
        self.rec2build = rec2build
        self.Par_ = parameters
        self.pids = []

        

        
    def start_receivers(self):
        file = 'timeslice_forwarding.py'
        for receiving_node,build_node in self.rec2build:
            logger.info(f"start timeslice forwarding node {receiving_node} for build node {build_node['node']}")
            logfile = 'logs/flesnet/tsclient/receiving_node_%s.log' % (receiving_node)
            #print(build_node)
            logfile_collectl = 'logs/collectl/tsclient/receiving_node_%s.csv' % (receiving_node)
            build_node_ip = build_node['inf_ip']
            command = (
                    'srun --nodelist=%s -N 1 -c 5 %s %s %s %s %s %s %s %s %s %s %s %s %s'
                    % (receiving_node,file,logfile, build_node_ip, self.Par_.influx_token, self.Par_.influx_node_ip, self.Par_.use_grafana, self.Par_.path,
                       self.Par_.port, self.Par_.write_data_to_file, self.Par_.analyze_data,  self.Par_.use_infiniband, self.Par_.use_collectl, logfile_collectl
                        )
                )
            try:
                result = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) 
            except subprocess.CalledProcessError as e:
                logger.error('ERROR {e} occurried in timeslice-forwarding: {receiving_node}. Shutdown flesnet')
                return 'shutdown' 
            self.pids += [result]
        logger.success('start of timeslice receivers successful')
        return None
        
            
    def stop_timeslice_forwarding(self):
        for pid in self.pids:
            pid.stdin.write('stop')
            stdout, stderr = pid.communicate()
            print('Output: ',stdout)
            print('Error: ', stderr)
            print('\n')


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
        self.schedule_nodes()

        self.entry_nodes_ips = ""
        self.build_nodes_ips = ""
        self.get_ips()
        self.entry_nodes_eth_ips = ""
        self.build_nodes_eth_ips = ""
        self.get_eth_ips()
        if self.Par_.activate_timesliceforwarding:
            self.rec2build = []
            self.assemble_receiving_nodes2build_nodes()
        self.entry_nodes_cls = Entry_nodes(self.entry_nodes,self.build_nodes_ips,self.build_nodes_eth_ips, self.Par_)
        self.build_nodes_cls = Build_nodes(self.build_nodes, self.entry_nodes_ips,self.entry_nodes_eth_ips, self.Par_)
        self.super_nodes_cls = Super_nodes(self.overlap_nodes, self.entry_nodes_ips,self.entry_nodes_eth_ips,self.build_nodes_ips,self.build_nodes_eth_ips, self.Par_)
    
        if self.Par_.activate_timesliceforwarding:
            self.timeslice_forwarding_cls = Timeslice_forwarding(self.rec2build, self.Par_)
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
            
        
    def get_ips(self):
        if self.Par_.overlap_usage_of_nodes:
            for key,val in self.overlap_nodes.items():
                self.entry_nodes_ips += val['inf_ip'] + "sep"
                self.build_nodes_ips += val['inf_ip'] + "sep"
        for key,val in self.entry_nodes.items():
            self.entry_nodes_ips += val['inf_ip'] + "sep"
        for key,val in self.build_nodes.items():
            self.build_nodes_ips += val['inf_ip'] + "sep"
    
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
                
                if entry_nodes_cnt < self.Par_.num_entrynodes and build_nodes_cnt < self.Par_.num_buildnodes:
                    self.overlap_nodes[node] = {
                        'node' : node,
                        'entry_node_idx' : entry_nodes_cnt,
                        'build_node_idx' : build_nodes_cnt,
                        'inf_ip' : node_ip,
                        'eth_ip' : node_eth_ip}
                    entry_nodes_cnt += 1
                    build_nodes_cnt += 1
                elif entry_nodes_cnt < self.Par_.num_entrynodes:
                    self.entry_nodes[node] = {
                        'node' : node,
                        'entry_node_idx' : entry_nodes_cnt,
                        'inf_ip' : node_ip,
                        'eth_ip' : node_eth_ip}
                    entry_nodes_cnt += 1
                elif build_nodes_cnt < self.Par_.num_buildnodes:
                    self.build_nodes[node] = {
                        'node' : node,
                        'build_node_idx' : build_nodes_cnt,
                        'inf_ip' : node_ip,
                        'eth_ip' : node_eth_ip}
                    build_nodes_cnt += 1
        else:
            if len(node_list) < (self.Par_.num_entrynodes - entry_nodes_cnt) + (self.Par_.num_buildnodes - build_nodes_cnt):
                logger.critical(f'Incorrect Number of nodes, expected:'
                                f'{(self.Par_.num_entrynodes - entry_nodes_cnt) + (self.Par_.num_buildnodes - build_nodes_cnt)}'
                                f', got: {len(node_list)} '
                                )
                sys.exit(1)
            for node in node_list:
                node_ip = infiniband_ip(node)
                node_eth_ip = ethernet_ip(node)
                time.sleep(1)
                if entry_nodes_cnt < self.Par_.num_entrynodes:
                    self.entry_nodes[node] = {
                        'node' : node,
                        'entry_node_idx' : entry_nodes_cnt,
                        'inf_ip' : node_ip,
                        'eth_ip' : node_eth_ip}
                    entry_nodes_cnt += 1
                elif build_nodes_cnt < self.Par_.num_buildnodes:
                    self.build_nodes[node] = {
                        'node' : node,
                        'build_node_idx' : build_nodes_cnt,
                        'inf_ip' : node_ip,
                        'eth_ip' : node_eth_ip}
                    build_nodes_cnt += 1
            
    # =============================================================================
    # Help function for schedule nodes. Used if the user wants to set the
    # entry nodes and build nodes manually
    # =============================================================================
    def schedule_nodes_customized(self,node_list,entry_nodes_cnt, build_nodes_cnt):
        #print(node_list)
        node_list_remaining = node_list[: ]
        if self.Par_.overlap_usage_of_nodes:
        
            if len(node_list) < max(self.Par_.num_entrynodes, self.Par_.num_buildnodes):
                logger.critical(f'Incorrect Number of nodes, expected: {self.Par_.num_entrynodes + self.Par_.num_buildnodes}, got: {len(node_list)} ')
                sys.exit(1)
            for node in node_list:
                node_ip = infiniband_ip(node)
                node_eth_ip = ethernet_ip(node)
                time.sleep(1)
                
                if node in self.Par_.entry_nodes_list and node in self.Par_.build_nodes_list:
                    self.overlap_nodes[node] = {
                        'node' : node,
                        'entry_node_idx' : entry_nodes_cnt,
                        'build_node_idx' : build_nodes_cnt,
                        'inf_ip' : node_ip,
                        'eth_ip' : node_eth_ip}
                    entry_nodes_cnt += 1
                    build_nodes_cnt += 1
                    node_list_remaining.remove(node)
                elif node in self.Par_.entry_nodes_list:
                    self.entry_nodes[node] = {
                        'node' : node,
                        'entry_node_idx' : entry_nodes_cnt,
                        'inf_ip' : node_ip,
                        'eth_ip' : node_eth_ip}
                    entry_nodes_cnt += 1
                    node_list_remaining.remove(node)
                elif node in self.Par_.build_nodes_list:
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
                if node in self.entry_nodes_list:
                    #print(node)
                    self.entry_nodes[node] = {
                        'node' : node,
                        'entry_node_idx' : entry_nodes_cnt,
                        'inf_ip' : node_ip,
                        'eth_ip' : node_eth_ip}
                    entry_nodes_cnt += 1
                    node_list_remaining.remove(node)
                elif node in self.build_nodes_list:
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
    
    # =============================================================================
    # Currently not used  
    # =============================================================================
    def bijectiv_mapping(self):
        for entry_node, build_node in zip(self.entry_nodes.keys(), self.build_nodes.keys()):
            self.entry_nodes[entry_node]['allocated_build_node'] = build_node
            self.build_nodes[build_node]['allocated_entry_node'] = entry_node
    
    
    def assemble_receiving_nodes2build_nodes(self):
        node_list = self.get_node_list()
        unused_nodes = [node for node in node_list if node not in self.entry_nodes and node not in self.build_nodes and node not in self.overlap_nodes]
        if len(unused_nodes) < self.Par_.num_buildnodes:
            logger.critical(f"Number of nodes are not sufficient for the Timeslice-forwarding. Number of nodes remaining {len(unused_nodes)}, expected: {self.Par_.num_buildnodes} Shutting down")
            sys.exit(1)
        cnt = 0
        if self.Par_.overlap_usage_of_nodes:
            for build_node_id,build_node in self.overlap_nodes.items():
                self.rec2build.append((unused_nodes[cnt],build_node))
                cnt += 1
        else:
            for build_node_id,build_node in self.build_nodes.items():
                self.rec2build.append((unused_nodes[cnt],build_node))
                cnt += 1
        Logfile.logfile.receiving_node_list = self.rec2build
        
        
    # =============================================================================
    # This function starts flesnet and partly checks if the start was successful  
    # =============================================================================
    def start_Flesnet(self):
        if self.Par_.activate_timesliceforwarding:
            res = self.timeslice_forwarding_cls.start_receivers()
            if res == 'shutdown':
                self.timeslice_forwarding_cls.stop_timeslice_forwarding()
                time.sleep(1)
                sys.exit()
        if self.Par_.overlap_usage_of_nodes:
            res = self.super_nodes_cls.start_flesnet()
            if res == 'shutdown':
                if self.Par_.activate_timesliceforwarding:
                    self.timeslice_forwarding_cls.stop_timeslice_forwarding()
                self.super_nodes_cls.stop_flesnet()
                sys.exit(1)
        else:
            res = self.entry_nodes_cls.start_flesnet()
            if res == 'shutdown':
                if self.Par_.activate_timesliceforwarding:
                    self.timeslice_forwarding_cls.stop_timeslice_forwarding()
                self.entry_nodes_cls.stop_flesnet()
                sys.exit(1)
            else:    
                res = self.build_nodes_cls.start_flesnet()
                if res == 'shutdown':
                    if self.Par_.activate_timesliceforwarding:
                        self.timeslice_forwarding_cls.stop_timeslice_forwarding()
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
            try: 
                self.monitoring()
            except Exception as e:
                logger.critical(f'Error {e} occured during monotoring. Terminating')
        while True:
            time.sleep(1)
    
    # =============================================================================
    # Stops the experiment and kills every process connected    
    # =============================================================================
    def stop_program(self):
        time.sleep(2)
        logger.info('stopping flesnet')
        total_data, avg_data_rate = 0,0
        if self.overlap_nodes:
            self.super_nodes_cls.stop_flesnet()
        else:
            self.build_nodes_cls.stop_flesnet()
            self.entry_nodes_cls.stop_flesnet()
        #print(self.activate_timesliceforwarding)
        if self.Par_.activate_timesliceforwarding:
            #print('test')
            self.timeslice_forwarding_cls.stop_timeslice_forwarding()
        if self.Par_.show_total_data:
            total_data, avg_data_rate = self.stop_monitoring()
        return total_data, avg_data_rate
            

    # =============================================================================
    # Starts the monotoring. 
    # not used. outdated code snipped. For new one see monitoring function.
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
        #print(contents)
        total_data = float(re.search(r'total_data: \s*([0-9.]+)', contents).group(1))
        avg_data_rate = float(re.search(r'avg_data_rate: \s*([0-9.]+)', contents).group(1))
        return total_data, avg_data_rate
            

        
    
    
