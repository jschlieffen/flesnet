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

# =============================================================================
# TODO: Search the Bottleneck. Very likely in the tail funct.
# =============================================================================
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

#it seems as it is a problem with the number of refreshings
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

def tail_file(file_path):
    with open(file_path, 'r') as file:

        file.seek(0, 2)
        while True:
            line = file.readline()
            if not line:
                time.sleep(0.01) 
                continue
            yield line

def main(stdscr,file_names, num_entry_nodes, num_build_nodes):

    data_dict = {}
    #last_update = time.time()
    for file_name in file_names:
        data_dict[file_name[0]] = {
            'current_data' : 0.0,
            'tail' : tail_file(file_name[0]),
            'total_data' : file_name[1]
            }
    '''
    with open('test.txt', 'w') as file:
        for key,val in data_dict.items():
            file.write(key)
    '''

    while True:
        for key,val in data_dict.items():
            try:
                line = next(val['tail'])
                data_rate = get_data_rate(line)
                data_dict[key]['current_data'] += data_rate
            except StopIteration:
                data_rate = 0.0
        #current_time = time.time()
        draw_progress_bar(stdscr, data_dict, num_entry_nodes, num_build_nodes)
        #if current_time - last_update >= 0.2:
            #draw_progress_bar(stdscr, data_dict, num_entry_nodes, num_build_nodes)
            #last_update = current_time
    stdscr.refresh()


