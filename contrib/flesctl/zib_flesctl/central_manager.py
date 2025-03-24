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

# =============================================================================
# TODO: get rid of entry nodes and build nodes cls. Use only super nodes
# =============================================================================

import subprocess
import sys
import os
import time
import docopt
import re
import monitoring as mon
import curses

class slurm_commands:
    
    def __init__(self):
        None
        
    def alloc_nodes(self,node_numbers):
        command = 'salloc --nodes=%s -p big --constraint=Infiniband --time=00:20:00'%(node_numbers)
        allocation = subprocess.run(command,shell=True)
        print(allocation.returncode)
        return allocation.returncode
    
    #Todo: try-except for all slurm-commands
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

    # =============================================================================
    #  TODO:
    #       1. take care that the message may change
    #       2. make sure that the message 
    # =============================================================================
    def ethernet_ip(self,node_id):
        command = 'srun --nodelist=%s -N 1 --ntasks 1 ip a' % (node_id)
        result = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout,stderr = result.communicate()
        match = re.search(r'eth0:(.*?)scope global eth0',stdout,re.DOTALL)
        content = match.group(1)
        match2 = re.search(r'inet (.*?)/23',content,re.DOTALL)
        content2 = match2.group(1)
        return content2
    
    def infiniband_ip(self,node_id):
        command = 'srun --nodelist=%s -N 1 --ntasks 1 ip a' % (node_id)
        result = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        result.wait()
        stdout,stderr = result.communicate()
        match = re.search(r'ib0:(.*?)scope global ib0',stdout,re.DOTALL)
        content = match.group(1)
        match2 = re.search(r'inet (.*?)/23',content,re.DOTALL)
        content2 = match2.group(1)
        return content2
        

    def start_customize_program(self,program_name,node_id):
        command = '%s &> /dev/null &' %(program_name)
        result = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return None
    
    def srun_test(self,file, node_id):
        command ='srun --nodelist=%s python3 %s' % (node_id,file)
        result = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return None
    
        

class Entry_nodes(slurm_commands):
    
    def __init__(self,node_list,build_nodes_ips,build_nodes_eth_ips, num_entry_nodes):
        super().__init__()
        self.node_list = node_list
        self.build_nodes_ips = build_nodes_ips
        self.build_nodes_eth_ips = build_nodes_eth_ips
        self.num_entry_nodes = num_entry_nodes
        self.pids = []
    

    def start_flesnet(self,input_files, influx_node_ip, influx_token, use_grafana):
        file = 'input.py'
        for node in self.node_list.keys():
            input_file = next((tup[1] for tup in input_files if tup[0] == node), None)
            # TODO: Check if there is a faster implementation
            if input_file is None:
                input_file = next((tup[1] for tup in input_files if tup[0] == 'e_remaining'), None)
            logfile = "logs/entry_node_%s.log" % node
            command = 'srun --nodelist=%s --oversubscribe -N 1 %s %s %s %s %s %s %s %s %s' % (node,file,input_file,logfile,self.build_nodes_ips, 
                                                                                              self.num_entry_nodes ,self.node_list[node]['entry_node_idx'],
                                                                                              influx_node_ip, influx_token, use_grafana)
            result = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) 
            time.sleep(1)
            self.pids += [result]
        return None
    
    def start_flesnet_zeromq(self):
        file = 'input_zeromq.py'
        for node in self.node_list.keys():
            command = 'srun --nodelist=%s -N 1 %s %s' % (node,file,self.build_nodes_eth_ips)
            result = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)    
        return None
    
    def stop_flesnet(self):
        for pid in self.pids:
            pid.stdin.write('stop')
            stdout, stderr = pid.communicate()
            print('Output: ',stdout)
            print('Error: ', stderr)
            print('\n')
    
class Build_nodes(slurm_commands):
    
    def __init__(self,node_list,entry_nodes_ips,entry_nodes_eth_ips, num_build_nodes):
        super().__init__()
        self.node_list = node_list
        self.num_build_nodes = num_build_nodes
        self.entry_node_ips = entry_nodes_ips
        self.entry_node_eth_ips = entry_nodes_eth_ips
        self.pids = []
        
    def start_flesnet(self, influx_node_ip, influx_token, use_grafana):
        file = 'output.py'
        for node in self.node_list.keys():
            logfile = 'logs/build_node_%s.log' % (node)
            command = 'srun --nodelist=%s -N 1 %s %s %s %s %s %s %s %s ' % (node,file,logfile, self.entry_node_ips, self.num_build_nodes ,
                                                                            self.node_list[node]['build_node_idx'], influx_node_ip, 
                                                                            influx_token, use_grafana)
            result = subprocess.Popen(command, shell=True,stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)        
            self.pids += [result]
        return None
    
    def start_flesnet_zeromq(self):
        file = 'output_zeromq.py'
        for node in self.node_list.keys():
            command = 'srun --nodelist=%s -N 1 %s %s' % (node,file,self.entry_node_eth_ips)
            result = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)    
        return None

    def stop_flesnet(self):
        for pid in self.pids:
            pid.stdin.write('stop')
            stdout, stderr = pid.communicate()
            print('Output: ',stdout)
            print('Error: ', stderr)
            print('\n')

class Super_nodes(slurm_commands):
    
    def __init__(self,node_list,entry_nodes_ips,entry_nodes_eth_ips, num_build_nodes,build_nodes_ips,build_nodes_eth_ips, num_entry_nodes):
        super().__init__()
        self.node_list = node_list
        self.num_build_nodes = num_build_nodes
        self.entry_node_ips = entry_nodes_ips
        self.entry_node_eth_ips = entry_nodes_eth_ips
        self.build_nodes_ips = build_nodes_ips
        self.build_nodes_eth_ips = build_nodes_eth_ips
        self.num_entry_nodes = num_entry_nodes
        self.pids = []
        print(self.node_list)
        
    def start_flesnet(self,input_files, influx_node_ip, influx_token, use_grafana):
        file = 'super_nodes.py'
        for node in self.node_list.keys():
            input_file = next((tup[1] for tup in input_files if tup[0] == node), None)
            # TODO: Check if there is a faster implementation
            if input_file is None:
                input_file = next((tup[1] for tup in input_files if tup[0] == 'e_remaining'), None)
            logfile_entry_node = "logs/entry_node_%s.log" % node
            logfile_build_node = "logs/build_node_%s.log" % node
            command = 'srun --nodelist=%s -N 1 %s %s %s %s %s %s %s %s %s %s %s %s %s' % (node,file,input_file,logfile_entry_node, logfile_build_node,
                                                                                                       self.build_nodes_ips, self.entry_node_ips, 
                                                                                                       self.num_entry_nodes , self.num_build_nodes,
                                                                                                       self.node_list[node]['entry_node_idx'], self.node_list[node]['build_node_idx'],
                                                                                                       influx_node_ip, influx_token, use_grafana)
            result = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) 
            time.sleep(1)
            self.pids += [result]
        return None
    
    def start_flesnet_zeromq(self):
        file = 'input_zeromq.py'
        for node in self.node_list.keys():
            command = 'srun --nodelist=%s -N 1 %s %s' % (node,file,self.build_nodes_eth_ips)
            result = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)    
        return None


    def stop_flesnet(self):
        for pid in self.pids:
            pid.stdin.write('stop')
            stdout, stderr = pid.communicate()
            print('Output: ',stdout)
            print('Error: ', stderr)
            print('\n')

class execution(slurm_commands):
    
    def __init__(self, input_files,num_entrynodes, num_buildnodes, show_total_data, influx_node_ip, influx_token, use_grafana, overlap_usage_of_nodes):
        super().__init__()
        self.input_files = input_files
        self.num_entrynodes = num_entrynodes 
        self.num_buildnodes = num_buildnodes
        self.show_total_data = show_total_data
        self.influx_node_ip = influx_node_ip
        self.influx_token = influx_token
        self.use_grafana = use_grafana
        self.overlap_usage_of_nodes = overlap_usage_of_nodes
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
        self.entry_nodes_cls = Entry_nodes(self.entry_nodes,self.build_nodes_ips,self.build_nodes_eth_ips, self.num_entrynodes)
        self.build_nodes_cls = Build_nodes(self.build_nodes, self.entry_nodes_ips,self.entry_nodes_eth_ips, self.num_buildnodes)
        self.super_nodes_cls = Super_nodes(self.overlap_nodes, self.entry_nodes_ips,self.entry_nodes_eth_ips, self.num_buildnodes,
                                                               self.build_nodes_ips,self.build_nodes_eth_ips, self.num_entrynodes)
        #print(type(self.show_total_data))
        #print(self.show_total_data)
    
    #TODO: Pattern does not work
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
            
    # =============================================================================
    # Ich habe keine Ahnung ob sich hier eventuell durch sbatch was aendert.
    # =============================================================================
    def schedule_nodes(self):
        node_list = self.get_node_list()
        entry_nodes_cnt = 0
        build_nodes_cnt = 0
        if node_list is None:
            print("Error: SLURM_NODELIST is not set.")
            sys.exit(1)
            
        # =============================================================================
        # Note: Hier aendert sich vielleicht noch was
        # =============================================================================
        elif len(node_list) != self.num_entrynodes + self.num_buildnodes:
            print('Incorrect number of nodes')
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
                #print(self.entry_nodes)
                #print(self.build_nodes)
                #print(self.overlap_nodes)
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
                else:
                    print('unexpected error with the number of nodes')
                    sys.exit(1)
     
        
    def bijectiv_mapping(self):
        for entry_node, build_node in zip(self.entry_nodes.keys(), self.build_nodes.keys()):
            self.entry_nodes[entry_node]['allocated_build_node'] = build_node
            self.build_nodes[build_node]['allocated_entry_node'] = entry_node
    
    
    def start_Flesnet(self):
        if self.overlap_usage_of_nodes:
            self.super_nodes_cls.start_flesnet(self.input_files,self.influx_node_ip, self.influx_token, self.use_grafana)
        self.entry_nodes_cls.start_flesnet(self.input_files,self.influx_node_ip, self.influx_token, self.use_grafana)
        self.build_nodes_cls.start_flesnet(self.influx_node_ip, self.influx_token, self.use_grafana)
            
    def start_Flesnet_zeromq(self):
        self.entry_nodes_cls.start_flesnet_zeromq()
        self.build_nodes_cls.start_flesnet_zeromq()
            
    
    #TODO Wednesday: debug monotoring
    def stop_via_ctrl_c(self):
        time.sleep(2)
        print('flesnet successfully launched')
        if self.show_total_data:
            print('test')
            try: 
                self.monitoring()
            except KeyboardInterrupt:
                print('Interrupting')
                self.build_nodes_cls.stop_flesnet()
                self.entry_nodes_cls.stop_flesnet()
        else: 
            try: 
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print('Interrupting')
                if self.overlap_nodes:
                    self.super_nodes_cls.stop_flesnet()
                self.build_nodes_cls.stop_flesnet()
                self.entry_nodes_cls.stop_flesnet()
            
        return None
        

    def monitoring(self):
        file_names = []
        for entry_node in self.entry_nodes.keys():
            logfile = 'logs/entry_node_%s.log' % (entry_node)
            total_data = 1000
            file_names.append((logfile,total_data))
        for build_node in self.build_nodes.keys():
            logfile = 'logs/build_node_%s.log' % (build_node)
            total_data = 2000
            file_names.append((logfile,total_data))
        curses.wrapper(mon.main,file_names,self.num_buildnodes, self.num_entrynodes)
        
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
        
    
    
