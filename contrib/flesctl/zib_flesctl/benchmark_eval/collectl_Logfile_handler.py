#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 11 18:20:09 2025

@author: jschlieffen
"""

import csv 
import os
from datetime import datetime

class serialize_data:
    
    def __init__(self, data_rates, cpu_usage, file_name, timeslice_forwarding_activated):
        
        self.data_rate = data_rates
        self.cpu_usage = cpu_usage
        self.file_name = file_name
        self.timeslice_forwarding_activated = timeslice_forwarding_activated
        

    def get_time_stmps(self, data_rates):
        all_timestamps = set()
        for inner_dict in data_rates.values():
            all_timestamps.update(inner_dict.keys())
        return sorted(all_timestamps)

    def get_csv_file_name_data_rates(self,node_type):
        dir = os.path.dirname(__file__)
        if node_type == "entry_nodes":
            path = os.path.join(dir,'collectl/data/data_rates/entry_nodes')
        elif node_type == "build_nodes":
            path = os.path.join(dir,'collectl/data/data_rates/build_nodes')
        elif node_type == 'tsclient':
            path = os.path.join(dir,'collectl/data/data_rates/receiving_nodes')
        if not os.path.exists(path):
            os.makedirs(path)
        path = path + '/'
        Run_id = os.path.basename(self.file_name)
        Run_id = Run_id.removesuffix(".log")
        if node_type == "entry_nodes":
            csv_file_name = f"{path}/data_rates_entry_nodes_{Run_id}.csv"
        elif node_type == "build_nodes":
            csv_file_name = f"{path}/data_rates_build_nodes_{Run_id}.csv"
        elif node_type == "receiving_nodes":
            csv_file_name = f"{path}/data_rates_receiving_nodes_{Run_id}.csv"
        return csv_file_name
            
    def serialize_data(self):
        for node_type in self.data_rate.keys():
            csv_file_name = self.get_csv_file_name_data_rates(node_type)
            timestamps = self.get_time_stmps(self.data_rate[node_type])
            with open(csv_file_name, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                if node_type == 'build_nodes' and self.timeslice_forwarding_activated:
                    first_header = ['timestamps'] 
                    second_header = ['timestamps']
                    for key in self.shm_usage.keys():
                        first_header.extend([key] + [''])
                        second_header.extend(['KBIn','KBOut'])
                        writer.writerow(first_header)
                        writer.writerow(second_header)
                else:
                    header = ['timestamps'] + list(self.data_rate[node_type].keys())
                    writer.writerow(header)
                for timestamp in timestamps:
                    row = [timestamp]
                    for data_dict in self.data_rate[node_type].values():
                        #row.append(val.get(timestamp,''))
                        vals = data_dict.get(timestamp,{})
                        if node_type == 'entry_nodes':
                            row.extend([vals.get('KBOut','')])
                        elif node_type == 'build_nodes':
                            if self.timeslice_forwarding_activated:
                                row.extend([
                                        vals.get('KBIn'),
                                        vals.get('KBOut')
                                    ])
                            else:
                                row.extend([vals.get('KBIn','')])
                        elif node_type == 'tsclient':
                            row.extend([vals.get('KBIn','')])
                    writer.writerow(row)
        
    def get_csv_file_name_cpu_usages(self, node_type):
        dir = os.path.dirname(__file__)
        if node_type == "entry_nodes":
            path = os.path.join(dir,'collectl/data/cpu_usages/entry_nodes')
        elif node_type == "build_nodes":
            path = os.path.join(dir,'collectl/data/cpu_usages/build_nodes')
        elif node_type == 'tsclient':
            path = os.path.join(dir,'collectl/data/cpu_usages/receiving_nodes')
        if not os.path.exists(path):
            os.makedirs(path)
        path = path + '/'
        Run_id = os.path.basename(self.file_name)
        Run_id = Run_id.removesuffix(".log")
        if node_type == "entry_nodes":
            csv_file_name = f"{path}/cpu_usages_entry_nodes_{Run_id}.csv"
        elif node_type == "build_nodes":
            csv_file_name = f"{path}/cpu_usages_build_nodes_{Run_id}.csv"
        elif node_type == "tsclient":
            csv_file_name = f"{path}/cpu_usages_receiving_nodes_{Run_id}.csv"
        return csv_file_name
    
    
    #maybe extended when cpu usage will be depended on allocation
    def serialize_cpu_usage(self):
        for node_type in self.cpu_usage.keys():
            csv_file_name = self.get_csv_file_name_cpu_usages(node_type)
            timestamps = self.get_time_stmps(self.cpu_usage[node_type])
            with open(csv_file_name, "w", newline='') as csvfile:
                writer = csv.writer(csvfile)
                header = ['timestamps'] + list(self.cpu_usage[node_type].keys())
                writer.writerow(header)
                for timestamp in timestamps:
                    row = [timestamp]
                    for cpu_dict in self.cpu_usage[node_type].values():
                        val = cpu_dict.get(timestamp, {})
                        #print(timestamps)
                        #print(val)
                        #print(cpu_dict)
                        row.append(100 - val.get('overall_avg', ''))
                    writer.writerow(row)
                
                
                
                
                
                