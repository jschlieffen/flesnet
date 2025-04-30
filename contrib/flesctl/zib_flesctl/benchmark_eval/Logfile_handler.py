#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 29 10:32:50 2025

@author: jschlieffen
"""

import csv
import Logfile_reader as LR
import os

# =============================================================================
# Write this for both entry and build nodes
# =============================================================================
class serialize_data:
    
    def __init__(self,node_type,data_rates,shm_usage,file_name):
        #self.timestamps = timestamps
        self.node_type = node_type
        self.data_rate = data_rates
        self.shm_usage = shm_usage
        self.file_name = file_name
        
        
    def get_time_stmps(self,data_rates):
        #print(data_rates)
        largest_key = max(data_rates, key=lambda k: len(data_rates[k]))
        largest_dict = data_rates[largest_key]
        timestamps = [key for key in largest_dict.keys()]
        return timestamps
    
    
    def get_csv_file_name_data_rates(self):
        dir = os.path.dirname(__file__)
        if self.node_type == "e":
            path = os.path.join(dir,'data/data_rates/entry_nodes')
        else:
            path = os.path.join(dir,'data/data_rates/build_nodes')
        if not os.path.exists(path):
            os.makedirs(path)
        path = path + '/'
        Run_id = os.path.basename(self.file_name)
        Run_id = Run_id.removesuffix(".log")
        if self.node_type == "e":
            csv_file_name = f"{path}/data_rates_entry_nodes_{Run_id}.csv"
        else:
            csv_file_name = f"{path}/data_rates_build_nodes_{Run_id}.csv"
        return csv_file_name
    
    def serialize_data_rates(self):
        csv_file_name = self.get_csv_file_name_data_rates()
        timestamps = self.get_time_stmps(self.data_rate)
        with open(csv_file_name, "w", newline='') as csvfile:
            writer = csv.writer(csvfile)
            header = ['timestamps'] + list(self.data_rate.keys())
            writer.writerow(header)
            for timestamp in timestamps:
                row = [timestamp]
                for val in self.data_rate.values():
                    row.append(val.get(timestamp,''))
                writer.writerow(row)
    
    
    def get_csv_file_name_shm_usages(self):
        dir = os.path.dirname(__file__)
        if self.node_type == "e":
            path = os.path.join(dir,'data/shm_usages/entry_nodes')
        else:
            path = os.path.join(dir,'data/shm_usages/build_nodes')
        if not os.path.exists(path):
            os.makedirs(path)
        path = path + '/'
        Run_id = os.path.basename(self.file_name)
        Run_id = Run_id.removesuffix(".log")
        if self.node_type == "e":
            csv_file_name = f"{path}/shm_usages_entry_nodes_{Run_id}.csv"
        else:
            csv_file_name = f"{path}/shm_usages_build_nodes_{Run_id}.csv"
        return csv_file_name
    
    
    def serialize_shm_usage_entry_nodes(self):
        csv_file_name = self.get_csv_file_name_shm_usages()
        timestamps = self.get_time_stmps(self.shm_usage)
        with open(csv_file_name, "w", newline='') as csvfile:
            writer = csv.writer(csvfile)
            first_header = ['timestamps'] 
            second_header = ['timestamps']
            for key in self.shm_usage.keys():
                first_header.extend([key] + ['']*3)
                second_header.extend(['used','sending','freeing','free'])
            
            writer.writerow(first_header)
            writer.writerow(second_header)
            for timestamp in timestamps:
                row=[timestamp]
                for shm_dict in self.shm_usage.values():
                    vals = shm_dict.get(timestamp,{})
                    row.extend([
                        vals.get('used',''),
                        vals.get('sending',''),
                        vals.get('freeing',''),
                        vals.get('free','')
                    ])
                writer.writerow(row)
                
            
    #def get_time_stmps_build_nodes(self):
        
                
    #TODO: extract time stamps from the shm usage.
    def serialize_shm_usage_build_nodes(self):
        #print(self.shm_usage)
        csv_file_name = self.get_csv_file_name_shm_usages()
        timestamps = self.get_time_stmps(self.data_rate)
        with open(csv_file_name, "w", newline='') as csvfile:
            writer = csv.writer(csvfile)
            first_header = ['timestamps'] 
            second_header = ['']
            third_header = ['']
            for key,value in self.shm_usage.items():
                first_header.extend([key] + ['']*2)
                num_entry_node = len(value)
                first_header.extend(['']*3*(num_entry_node - 1))
                for entry_node_id in value.keys():
                    second_header.extend([entry_node_id]+ ['']*2)
                    third_header.extend(['used','freeing','free'])
            
            writer.writerow(first_header)
            writer.writerow(second_header)
            writer.writerow(third_header)
            for timestamp in timestamps:
                row=[timestamp]
                for shm_dict in self.shm_usage.values():
                    #print('test')
                    #print(shm_dict)
                    for entry_node_dict in shm_dict.values():
                        vals = entry_node_dict.get(timestamp,{})
                        row.extend([
                            vals.get('used',''),
                            #vals.get('sending',''),
                            vals.get('freeing',''),
                            vals.get('free','')
                        ])
                        #print(vals)
                writer.writerow(row)
                
            
    
    