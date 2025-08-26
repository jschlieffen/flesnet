#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 25 12:15:18 2025

@author: jschlieffen
"""

import os
import monitoring
import curses
os.chdir('monitoring/')

with open("pids_monitoring.txt", "w") as f:
    f.write(str(os.getpid()))
    
    
def get_params():
    file_names = []
    
    with open('mon_parameters.txt', 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith("file_name:"):
                _, data = line.split("file_name: ")
                logfile, file_data = data.split(", ")
                file_names.append((logfile, int(file_data)))
            elif line.startswith("num_buildnodes:"):
                num_buildnodes = int(line.split(": ")[1])
            elif line.startswith("num_entrynodes:"):
                num_entrynodes = int(line.split(": ")[1])
            elif line.startswith("enable_graph:"):
                enable_graph = line.split(": ")[1] == '1'
            elif line.startswith("enable_progess_bar:"):
                enable_progess_bar = line.split(": ")[1] == '1'
    return file_names, num_buildnodes, num_entrynodes, enable_graph, enable_progess_bar

with open("monitoring.log", "w") as log_file:
    try:
        file_names, num_buildnodes, num_entrynodes, enable_graph, enable_progress_bar = get_params()
        #log_file.write(file_names)
        #log_file.write('test123 \n')
        #for file in file_names:    
            #log_file.write(file[0] + '\n')
            #log_file.write(str(os.path.isfile(file[0])))
        #log_file.write(str(os.getcwd()) + '\n')
        #log_file.write(str(enable_graph) + '\n')
        total_data, avg_data_rate = curses.wrapper(monitoring.main,file_names, 
                                                   num_buildnodes, 
                                                   num_entrynodes, 
                                                   enable_graph, 
                                                   enable_progress_bar)
        log_file.write(f'total_data: {total_data} \n')
        log_file.write(f'avg_data_rate: {avg_data_rate} \n')
    except Exception as e:
        log_file.write(f"Error: {e}\n")
        print(f"Error: {e}")
