#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 25 12:39:46 2025

@author: jschlieffen
"""

import re
from datetime import datetime

class Logfile_reader:
    
    def __init__(self,Logfile_name,Logfile_type):
        self.Logfile = self.read_file(Logfile_name)
        self.Logfile_type = Logfile_type
        self.data_rate = {}
        self.data_shms = {}
        self.extract_data_rates()
        self.extract_data_shms()
        
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
    
    def extract_data_shms(self):
         for line in self.Logfile:
             if 'DEBUG:' in line and 'data' in line:
                 vals = self.get_shm_usage(line)
                 if vals:    
                     time_stmp = self.extract_timestamp(line)
                     self.data_shms[time_stmp] = {
                             'used' : vals[0],
                             'sending' : vals[1],
                             'freeing' : vals[2],
                             'free' : vals[3]
                         }

    def get_shm_usage(self,log_line):
        match = re.search(r"data\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)", log_line)
        if match:
            return tuple(float(val) for val in match.groups())
        else:
            return None        
        
        
def main():
    Logfile_reader_cls = Logfile_reader("../logs/flesnet/entry_nodes/entry_node_htc-cmp108.log", "entry_node")
    for line in Logfile_reader_cls.Logfile:
        print(line)
    
    for key,val in Logfile_reader_cls.data_rate.items():
        print(f'time_stamp: {key}, data rate: {val}')
    
    for key,val in Logfile_reader_cls.data_shms.items():
        print(f"time_stamp: {key}, shm: used: {val['used']}, sending: {val['sending']}, freeing: {val['freeing']}, free: {val['free']}")

if __name__ == '__main__':
    main()