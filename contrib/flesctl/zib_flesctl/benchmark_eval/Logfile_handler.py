#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 29 10:32:50 2025

@author: jschlieffen
"""

import csv
import Logfile_reader as LR
import os
from datetime import datetime

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
        
        
    def get_time_stmps_v2(self,data_rates):
        #print(data_rates)
        largest_key = max(data_rates, key=lambda k: len(data_rates[k]))
        largest_dict = data_rates[largest_key]
        timestamps = [key for key in largest_dict.keys()]
        return timestamps
    
    def get_time_stmps(self, data_rates):
        all_timestamps = set()
        for inner_dict in data_rates.values():
            all_timestamps.update(inner_dict.keys())
        return sorted(all_timestamps)
    
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
        #print(timestamps)
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
                
            
    def get_time_stmps_build_nodes_v2(self,data_rates):
        max_len = 0
        timestamps = []
        #print(data_rates)
        for outer_dict in data_rates.values():
            #print(outer_dict)
            for inner_dict in outer_dict.values():
                if len(inner_dict) > max_len:
                    max_len = len(inner_dict)
                    timestamps = list(inner_dict.keys())
        
        return timestamps
                
    def get_time_stmps_build_nodes(self, data_rates):
        all_timestamps = set()
        for outer_dict in data_rates.values():
            for inner_dict in outer_dict.values():
                all_timestamps.update(inner_dict.keys())
        
        return sorted(all_timestamps)
    
    
    #TODO: extract time stamps from the shm usage.
    def serialize_shm_usage_build_nodes(self):
        #print(self.shm_usage)
        csv_file_name = self.get_csv_file_name_shm_usages()
        timestamps = self.get_time_stmps_build_nodes(self.shm_usage)
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
                
    

                
            
class deserialize_data:
    
    def __init__(self,node_type,file_name):
        self.node_type = node_type
        self.file_name = file_name
        self.data_rate = {} 
        self.shm_usage = {}


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

    def deserialize_data_rates(self):
        csv_file_name = self.get_csv_file_name_data_rates()
        data_rate = {}
    
        with open(csv_file_name, "r", newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                timestamp_str = row['timestamps']
                try:
                    timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    try:
                        timestamp = datetime.fromtimestamp(float(timestamp_str))
                    except ValueError:
                        raise ValueError(f"Unrecognized timestamp format: {timestamp_str}")
                for key in row:
                    if key == 'timestamps':
                        continue
                    value = row[key]
                    if value != '':
                        try:
                            value = int(value)
                        except ValueError:
                            try:
                                value = float(value)
                            except ValueError:
                                pass
                        if key not in data_rate:
                            data_rate[key] = {}
                        data_rate[key][timestamp] = value
    
        #print(data_rate)
        self.data_rate = data_rate


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



    def deserialize_shm_usage_entry_nodes(self):
        csv_file_name = self.get_csv_file_name_shm_usages()
        shm_usage = {}
    
        with open(csv_file_name,"r", newline='') as csvfile:
            reader = csv.reader(csvfile)
            first_header = next(reader)
            second_header = next(reader)
            keys = [key for key in first_header if key != '' and key != 'timestamps']
            
            for row in reader:
                timestamp_str = row[0]
                try:
                    timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    try:
                        timestamp = datetime.fromtimestamp(float(timestamp_str))
                    except ValueError:
                        raise ValueError(f"Unrecognized timestamp format: {timestamp_str}")
                for i, node in enumerate(keys):
                    idx = 1 + i * 4  
                    vals = row[idx:idx+4]
  
                    if all(v == '' for v in vals):
                        continue
                    shm_dict = {}
                    for key, val in zip(['used', 'sending', 'freeing', 'free'], vals):
                        if val != '':
                            shm_dict[key] = float(val)

                    if node not in shm_usage:
                        shm_usage[node] = {}
                    shm_usage[node][timestamp] = shm_dict
    
        self.shm_usage = shm_usage
        #print(shm_usage['entry_node_htc-cmp506'])
    
    
    def deserialize_shm_usage_build_nodes(self):
        csv_file_name = self.get_csv_file_name_shm_usages()
        shm_usage = {}
    
        with open(csv_file_name, newline='') as csvfile:
            reader = csv.reader(csvfile)
            first_header = next(reader)  
            second_header = next(reader) 
            third_header = next(reader) 
    
            node_keys = []
            prev_build_node = ''
            for i in range(1, len(first_header), 3): 
                build_node = first_header[i]
                entry_node = second_header[i]
                if build_node == '':    
                    node_keys.append((prev_build_node, int(entry_node)))
                else:
                    prev_build_node = build_node
                    node_keys.append((build_node, int(entry_node)))
    
            for row in reader:
                timestamp_str = row[0]
                try:
                    timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    try:
                        timestamp = datetime.fromtimestamp(float(timestamp_str))
                    except ValueError:
                        raise ValueError(f"Invalid timestamp: {timestamp_str}")
    
                for i, (build_node, entry_node) in enumerate(node_keys):
                    idx = 1 + i * 3  
                    vals = row[idx:idx+3]

                    if all(v == '' for v in vals):
                        continue

                    shm_dict = {}
                    for key, val in zip(['used', 'freeing', 'free'], vals):
                        if val != '':
                            shm_dict[key] = float(val)

                    if build_node not in shm_usage:
                        shm_usage[build_node] = {}
                    if entry_node not in shm_usage[build_node]:
                        shm_usage[build_node][entry_node] = {}
                    shm_usage[build_node][entry_node][timestamp] = shm_dict
    
        self.shm_usage = shm_usage
    
    