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
from contextlib import redirect_stdout
import signal
from log_msg import *

terminate_program = False

def get_data_rate(log_line):
    match = re.search(r'(\d+\.\d+)\sGB/s', log_line)
    if match:
        return float(match.group(1))
    match = re.search(r'(\d+\.\d+)\sMB/s', log_line)
    if match:
        return float(match.group(1))/1000
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
    #stdscr.clear()
    bar_width = 50
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
        stdscr.addstr(green, curses.color_pair(2))
        stdscr.addstr(red, curses.color_pair(1))   
        stdscr.addstr(f" {val['current_data']:12.2f} / {val['total_data']:.2f}", curses.color_pair(3))  
        i += 1
        


def strip_and_translate_ansi_escape_sequences(text):
    ansi_escape = re.compile(r'\x1b\[[0-9;]*[m]')
    color_codes = []
    result_text = []
    last_pos = 0
    
    def replace_with_curses(match):
        code_str = match.group(0)
        color_code = None
        nonlocal last_pos
        if ';' not in code_str:  
            try:
                color_code = int(code_str[2][:-1]) 
            except ValueError:
                return ''  
        elif '38;5;' in code_str:
            try:
                color_code = int(code_str.split(';')[2][:-1]) 
            except ValueError:
                return '' 
            
        if color_code is not None:
            text_segment = text[last_pos:match.start()]
            clean_segment = ansi_escape.sub('', text_segment)
            if text_segment:
                result_text.append(('text', clean_segment))  
            result_text.append(('color', color_code))  
            last_pos = match.end()  
            return '' 

        return ''
    
    processed_txt = ansi_escape.sub(replace_with_curses, text)

    if last_pos < len(text):
        text_segment = text[last_pos:]
        clean_segment = ansi_escape.sub('', text_segment) 
        if clean_segment:
            result_text.append(('text', clean_segment))


    return result_text


def init_color_pairs_v2():
    curses.use_default_colors()
    for i in range(0, curses.COLORS):
        curses.init_pair(i, i, -1)

def draw_Graph(stdscr, data_dict):
    curses.start_color()

    plt.clf()
    for idx, (key,val) in enumerate(data_dict.items()):
        data = val['data_array']
        while True:
            if len(data) > 20:
                data.pop(0)
            else:
                break
        lbl = calc_outout_str(key)
        plt.plot(data, label=lbl)
        
    plt.theme("dark")
    plt.title("data rate")
    plt.plot_size(80,20)
    buf = io.StringIO()
    with redirect_stdout(buf):
        plt.show()
    plot_str = buf.getvalue()
    max_y, max_x = stdscr.getmaxyx()  
    lines = plot_str.splitlines()
    for i, line in enumerate(lines):
        if i < max_y - 1:  
            result_arr = strip_and_translate_ansi_escape_sequences(line)         
            color_pair = 0
            char = ''
            y, x = 0, 0
            was_prev_color = False
            count = 0
            for j,tup in enumerate(result_arr):
                if tup[0] == 'color':
                    color_pair = tup[1]
                    was_prev_color = True
                elif tup[0] == 'text':
                    char = tup[1]
                    stdscr.addstr(i+15,x,char, curses.color_pair(int(color_pair)))
                    was_prev_color = False
                    count += 1
                    
                    x += len(char)
            x = 0

def tail_file_v2(file_path):
    f = subprocess.Popen(['tail','-F',file_path],\
            stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    p = select.poll()
    p.register(f.stdout)
    
    while True:
        if p.poll(1):
            yield str(f.stdout.readline())
        time.sleep(0.5)
        
def tail_file(file_path):
    f = subprocess.Popen(['tail', '-F', file_path],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    while True:
        # Using select.select to check if there's data ready to read
        rlist, _, _ = select.select([f.stdout], [], [], 1)  # 1-second timeout
        if rlist:
            yield str(f.stdout.readline(), 'utf-8').strip()

def main(stdscr,file_names, num_entry_nodes, num_build_nodes,enable_graph,enable_progress_bar):
    global terminate_program
    signal.signal(signal.SIGINT, lambda signum, frame: signal_handler(signum, frame, stdscr))
    signal.signal(signal.SIGTERM, lambda signum, frame: signal_handler(signum, frame, stdscr))
    stdscr.clear()
    data_dict = {}
    init_color_pairs_v2()
    for file_name in file_names:
        data_dict[file_name[0]] = {
            'current_data' : 0.0,
            'tail' : tail_file(file_name[0]),
            'total_data' : file_name[1], 
            'data_array' : []
            }
    while True:
        if terminate_program:
            break
        for key,val in data_dict.items():
            try:
                line = next(val['tail'])
                data_rate = get_data_rate(line)
                data_dict[key]['current_data'] += data_rate
                data_dict[key]['data_array'].append(data_rate)
            except StopIteration:
                data_rate = 0.0
        time.sleep(1)
        if enable_progress_bar:
            draw_progress_bar(stdscr, data_dict, num_entry_nodes, num_build_nodes)
        if enable_graph:
            draw_Graph(stdscr,data_dict)
        stdscr.refresh()
    #cleanup(stdscr)
    total_data, avg_data_rate = calc_output_msg(data_dict)
    return total_data, avg_data_rate
    
def calc_output_msg(data_dict):
    total_data = 0
    avg_data_rate = 0
    it_counter = 0
    for key,val in data_dict.items():
        if 'entry_node' in key:
            total_data += val['current_data']
            for data_rate in val['data_array']:
                if data_rate > 0:
                    avg_data_rate += data_rate
                    it_counter += 1
    avg_data_rate = avg_data_rate/it_counter
    return total_data, avg_data_rate
        
def signal_handler(signum, frame,stdscr):
    if signum == signal.SIGINT:
        logger.error(f'received signal {signum}. Handling termination')
        #print(f'\033[31mERROR: received signal {signum}. Handling termination')
    elif signum == signal.SIGTERM:
        #print(f'\033[31mERROR: received signal {signum}. Handling termination')
        logger.error(f'received signal {signum}. Handling termination')
    cleanup(stdscr)

def cleanup(stdscr):
    global terminate_program
    if stdscr is not None:
        curses.endwin()
    #sys.exit(0)
    terminate_program = True
