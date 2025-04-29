#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 29 10:32:50 2025

@author: jschlieffen
"""

import csv
import Logfile_reader as LR

# =============================================================================
# Write this for both entry and build nodes
# =============================================================================
class serialize_data:
    
    def __init__(self,timestamps,data_rates,shm_usage,file_name):
        #self.timestamps = timestamps
        self.data_rate = data_rates
        self.shm_usage = shm_usage
        self.file_name = file_name
        
        
    def get_time_stmps(self,data_rates):
        largest_key = max(data_rates, key=lambda k: len(data_rates[k]))
        largest_dict = data_rates[largest_key]
        timestamps = [key for key in largest_dict.keys()]
        return timestamps
    
    
    def serialize_data_rates(self):
        csv_file_name = f"data_rates_{self.file_name}.csv"
        timestamps = self.get_time_stmps(self.data_rates)
        with open(csv_file_name, "w", newline='') as csvfile:
            writer = csv.writer(csvfile)
            header = ['timestamps'] + list(self.data_rate.keys())
            
            for timestamp in self.timestamps:
                row = [timestamp]
                for val in self.data_rates.values():
                    row.append(val.get(timestamp,''))
                writer.writerow(row)
    
    def serialize_shm_usage(self):
        return None
    
    