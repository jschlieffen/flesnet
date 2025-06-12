#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun  6 11:58:03 2025

@author: jschlieffen
"""

import csv
from datetime import datetime
import re



class collectl_reader:
    
    def __init__(self,Logfile_name_infiniband,Logfile_name_cpu, node_type, timeslice_forwarding_activated):
        self.Logfile_infiniband = self.read_file(Logfile_name_infiniband)
        self.Logfile_cpu_usage = self.read_file(Logfile_name_cpu)
        self.node_type = node_type
        self.timeslice_forwarding_activated = timeslice_forwarding_activated
        self.data_rates = {}
        self.cpu_usage = {}

    def read_file(self, Logfile_name):
        with open(Logfile_name, newline='') as csvfile:
            next(csvfile)
            reader = csv.DictReader(csvfile)
            return list(reader)
    
    
    def extract_infiniband_usage(self):
        for row in self.Logfile_infiniband:
            #print(row)
            dt = row['#Date'] + ' ' + row['Time']
            timestamp = datetime.strptime(dt, "%Y%m%d %H:%M:%S")
            if self.node_type == 'tsclient':
                self.data_rates[timestamp] = {
                        'KBIn' : int(row['[IB]InKB'])
                    }
            elif self.node_type == 'entry_node':
                self.data_rates[timestamp] = {
                        'KBOut' : int(row['[IB]OutKB'])
                    }
            elif self.node_type == 'build_node':
                if self.timeslice_forwarding_activated:
                    self.data_rates[timestamp] = {
                            'KBIn' : int(row['[IB]InKB']),
                            'KBOut' : int(row['[IB]OutKB'])
                        }
                else:
                    self.data_rates[timestamp] = {
                            'KBIn' : int(row['[IB]InKB'])
                        }
    def get_num_cpus(self,header):
        cpu_ids = set()
        for col in header:
            match = re.match(r'\[CPU:(\d+)\]',col)
            if match:
                cpu_ids.add(int(match.group(1)))
        return len(cpu_ids)
        
    #TODO: make avg over allocated cpus from flesnet
    def extract_cpu_usage(self):
        header = (self.Logfile_cpu_usage[0])
        #print(header)
        num_cpus = self.get_num_cpus(header)
        for row in self.Logfile_cpu_usage:
            dt = row['#Date'] + ' ' + row['Time']
            timestamp = datetime.strptime(dt, "%Y%m%d %H:%M:%S")
            #self.cpu_usage = {}
            avg_usage = 0 
            for i in range(0,num_cpus):
                avg_usage += int(row[f'[CPU:{i}]Idle%'])
            avg_usage = avg_usage/num_cpus
            self.cpu_usage[timestamp] = {
                    'overall_avg' : avg_usage
                }
                
        #idle_indices = [i for i,col in enumerate(header) if 'Idle%' in col]
        
                
                
def main():
    
    entry_node_reader = collectl_reader('../logs/collectl/entry_nodes/entry_node_htc-cmp507.csv', 
                                        '../logs/collectl/entry_nodes/entry_node_htc-cmp507_cpu_usage.csv', 'entry_node')
    build_node_reader = collectl_reader('../logs/collectl/build_nodes/build_node_htc-cmp520.csv',
                                        '../logs/collectl/build_nodes/build_node_htc-cmp520_cpu_usage.csv', 'build_node')
    tsclient_reader = collectl_reader('../logs/collectl/tsclient/receiving_node_htc-cmp523.csv', 
                                      '../logs/collectl/tsclient/receiving_node_htc-cmp523_cpu_usage.csv', 'tsclient')
    entry_node_reader.extract_infiniband_usage()
    build_node_reader.extract_infiniband_usage()
    tsclient_reader.extract_infiniband_usage()
    print("\033[35mentry_nodes\033[0m")
    #print(entry_node_reader.data_rates)
    for data in entry_node_reader.data_rates:
        print(f"\033[32m{data}: \033[0m {entry_node_reader.data_rates[data]}")
    print("\033[35mbuild_nodes\033[0m")
    for data in build_node_reader.data_rates:
        print(f"\033[32m{data}: \033[0m {build_node_reader.data_rates[data]}")
    print("\033[35mtsclient\033[0m")
    for data in tsclient_reader.data_rates:
        print(f"\033[32m{data}: \033[0m {tsclient_reader.data_rates[data]}")
        
    entry_node_reader.extract_cpu_usage()
    build_node_reader.extract_cpu_usage()
    tsclient_reader.extract_cpu_usage()
    
    print("\033[35mentry_nodes\033[0m")
    #print(entry_node_reader.data_rates)
    for data in entry_node_reader.cpu_usage:
        print(f"\033[32m{data}: \033[0m {entry_node_reader.cpu_usage[data]}")
    print("\033[35mbuild_nodes\033[0m")
    for data in build_node_reader.cpu_usage:
        print(f"\033[32m{data}: \033[0m {build_node_reader.cpu_usage[data]}")
    print("\033[35mtsclient\033[0m")
    for data in tsclient_reader.cpu_usage:
        print(f"\033[32m{data}: \033[0m {tsclient_reader.cpu_usage[data]}")

if __name__ == '__main__':
    main()
        
    
    
    
    