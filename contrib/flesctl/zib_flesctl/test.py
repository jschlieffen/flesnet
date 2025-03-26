#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 26 12:05:44 2025

@author: jschlieffen
"""

import re
import time
import sys
import os
import curses
import select
import subprocess
import plotext as plt
import threading


def create_graph(stdscr, data_dict):
    #data = {}
    #for key,val in data_dict.items():
        #data[key] = {
                #'data' : [val['current_data']]
            #}
    while True:
        #data.append(new_value)
        #for key,val in data_dict.items():
            #print('test')
            #data[key]['data'].append(val['current_data'])
            #if len(data[key]['data']) > 20:
                #data[key]['data'].pop(0)
    
            
        stdscr.move(15, 0)  
            
        plt.clf()  
        colors = [1, 2, 3, 4, 5, 6, 7, 8] 
        markers = ['.', 'o', 'x', '^', 's', 'd', 'p', '*']
        for idx, (key,val) in enumerate(data_dict.items()):
            data = val['data_array']
            while True:
                if len(data) > 20:
                    data.pop(0)
            color_idx = (idx % len(colors)) + 1
            marker_idx = idx % len(markers) 
            #plt.plot(val['data_array'], label=key, color=color_idx)
            plt.plot(data, label=key, marker=markers[marker_idx], color=color_idx)
            #plt.plot(val['data_array'], label=key)
        plt.title("Real-Time Data Plot")
        plt.ylim(0, 100)  
        #plt.legend()
        plt.show()  
        sys.stdout.flush()
        #print(f"Latest Value: {new_value}")
        #print(f"Average Value: {sum(data) / len(data):.2f}")
        #print(f"Data Points: {data}")

        time.sleep(1)  
                
            
def tail_file(file_path):
    f = subprocess.Popen(['tail','-F',file_path],\
            stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    p = select.poll()
    p.register(f.stdout)
    
    while True:
        if p.poll(1):
            yield str(f.stdout.readline())
        time.sleep(0.5)

def main(stdscr,file_names, num_entry_nodes, num_build_nodes):

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
    plot_thread = threading.Thread(target=create_graph, args=(stdscr,data_dict))
    plot_thread.daemon = True
    plot_thread.start()

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
        time.sleep(1)
        #draw_progress_bar(stdscr, data_dict, num_entry_nodes, num_build_nodes)
        #if current_time - last_update >= 0.2:
            #draw_progress_bar(stdscr, data_dict, num_entry_nodes, num_build_nodes)
            #last_update = current_time
    stdscr.refresh()