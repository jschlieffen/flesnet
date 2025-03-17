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

def get_data_rate(log_line):
    match = re.search(r'(\d+\.\d+)\sGB/s', log_line)
    if match:
        return float(match.group(1))
        #return 
    return 0.0

def calculate_progress(current_data, total_data):
    return current_data / total_data

def calc_outout_str(input_string):
    
    #log_path = "logs/build_node_htc-cmp12.log"  # Example log path
    
    # Regular expression to capture the required parts
    pattern = r"logs/(build|entry)_node_(.+?)\.log"
    
    match = re.search(pattern, input_string)
    if match:
        node_type = match.group(1)  # 'build' or 'entry'
        node_id = match.group(2)    # 'htc-cmp12' or similar
        formatted_output = f"{node_type} node: {node_id}"
        #print(formatted_output)
        return formatted_output
    #else:
        #print("No match found.")

def draw_progress_bar(stdscr, data_dict):
    stdscr.clear()
    bar_width = 50
    
    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK) 
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)   
    curses.init_pair(3, curses.COLOR_MAGENTA, curses.COLOR_BLACK) 
    i = 0
    for key,val in data_dict.items():
        progress = calculate_progress(val['current_data'], val['total_data'])
        #with open('prog.txt', 'w') as file:
            #file.write(str(progress)+ ' \n')
            #file.write(key + ' \n')
        #print(key)
        output_str = calc_outout_str(key)
        green = u'\u2500' * int(progress * bar_width)
        red = u'\u2500' * (bar_width - len(green))
        
        stdscr.addstr(i, 0, "Progress Bar " + output_str + ': ')
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
                time.sleep(0.1) 
                continue
            yield line

def main(stdscr,file_names):

    data_dict = {}

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
        draw_progress_bar(stdscr, data_dict)
    stdscr.refresh()
    time.sleep(2)


