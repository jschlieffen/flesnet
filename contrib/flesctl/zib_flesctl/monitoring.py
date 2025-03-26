#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 26 16:53:41 2025

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
import io
import contextlib

def get_data_rate(log_line):
    match = re.search(r'(\d+\.\d+)\sGB/s', log_line)
    if match:
        return float(match.group(1))
    return 0.0

def calculate_progress(current_data, total_data):
    return current_data / total_data

def calc_outout_str(input_string):
    
    pattern = r"logs/(build|entry)_node_(.+?)\.log"
    
    match = re.search(pattern, input_string)
    if match:
        node_type = match.group(1) 
        node_id = match.group(2)
        formatted_output = f"{node_type} node: {node_id}"
        return formatted_output

def draw_progress_bar(stdscr, data_dict, num_entry_nodes, num_build_nodes):
    stdscr.clear()
    bar_width = 50

    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK) 
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)   
    curses.init_pair(3, curses.COLOR_MAGENTA, curses.COLOR_BLACK) 
    curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    stdscr.addstr(0, 0, "Number of: ")
    stdscr.addstr("entry nodes: " + str(num_entry_nodes), curses.color_pair(4))
    stdscr.addstr(1,0, "           build nodes: " + str(num_build_nodes), curses.color_pair(5))
    i = 2
    for key,val in data_dict.items():
        progress = calculate_progress(val['current_data'], val['total_data'])
        output_str = calc_outout_str(key)
        green = u'\u2500' * int(progress * bar_width)
        red = u'\u2500' * (bar_width - len(green))
        if 'entry node' in output_str:
            stdscr.addstr(i, 0, output_str + ': ', curses.color_pair(4))
        elif 'build node' in output_str:
            stdscr.addstr(i, 0, output_str + ': ', curses.color_pair(5))
        else:
            stdscr.addstr(i, 0, output_str + ': ')
        stdscr.addstr(green, curses.color_pair(1))
        stdscr.addstr(red, curses.color_pair(2))   
        stdscr.addstr(f" {val['current_data']:12.2f} / {val['total_data']:.2f}", curses.color_pair(3))  
        i += 1
        
    stdscr.refresh()

def create_graph_v2(stdscr, data_dict):
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
        plt.show()  
        sys.stdout.flush()
        time.sleep(1)  
        
def create_graph(stdscr,data_dict):
    stdscr.clear()
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
    #plt.show()
    #plot_output= plt.figtext()
    # Create a StringIO buffer to capture the plot output

    # Create a StringIO buffer to capture the plot output
    #buf = io.StringIO()

    # Save the plot to the buffer (instead of printing it)
    #plt.savefig(buf)  # Save the plot as text to the buffer

    # Get the plot as a string from the buffer
    #plot_output = buf.getvalue()
    # Create a StringIO buffer to capture the plot output
    buf = io.StringIO()

    # Use contextlib.redirect_stdout to capture plt.show() output
    with contextlib.redirect_stdout(buf):
        plt.show()  # This will print the plot to the StringIO buffer

    # Get the plot as a string from the buffer
    plot_output = buf.getvalue()

    # Display the plot inside the curses window
    stdscr.addstr(0, 0, plot_output)  # Add the plot output to the curses window

    
    stdscr.addstr(0,0, plot_output)
    stdscr.refresh()
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
    #plot_thread = threading.Thread(target=create_graph, args=(data_dict))
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
        time.sleep(1)
        #draw_progress_bar(stdscr, data_dict, num_entry_nodes, num_build_nodes)
        #if current_time - last_update >= 0.2:
            #draw_progress_bar(stdscr, data_dict, num_entry_nodes, num_build_nodes)
            #last_update = current_time
        create_graph(stdscr,data_dict)
    stdscr.refresh()


