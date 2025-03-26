#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 26 15:20:28 2025

@author: jschlieffen
"""

import plotext as plt
import random
import curses
import time
import subprocess
import select
import re

def get_data_rate(log_line):
    match = re.search(r'(\d+\.\d+)\sGB/s', log_line)
    if match:
        return float(match.group(1))
    return 0.0

def tail_file(file_path):
    f = subprocess.Popen(['tail','-F',file_path],\
            stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    p = select.poll()
    p.register(f.stdout)
    
    while True:
        if p.poll(1):
            yield str(f.stdout.readline())
        time.sleep(0.5)

def main(file_names):
    data_dict = {}
    #last_update = time.time()
    for file_name in file_names:
        data_dict[file_name[0]] = {
            'current_data' : 0.0,
            'tail' : tail_file(file_name[0]),
            'total_data' : file_name[1], 
            'data_array' : []
            }
    '''
    with open('test.txt', 'w') as file:
        for key,val in data_dict.items():
            file.write(key)
    '''
    #plot_thread = threading.Thread(target=create_graph, args=(stdscr,data_dict))
    #plot_thread.daemon = True
    #plot_thread.start()

    while True:
        for key,val in data_dict.items():
            try:
                line = next(val['tail'])
                data_rate = get_data_rate(line)
                data_dict[key]['current_data'] += data_rate
                data_dict[key]['data_array'].append(data_rate)
            except StopIteration:
                data_rate = 0.0
        #current_time = time.time()
        #time.sleep(1)
        create_graph(data_dict)
        #draw_progress_bar(stdscr, data_dict, num_entry_nodes, num_build_nodes)
        #if current_time - last_update >= 0.2:
            #draw_progress_bar(stdscr, data_dict, num_entry_nodes, num_build_nodes)
            #last_update = current_time
    #stdscr.refresh()

# Function to generate random data
def generate_data():
    return [random.uniform(0, 7) for _ in range(20)]

def create_graph(data_dict):
    plt.clf()
    for idx, (key,val) in enumerate(data_dict.items()):
        data = val['data_array']
        while True:
            if len(data) > 20:
                data.pop(0)
            else:
                break
        #color_idx = (idx % len(colors)) + 1
        #marker_idx = idx % len(markers) 
        #plt.plot(val['data_array'], label=key, color=color_idx)
        plt.plot(data, label=key)
    plt.theme("dark")
    plt.title("random num")
    plt.show()
    time.sleep(1)

#main()