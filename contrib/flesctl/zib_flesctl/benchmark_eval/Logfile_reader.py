#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 25 12:39:46 2025

@author: jschlieffen
"""

import re
from datetime import datetime


# =============================================================================
# This file reads the collectl-logfile obtained by flesctrl
# =============================================================================
class Logfile_reader_entry_node:
    
    def __init__(self,Logfile_name):
        self.Logfile = self.read_file(Logfile_name)
        self.data_rate = {}
        self.data_shms = {}

    def read_file(self, Logfile_name):
        with open(Logfile_name, "r") as file:
            return file.readlines()
        
    def extract_timestamp(self,log_line):
        match = re.search(r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]", log_line)
        if match:
            timestamp_str = match.group(1)
            return datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        else:
            return None
        
        
    def extract_data_rates(self):
        for line in self.Logfile:
            if "STATUS:" in line or "INFO:" in line:
                
                data_rate = self.get_data_rate(line)
                if data_rate is not None:
                    time_stmp = self.extract_timestamp(line)
                    self.data_rate[time_stmp] = data_rate 
                
                
    def get_data_rate(self,log_line):
        match = re.search(r'(\d+\.\d+)\sGB/s', log_line)
        if match:
            return float(match.group(1))
        match = re.search(r'(\d+\.\d+)\sMB/s', log_line)
        if match:
            return float(match.group(1))/1000
        return None # This line returns 0
    
    def extract_data_shms_entry_node(self):
         for line in self.Logfile:
             if 'DEBUG:' in line and 'data' in line:
                 vals = self.get_shm_usage_entry_node(line)
                 if vals:    
                     time_stmp = self.extract_timestamp(line)
                     self.data_shms[time_stmp] = {
                             'used' : vals[0],
                             'sending' : vals[1],
                             'freeing' : vals[2],
                             'free' : vals[3]
                         }

    def get_shm_usage_entry_node(self,log_line):
        match = re.search(r"data\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)", log_line)
        if match:
            return tuple(float(val) for val in match.groups())
        else:
            return None        
        
    

            
class Logfile_reader_build_node:
    
    def __init__(self,Logfile_name):
        self.Logfile = self.read_file(Logfile_name)
        self.data_rate = {}
        self.data_shms = {}
        
        
    def read_file(self, Logfile_name):
        with open(Logfile_name, "r") as file:
            return file.readlines()
        
    def extract_timestamp(self,log_line):
        match = re.search(r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]", log_line)
        if match:
            timestamp_str = match.group(1)
            return datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        else:
            return None
        
        
    def extract_data_rates(self):
        for line in self.Logfile:
            if "STATUS:" in line or "INFO:" in line:
                
                data_rate = self.get_data_rate(line)
                if data_rate is not None:
                    time_stmp = self.extract_timestamp(line)
                    self.data_rate[time_stmp] = data_rate 
                
                
    def get_data_rate(self,log_line):
        match = re.search(r'(\d+\.\d+)\sGB/s', log_line)
        if match:
            return float(match.group(1))
        match = re.search(r'(\d+\.\d+)\sMB/s', log_line)
        if match:
            return float(match.group(1))/1000
        return None # This line returns 0
    
    
    def extract_data_shms_build_node(self):
        get_index = False
        for line in self.Logfile:
            if 'DEBUG:' in line and 'data' in line:
                vals = self.get_shm_usage_build_nodes(line)
                get_index = True
            elif get_index == True:
                time_stmp = self.extract_timestamp(line)
                entry_node_idx = self.get_entry_node_index(line)
                if entry_node_idx not in self.data_shms:
                    self.data_shms[entry_node_idx] = {}
                self.data_shms[entry_node_idx][time_stmp] = {
                        'used' : vals[0],
                        'freeing' : vals[1],
                        'free' : vals[2]
                    }
                get_index = False
        
    def get_shm_usage_build_nodes(self,log_line):
        match = re.search(r"data\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)", log_line)
        if match:
            return tuple(float(val) for val in match.groups())
        else:
            return None     
        
    def get_entry_node_index(self,log_line):
        match = re.search(r"\[c\d+_(\d+)\]", log_line)
        if match:
            return int(match.group(1))
        else:
            return None

def main():
    Logfile_reader_cls = Logfile_reader_entry_node("../logs/flesnet/entry_nodes/entry_node_htc-cmp108.log")
    #for line in Logfile_reader_cls.Logfile:
       # print(line)
    Logfile_reader_cls.extract_data_rates()
    Logfile_reader_cls.extract_data_shms_entry_node()
    
    for key,val in Logfile_reader_cls.data_rate.items():
        print(f'time_stamp: {key}, data rate: {val}')
    
    for key,val in Logfile_reader_cls.data_shms.items():
        print(f"time_stamp: {key}, shm: used: {val['used']}, sending: {val['sending']}, freeing: {val['freeing']}, free: {val['free']}")
        
    Logfile_reader_cls_v2 = Logfile_reader_build_node("../logs/flesnet/build_nodes/build_node_htc-cmp509.log")
    
    Logfile_reader_cls_v2.extract_data_rates()
    Logfile_reader_cls_v2.extract_data_shms_build_node()
    
    for key,val in Logfile_reader_cls_v2.data_rate.items():
        print(f'time_stamp: {key}, data rate: {val}')
    
    for key1,val1 in Logfile_reader_cls_v2.data_shms.items():
        print(f"shm for entry node: {key1}")
        for key,val in val1.items():
            print(f"time_stamp: {key}, used: {val['used']}, freeing: {val['freeing']}, free: {val['free']}")

if __name__ == '__main__':
    main()