
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
        dir = os.getcwd()
        if node_type == "entry_nodes":
            path = os.path.join(dir,'collectl/data/data_rates/entry_nodes')
        elif node_type == "build_nodes":
            path = os.path.join(dir,'collectl/data/data_rates/build_nodes')
        elif node_type == 'receiving_nodes':
            path = os.path.join(dir,'collectl/data/data_rates/receiving_nodes')
        #print(node_type)
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
                    for key in self.data_rate[node_type].keys():
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
                        elif node_type == 'receiving_nodes':
                            row.extend([vals.get('KBIn','')])
                    writer.writerow(row)
        
    def get_csv_file_name_cpu_usages(self, node_type):
        dir = os.getcwd()
        if node_type == "entry_nodes":
            path = os.path.join(dir,'collectl/data/cpu_usages/entry_nodes')
        elif node_type == "build_nodes":
            path = os.path.join(dir,'collectl/data/cpu_usages/build_nodes')
        elif node_type == 'receiving_nodes':
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
        elif node_type == "receiving_nodes":
            csv_file_name = f"{path}/cpu_usages_receiving_nodes_{Run_id}.csv"
        return csv_file_name
    
    def serialize_cpu_usage(self):
        for node_type in self.cpu_usage.keys():
            csv_file_name = self.get_csv_file_name_cpu_usages(node_type)
            timestamps = self.get_time_stmps(self.cpu_usage[node_type])
            with open(csv_file_name, "w", newline='') as csvfile:
                writer = csv.writer(csvfile)
                header = ['timestamps']
                second_header = ['timestamps']
                alloc_cpus = {}
                for key,val in self.cpu_usage[node_type].items():
                    #header.extend([key] + ['']*(len(val)-1))
                    cpu_cnt = 0
                    first_timestmp = next((item for item in timestamps if item in val), None)
                    alloc_cpus[key] = [cpu for cpu in val[first_timestmp].keys()]
                    for cpu in alloc_cpus[key]:
                        second_header.extend([cpu])
                        cpu_cnt += 1
                    header.extend([key] + ['']*(cpu_cnt-1))
                writer.writerow(header)
                writer.writerow(second_header)
                for timestamp in timestamps:
                    row = [timestamp]
                    for key,cpu_dict in self.cpu_usage[node_type].items():
                        val = cpu_dict.get(timestamp, {})
                        for cpu in alloc_cpus[key]:
                            cpu_val = val.get(cpu, '')
                            if cpu_val != '':
                                row.append(100 - cpu_val)
                            else:
                                row.append('')
                    writer.writerow(row)
                
                
class deserialize_data:
    
    def __init__(self,file_name, timeslice_forwarding_activated):
        
        self.timeslice_forwarding_activated = timeslice_forwarding_activated
        self.file_name = file_name
        self.data_rate = {}
        self.cpu_usage = {}
    
    
    def get_csv_file_name_data_rates(self,node_type):
        dir = os.getcwd()
        if node_type == "entry_nodes":
            path = os.path.join(dir,'collectl/data/data_rates/entry_nodes')
        elif node_type == "build_nodes":
            path = os.path.join(dir,'collectl/data/data_rates/build_nodes')
        elif node_type == 'receiving_nodes':
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
    
    
    def deserialize_data(self):
        node_types = ['entry_nodes', 'build_nodes']
        if self.timeslice_forwarding_activated:
            node_types.append('receiving_nodes')
        for node_type in node_types:
            csv_file_name = self.get_csv_file_name_data_rates(node_type)
            data_dict = {}
            with open(csv_file_name, 'r', newline='') as csvfile:
                reader = csv.reader(csvfile)
                first_header = next(reader)
                keys = [key for key in first_header if key != '' and key != 'timestamps']
                if node_type == 'build_nodes' and self.timeslice_forwarding_activated:
                    second_header = next(reader)
                for row in reader:
                    vals = ''
                    timestamp_str = row[0]
                    #print(timestamp_str)
                    try:
                        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        try:
                            timestamp = datetime.fromtimestamp(float(timestamp_str))
                        except ValueError:
                            raise ValueError(f"Unrecognized timestamp format: {timestamp_str}")
                    if node_type == 'build_nodes' and self.timeslice_forwarding_activated:
                        #print('test')
                        for i, node in enumerate(keys):
                            idx = 1 + i * 2  
                            vals = row[idx:idx+2]
          
                            if all(v == '' for v in vals):
                                continue
                            data_dict_tmp = {}
                            for key, val in zip(['KBIn', 'KBOut'], vals):
                                if val != '':
                                    data_dict_tmp[key] = self.auto_cast_number(val)

                            if node not in data_dict:
                                data_dict[node] = {}
                            data_dict[node][timestamp] = data_dict_tmp
                    elif node_type =='entry_nodes':
                        for i, node in enumerate(keys):
                            idx = 1 + i
                            vals = row[idx]
                            if vals != '':
                                data_dict_tmp = {
                                        'KBOut' : self.auto_cast_number(vals)
                                    }
                                if node not in data_dict:
                                    data_dict[node] = {}
                                data_dict[node][timestamp] = data_dict_tmp
                    elif node_type == 'receiving_nodes' or node_type =='build_nodes':
                        for i, node in enumerate(keys):
                            idx = 1 + i
                            vals = row[idx]
                            if vals != '':
                                data_dict_tmp = {
                                        'KBIn' : self.auto_cast_number(vals)
                                    }
                                if node not in data_dict:
                                    data_dict[node] = {}
                                data_dict[node][timestamp] = data_dict_tmp
                    
                
                
                self.data_rate[node_type] = data_dict
                
                
    def get_csv_file_name_cpu_usages(self, node_type):
        dir = os.getcwd()
        if node_type == "entry_nodes":
            path = os.path.join(dir,'collectl/data/cpu_usages/entry_nodes')
        elif node_type == "build_nodes":
            path = os.path.join(dir,'collectl/data/cpu_usages/build_nodes')
        elif node_type == 'receiving_nodes':
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
        elif node_type == "receiving_nodes":
            csv_file_name = f"{path}/cpu_usages_receiving_nodes_{Run_id}.csv"
        return csv_file_name

    def auto_cast_number(self,s):
        try:
            number = float(s)
            if number.is_integer():
                return int(number)
            return number
        except ValueError:
            raise ValueError(f"'{s}' is not a valid number")
    #KeyErrors for more then one node. Debug that 
    def deserialize_cpu_usage(self):
        node_types = ['entry_nodes', 'build_nodes']
        if self.timeslice_forwarding_activated:
            node_types.append('receiving_nodes')
        for node_type in node_types:
            csv_file_name = self.get_csv_file_name_cpu_usages(node_type)
            cpu_usage = {}
            with open(csv_file_name, 'r', newline='') as csvfile:
                reader = csv.reader(csvfile)
                first_header = next(reader)
                second_header = next(reader)
                #for
                node_indices = []
                keys = []
                for idx,name in enumerate(first_header):
                    if name not in ('','timestamps'):
                        node_indices.append(idx)
                        keys.append(name)
                for row in reader:
                    timestamp_str = row[0]
                    try:
                        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        try:
                            timestamp = datetime.fromtimestamp(float(timestamp_str))
                        except ValueError:
                            raise ValueError(f"Unrecognized timestamp format: {timestamp_str}")
                    for i in range(len(node_indices)):
                        #print('test')
                        idx = node_indices[i]
                        node = keys[i]
                        if i+1 < len(node_indices):
                            next_idx_node = node_indices[i+1]
                        else:
                            next_idx_node = len(second_header)
                        while idx < next_idx_node:
                            
                            cpu = (second_header[idx])
                            if cpu != 'overall_avg':
                                cpu = int(cpu)
                            try:
                                #vals = float(row[idx])
                                row_val = row[idx]
                                if row_val != '':
                                    vals = self.auto_cast_number(row_val)
                                    val = 100 - vals
                                    if node not in cpu_usage:
                                        cpu_usage[node] = {}
                                    if timestamp not in cpu_usage[node]:
                                        cpu_usage[node][timestamp] = {}
                                    cpu_usage[node][timestamp][cpu] = val
                                idx += 1
                            except (ValueError, IndexError):
                                #print('something')
                                #print(idx)
                                #print(row)
                                #print(node)
                                idx+=1
                                continue

                self.cpu_usage[node_type] = cpu_usage
                
                