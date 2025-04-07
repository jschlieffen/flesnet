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
# import test_terminal_Graph_v2 as test
from log_msg import *
import logfile_gen as Logfile

class slurm_commands:
    
    def __init__(self):
        None
        
    def alloc_nodes(self,node_numbers):
        command = 'salloc --nodes=%s -p big --constraint=Infiniband --time=00:20:00'%(node_numbers)
        allocation = subprocess.run(command,shell=True)
        print(allocation.returncode)
        return allocation.returncode
    
    def pids(self,node_id):
        command = 'ps aux | grep %s' % (node_id) 
        try:
            result = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout,stderr = result.communicate()
            return stdout
        except subprocess.CalledProcessError as e:
            print('Error')
            sys.exit(1)
        return None

    def ethernet_ip(self,node_id):
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
    
    def infiniband_ip(self,node_id):
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
        
        

class Entry_nodes(slurm_commands):
    
    def __init__(self,node_list,build_nodes_ips,build_nodes_eth_ips, num_entry_nodes,
                 path, transport_method, customize_string, use_pattern_gen, use_dmsa_files):
        super().__init__()
        self.node_list = node_list
        self.build_nodes_ips = build_nodes_ips
        self.build_nodes_eth_ips = build_nodes_eth_ips
        self.num_entry_nodes = num_entry_nodes
        self.path = path
        self.transport_method = transport_method
        self.customize_string = customize_string
        self.use_pattern_gen = use_pattern_gen
        self.use_dmsa_files = use_dmsa_files
        self.pids = []
    

    def start_flesnet(self,input_files, influx_node_ip, influx_token, use_grafana):
        file = 'input.py'
        node_cnt = 0
        for node in self.node_list.keys():
            input_file = next((tup[1] for tup in input_files if tup[0] == ('entry_node_' + str(node_cnt))), None)
            if input_file is None:
                input_file = next((tup[1] for tup in input_files if tup[0] == 'e_remaining'), None)
            
            logger.info(f'start entry node: {node}, with input file {input_file}')
            logfile = "logs/flesnet/entry_nodes/entry_node_%s.log" % node
            command = (
                'srun --nodelist=%s --oversubscribe -N 1 %s %s %s %s %s %s %s %s %s %s %s " %s" %s %s' 
                % (node,file,input_file,logfile,self.build_nodes_ips, 
                self.num_entry_nodes ,self.node_list[node]['entry_node_idx'],
                 influx_node_ip, influx_token, use_grafana, self.path,
                 self.transport_method, self.customize_string,
                 self.use_pattern_gen, self.use_dmsa_files)
            )
            try:
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
    
class Build_nodes(slurm_commands):
    
    def __init__(self,node_list,entry_nodes_ips,entry_nodes_eth_ips, num_build_nodes,
                 path, transport_method, customize_string):
        super().__init__()
        self.node_list = node_list
        self.num_build_nodes = num_build_nodes
        self.entry_node_ips = entry_nodes_ips
        self.entry_node_eth_ips = entry_nodes_eth_ips
        self.path = path
        self.transport_method = transport_method
        self.customize_string = customize_string
        self.pids = []
        
    def start_flesnet(self, influx_node_ip, influx_token, use_grafana):
        file = 'output.py'
        for node in self.node_list.keys():
            logger.info(f'start build node: {node}')
            logfile = 'logs/flesnet/build_nodes/build_node_%s.log' % (node)
            command = (
                'srun --nodelist=%s -N 1 %s %s %s %s %s %s %s %s %s %s " %s"'
                % (node,file,logfile, self.entry_node_ips, self.num_build_nodes ,
                   self.node_list[node]['build_node_idx'], influx_node_ip, 
                   influx_token, use_grafana, self.path,
                   self.transport_method,self.customize_string)
            )
            try:
                result = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) 
            except subprocess.CalledProcessError as e:
                logger.error('ERROR {e} occurried in build node: {node}. Shutdown flesnet')
                return 'shutdown'            
            self.pids += [result]
            logger.success(f'start successful')
        return None
    

    def stop_flesnet(self):
        for pid in self.pids:
            pid.stdin.write('stop')
            stdout, stderr = pid.communicate()
            print('Output: ',stdout)
            print('Error: ', stderr)
            print('\n')

class Super_nodes(slurm_commands):
    
    def __init__(self,node_list,entry_nodes_ips,entry_nodes_eth_ips, num_build_nodes,build_nodes_ips,build_nodes_eth_ips, num_entry_nodes, 
                 path, transport_method, customize_string, use_pattern_gen, use_dmsa_files):
        super().__init__()
        self.node_list = node_list
        self.num_build_nodes = num_build_nodes
        self.entry_node_ips = entry_nodes_ips
        self.entry_node_eth_ips = entry_nodes_eth_ips
        self.build_nodes_ips = build_nodes_ips
        self.build_nodes_eth_ips = build_nodes_eth_ips
        self.num_entry_nodes = num_entry_nodes
        self.path = path
        self.transport_method = transport_method
        self.customize_string = customize_string
        self.use_pattern_gen = use_pattern_gen
        self.use_dmsa_files = use_dmsa_files
        self.pids = []
        
    def start_flesnet(self,input_files, influx_node_ip, influx_token, use_grafana):
        file = 'super_nodes.py'
        node_cnt = 0
        for node in self.node_list.keys():
            input_file = next((tup[1] for tup in input_files if tup[0] == ('entry_node_' + str(node_cnt))), None)
            if input_file is None:
                input_file = next((tup[1] for tup in input_files if tup[0] == 'e_remaining'), None)
            
            logger.info(f'start entry node: {node}, with input file {input_file}')
            logfile_entry_node = "logs/flesnet/entry_nodes/entry_node_%s.log" % node
            logfile_build_node = "logs/flesnet/build_nodes/build_node_%s.log" % node
            command = (
                'srun --nodelist=%s -N 1 %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s " %s" %s %s'
                % (node,file,input_file,logfile_entry_node, logfile_build_node,
                   self.build_nodes_ips, self.entry_node_ips, 
                   self.num_entry_nodes , self.num_build_nodes,
                   self.node_list[node]['entry_node_idx'], self.node_list[node]['build_node_idx'],
                   influx_node_ip, influx_token, use_grafana, self.path,
                   self.transport_method, self.customize_string,
                   self.use_pattern_gen, self.use_dmsa_files)
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

class execution(slurm_commands):
    
    def __init__(self, input_files,num_entrynodes, num_buildnodes, show_total_data, influx_node_ip, influx_token, use_grafana, 
                 overlap_usage_of_nodes,path,transport_method,customize_string, enable_graph, enable_progess_bar,
                 show_only_entry_nodes, use_pattern_gen, use_dmsa_files):
        super().__init__()
        self.input_files = input_files
        self.num_entrynodes = num_entrynodes 
        self.num_buildnodes = num_buildnodes
        self.show_total_data = show_total_data
        self.influx_node_ip = influx_node_ip
        self.influx_token = influx_token
        self.use_grafana = use_grafana
        self.overlap_usage_of_nodes = overlap_usage_of_nodes
        self.path = path
        self.transport_method = transport_method
        self.customize_string = customize_string
        self.enable_graph = enable_graph
        self.enable_progess_bar = enable_progess_bar
        self.show_only_entry_nodes = show_only_entry_nodes
        self.use_pattern_gen = use_pattern_gen
        self.use_dmsa_files = use_dmsa_files
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
        self.entry_nodes_cls = Entry_nodes(self.entry_nodes,self.build_nodes_ips,self.build_nodes_eth_ips, self.num_entrynodes,
                                           self.path, self.transport_method, self.customize_string, self.use_pattern_gen, self.use_dmsa_files)
        self.build_nodes_cls = Build_nodes(self.build_nodes, self.entry_nodes_ips,self.entry_nodes_eth_ips, self.num_buildnodes,
                                           self.path, self.transport_method, self.customize_string)
        self.super_nodes_cls = Super_nodes(self.overlap_nodes, self.entry_nodes_ips,self.entry_nodes_eth_ips, self.num_buildnodes,
                                           self.build_nodes_ips,self.build_nodes_eth_ips, self.num_entrynodes, self.path, 
                                           self.transport_method, self.customize_string, self.use_pattern_gen, self.use_dmsa_files)
        
        
    def get_node_list(self):
        node_str = os.environ.get('SLURM_NODELIST')
        node_list = []
        range_pattern = re.findall(r'(.*?)(\d+)-(\d+)', node_str)
        list_pattern = re.findall(r'(.*?)(\d+(?:,\d+)*)', node_str)
        for base, start, end in range_pattern:
            start, end = int(start), int(end)
            node_list.extend([f"htc-cmp{i}" for i in range(start, end + 1)])
        for base, numbers in list_pattern:
            num_list = numbers.split(",")
            node_list.extend([f"htc-cmp{num.strip()}" for num in num_list])
        node_list = sorted(set(node_list))
        return node_list
    
    
    
    def get_eth_ips(self):
        for key, val in self.entry_nodes.items():
            self.entry_nodes_eth_ips += 'shm://' + val['eth_ip'] + '/0'
        for key, val in self.build_nodes.items():
            self.build_nodes_eth_ips += 'shm://' + val['eth_ip'] + '/0'
            
        
    def get_ips(self):
        if self.overlap_usage_of_nodes:
            for key,val in self.overlap_nodes.items():
                self.entry_nodes_ips += val['inf_ip'] + "sep"
                self.build_nodes_ips += val['inf_ip'] + "sep"
        for key,val in self.entry_nodes.items():
            self.entry_nodes_ips += val['inf_ip'] + "sep"
        for key,val in self.build_nodes.items():
            self.build_nodes_ips += val['inf_ip'] + "sep"
            
    def schedule_nodes(self):
        node_list = self.get_node_list()
        entry_nodes_cnt = 0
        build_nodes_cnt = 0
        if node_list is None:
            logger.critical('SLURM_NODELIST is not set, Maybe you forget to allocate the nodes')
            sys.exit(1)
            
        elif len(node_list) < self.num_entrynodes + self.num_buildnodes:
            logger.critical('Incorrect Number of nodes, expected: {self.num_entrynodes + self.num_buildnodes}, got: {len(node_list)} ')
            sys.exit(1)
        if self.overlap_usage_of_nodes:
            for node in node_list:
                node_ip = self.infiniband_ip(node)
                node_eth_ip = self.ethernet_ip(node)
                time.sleep(1)
                
                if entry_nodes_cnt < self.num_entrynodes and build_nodes_cnt < self.num_buildnodes:
                    self.overlap_nodes[node] = {
                        'node' : node,
                        'entry_node_idx' : entry_nodes_cnt,
                        'build_node_idx' : build_nodes_cnt,
                        'inf_ip' : node_ip,
                        'eth_ip' : node_eth_ip}
                    entry_nodes_cnt += 1
                    build_nodes_cnt += 1
                elif entry_nodes_cnt < self.num_entrynodes:
                    self.entry_nodes[node] = {
                        'node' : node,
                        'entry_node_idx' : entry_nodes_cnt,
                        'inf_ip' : node_ip,
                        'eth_ip' : node_eth_ip}
                    entry_nodes_cnt += 1
                elif build_nodes_cnt < self.num_buildnodes:
                    self.build_nodes[node] = {
                        'node' : node,
                        'build_node_idx' : build_nodes_cnt,
                        'inf_ip' : node_ip,
                        'eth_ip' : node_eth_ip}
                    build_nodes_cnt += 1
        else:
            for node in node_list:
                node_ip = self.infiniband_ip(node)
                node_eth_ip = self.ethernet_ip(node)
                time.sleep(1)
                if entry_nodes_cnt < self.num_entrynodes:
                    self.entry_nodes[node] = {
                        'node' : node,
                        'entry_node_idx' : entry_nodes_cnt,
                        'inf_ip' : node_ip,
                        'eth_ip' : node_eth_ip}
                    entry_nodes_cnt += 1
                elif build_nodes_cnt < self.num_buildnodes:
                    self.build_nodes[node] = {
                        'node' : node,
                        'build_node_idx' : build_nodes_cnt,
                        'inf_ip' : node_ip,
                        'eth_ip' : node_eth_ip}
                    build_nodes_cnt += 1
        
        Logfile.logfile.entry_nodes_list = self.entry_nodes
        Logfile.logfile.build_nodes_list = self.build_nodes
        Logfile.logfile.overlap_nodes_list = self.overlap_nodes
        
    def bijectiv_mapping(self):
        for entry_node, build_node in zip(self.entry_nodes.keys(), self.build_nodes.keys()):
            self.entry_nodes[entry_node]['allocated_build_node'] = build_node
            self.build_nodes[build_node]['allocated_entry_node'] = entry_node
    
    
    def start_Flesnet(self):
        if self.overlap_usage_of_nodes:
            res = self.super_nodes_cls.start_flesnet(self.input_files,self.influx_node_ip, self.influx_token, self.use_grafana)
            if res == 'shutdown':
                self.super_nodes_cls.stop_flesnet()
                sys.exit(1)
        else:
            res = self.entry_nodes_cls.start_flesnet(self.input_files,self.influx_node_ip, self.influx_token, self.use_grafana)
            if res == 'shutdown':
                self.entry_nodes_cls.stop_flesnet()
                sys.exit(1)
            else:    
                res = self.build_nodes_cls.start_flesnet(self.influx_node_ip, self.influx_token, self.use_grafana)
                if res == 'shutdown':
                    self.entry_nodes_cls.stop_flesnet()
                    self.build_nodes_cls.stop_flesnet()
                    sys.exit(1)
                    
                    
    def start_Flesnet_zeromq(self):
        self.entry_nodes_cls.start_flesnet_zeromq()
        self.build_nodes_cls.start_flesnet_zeromq()
            
    
    def stop_via_ctrl_c(self):
        time.sleep(2)
        logger.success('flesnet launched successfully')
        if self.show_total_data:
            try: 
                total_data, avg_data_rate = self.monitoring()
            except Exception as e:
                logger.critical(f'Error {e} occured during monotoring. Terminating')
        else:
            while True:
                time.sleep(1)
        self.stop_program()
        return total_data, avg_data_rate
        
    def stop_program(self):
        time.sleep(2)
        logger.info('stopping flesnet')
        if self.overlap_nodes:
            self.super_nodes_cls.stop_flesnet()
        else:
            self.build_nodes_cls.stop_flesnet()
            self.entry_nodes_cls.stop_flesnet()

    def monitoring(self):
        file_names = []
        if self.overlap_nodes:
            entry_nodes_cnt = 0
            total_file_data = 0
            for super_node in self.overlap_nodes.keys():
                logfile = 'logs/flesnet/entry_nodes/entry_node_%s.log' % (super_node)
                #total_data = 1000
                file_data = 0
                file_data = next((tup[2] for tup in self.input_files if tup[0] == ('entry_node_' + str(entry_nodes_cnt))), None)
                if file_data is None:
                    file_data = next((tup[2] for tup in self.input_files if tup[0] == 'e_remaining'), None)
                
                file_names.append((logfile,file_data))
                entry_nodes_cnt += 1
                total_file_data += file_data
                
            for super_node in self.overlap_nodes.keys():
                if not self.show_only_entry_nodes:
                    logfile_build = 'logs/flesnet/build_nodes/build_node_%s.log' % (super_node)
                    total_data = total_file_data
                    file_names.append((logfile_build,total_data))
            total_data, avg_data_rate = curses.wrapper(mon.main,file_names,self.num_buildnodes, self.num_entrynodes, 
                                                       self.enable_graph, self.enable_progess_bar)
        else:
            entry_nodes_cnt = 0
            total_file_data = 0
            for entry_node in self.entry_nodes.keys():
                logfile = 'logs/flesnet/entry_nodes/entry_node_%s.log' % (entry_node)
                #total_data = 1000
                #logfile='testefkEGBW'
                file_data = 0
                file_data = next((tup[2] for tup in self.input_files if tup[0] == ('entry_node_' + str(entry_nodes_cnt))), None)
                if file_data is None:
                    file_data = next((tup[2] for tup in self.input_files if tup[0] == 'e_remaining'), None)
                
                file_names.append((logfile,file_data))
                entry_nodes_cnt += 1
                total_file_data += file_data
            if not self.show_only_entry_nodes:
                for build_node in self.build_nodes.keys():
                    logfile = 'logs/flesnet/build_nodes/build_node_%s.log' % (build_node)
                    #logfile='uefjsav'
                    file_data = total_file_data
                    file_names.append((logfile,file_data))
            #print(file_names)
            total_data, avg_data_rate = curses.wrapper(mon.main,file_names,self.num_buildnodes, self.num_entrynodes, 
                                                       self.enable_graph, self.enable_progess_bar)
        return total_data, avg_data_rate
        
def main():
    arg = docopt.docopt(__doc__, version='0.2')
    
    allocating_nodes = arg["<allocating_nodes>"]
    
    s = slurm_commands()

    if allocating_nodes != '0':
        s.alloc_nodes(4)
    else:

        exec_ = execution(3, 2)
        print('Entry nodes: ', exec_.entry_nodes)
        print('Build nodes: ', exec_.build_nodes)
        print('Build nodes ips: ' + exec_.entry_nodes_ips)
        print('Entry Nodes ips: ' + exec_.build_nodes_ips)
        exec_.start_Flesnet()
        exec_.stop_via_ctrl_c()
        
    
if __name__ == '__main__':
    main()
        
    
    
