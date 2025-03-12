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

def monitoring_V2(file_name, data_size):
    with open(file_name,'r') as file:
        #print(file.read())
        file.seek(0,2)
        data_sended = 0
        while(True):
            line = file.readline()
            if line:
                #print(line.strip())
                string = line.strip()
                pattern = r'(\d+\.\d+)\sGB/s'
                data_rate = re.search(pattern,string)
                if data_rate:
                    #print(data_rate.group(1))
                    data_rate_int = float(data_rate.group(1))
                    data_sended += data_rate_int
                    line_length = 50
                    green_length = int((data_sended / data_size) * line_length)  # How many are green
                    red_length = line_length - green_length  # The rest are red

                    # Create the visual representation: green part and red part
                    green_part = '\033[32m' + '-' * green_length  # Green part
                    red_part = '\033[31m' + '-' * red_length  # Red part

                    # Build the output string, including the counter value
                    line = f'[{green_part}{red_part}] {data_sended}/{data_size}\033[0m'  # Reset color after printing

                    # Print the line and overwrite it in place
                    sys.stdout.write('\r' + line)
                    sys.stdout.flush()
            else:
                time.sleep(1)

def tail_V3(file):
    file.seek(0, os.SEEK_END)  # Go to the end of the file
    while True:
        line = file.readline()
        if not line:  # No new line, wait for new data
            time.sleep(1)  # Wait a second before checking again
            continue
        yield line

def monitoring_V3(file_name,data_size):
    data_sended = 0
    with open(file_name,'r') as file:
        for line in tail(file):
            string = line.strip()
            pattern = r'(\d+\.\d+)\sGB/s'
            data_rate = re.search(pattern, string)
            if data_rate:
                data_rate_int = float(data_rate.group(1))
                data_sended += data_rate_int
                line_length = 50
                green_length = int((data_sended / data_size) * line_length)  
                red_length = line_length - green_length
                green_part = '\033[32m' + u'\u2500' * green_length  
                red_part = '\033[31m' + u'\u2500' * red_length  
                line = f'{green_part}{red_part} \033[35m{data_sended}/{data_size}\033[0m' 
                sys.stdout.write('\r' + line)
                sys.stdout.flush()

                
def tail(file):
    file.seek(0, os.SEEK_END)
    while True:
        line = file.readline()
        if not line:
            time.sleep(1)
            continue
        yield line

def monitoring(file_name, data_size, progress_bar_number, file_iter):
    """Monitor a file's progress and update a progress bar."""
    data_sended = 0
    for line in file_iter:
        string = line.strip()
        pattern = r'(\d+\.\d+)\sGB/s'
        data_rate = re.search(pattern, string)
        if data_rate:
            data_rate_int = float(data_rate.group(1))
            data_sended += data_rate_int
            line_length = 50
            green_length = int((data_sended / data_size) * line_length) 
            red_length = line_length - green_length 
            green_part = '\033[32m' + u'\u2500' * green_length 
            red_part = '\033[31m' + u'\u2500' * red_length 
            line = f'Progress Bar {progress_bar_number}: {green_part}{red_part} \033[35m{data_sended}/{data_size}\033[0m' 
            sys.stdout.write('\r' + line)
            sys.stdout.flush()

def sequential_monitoring(file_names, data_sizes):
    """Monitor multiple files sequentially line by line."""
    file_iters = [tail(open(file_name, 'r')) for file_name in file_names]  
    progress_bar_number = 1
    print(file_iters)
    while True:
        for i in range(len(file_iters)):
            file_iter = file_iters[i]
            file_name = file_names[i]
            data_size = data_sizes[i]
            
            monitoring(file_name, data_size, progress_bar_number, file_iter)
            
            progress_bar_number += 1
            print()

    



def get_data_rate(log_line):
    match = re.search(r'(\d+\.\d+)\sGB/s', log_line)
    if match:
        return float(match.group(1))
        #return 
    return 0.0

def calculate_progress(current_data, total_data):
    return current_data / total_data

def draw_progress_bar(stdscr, data_dict):
    stdscr.clear()
    bar_width = 50
    
    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK) 
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)   
    curses.init_pair(3, curses.COLOR_MAGENTA, curses.COLOR_BLACK) 
    '''
    green1 =  u'\u2500' * int(progress1 * bar_width)
    red1 =  u'\u2500' * (bar_width - len(green1))
    green2 = u'\u2500'* int(progress2 * bar_width)
    red2 = u'\u2500'* (bar_width - len(green2))


    stdscr.addstr(0, 0, "Progress Bar 1: ")
    stdscr.addstr(green1, curses.color_pair(1))
    stdscr.addstr(red1, curses.color_pair(2))   
    stdscr.addstr(f" {current_data1:12.2f} / {total_data_1:.2f}", curses.color_pair(3))  # Pink numbers

    stdscr.addstr(1, 0, "Progress Bar 2: ")
    stdscr.addstr(green2, curses.color_pair(1)) 
    stdscr.addstr(red2, curses.color_pair(2)) 
    stdscr.addstr(f" {current_data2:12.2f} / {total_data_2:.2f}", curses.color_pair(3))  # Pink numbers
    '''
    '''
    with open('test.txt', 'w') as file:
        for key,val in data_dict.items():
            file.write(key)
    '''
    i = 0
    for key,val in data_dict.items():
        progress = calculate_progress(val['current_data'], val['total_data'])
        with open('prog.txt', 'w') as file:
            file.write(str(progress)+ ' \n')
            file.write(key + ' \n')
        #print(key)
        green = u'\u2500' * int(progress * bar_width)
        red = u'\u2500' * (bar_width - len(green))
        
        stdscr.addstr(i, 0, "Progress Bar " + key + ': ')
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

    #total_data_1 = 1000.0
    #total_data_2 = 2000.0
    #start_time = time.time()


    #current_data1 = 0.0
    #current_data2 = 0.0
    #tail_a = tail_file(file_a)
    #tail_b = tail_file(file_b)
    data_dict = {}
    #i = 0
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
    '''
    # Main loop to read both files
    while True:
        # Open the files and read the latest line
        with open(file_a, 'r') as f1, open(file_b, 'r') as f2:
            lines_a = f1.readlines()
            lines_b = f2.readlines()
        
        # Assuming the last line in each file has the most recent data
        if lines_a:
            data_rate_a = get_data_rate(lines_a[-1])
            #print(data_rate_a)
            current_data1 += data_rate_a * (time.time() - start_time) / 1000  # GB (adjust as needed)

        if lines_b:
            data_rate_b = get_data_rate(lines_b[-1])
            current_data2 += data_rate_b * (time.time() - start_time) / 1000  # GB (adjust as needed)

        # Calculate the progress of both files
        progress1 = calculate_progress(current_data1, total_data_1)
        progress2 = calculate_progress(current_data2, total_data_2)

        # Draw the progress bars
        draw_progress_bar(stdscr, progress1, progress2, total_data_1, total_data_2, current_data1, current_data2)

        # Pause for a short moment to update the screen (10 ms)
        time.sleep(0.01)

        # Stop when the progress reaches 100%
        if progress1 >= 1.0 and progress2 >= 1.0:
            break

    # Final message
    stdscr.addstr(2, 0, "Both transfers complete!")
    stdscr.refresh()
    time.sleep(2)
    '''
    while True:
        '''
        try:
            line_a = next(tail_a)
            data_rate_a = get_data_rate(line_a)
            current_data1 += data_rate_a 
        except StopIteration:
            data_rate_a = 0.0
    
        try:
            line_b = next(tail_b)
            data_rate_b = get_data_rate(line_b)
            current_data2 += data_rate_b 
        except StopIteration:
            data_rate_b = 0.0

        progress1 = calculate_progress(current_data1, total_data_1)
        progress2 = calculate_progress(current_data2, total_data_2)

        draw_progress_bar(stdscr, progress1, progress2, total_data_1, total_data_2, current_data1, current_data2)
        if progress1 >= 1.0 and progress2 >= 1.0:
            break
        '''
        for key,val in data_dict.items():
            #print('test1223')
            #stdscr.addstr(key)
            try:
                #print('test1223')
                #print(val['tail'])
                line = next(val['tail'])
                data_rate = get_data_rate(line)
                data_dict[key]['current_data'] += data_rate
            except StopIteration:
                data_rate = 0.0
            #progress = calculate_progress(data_dict[key]['current_data'], total_data_1)
        draw_progress_bar(stdscr, data_dict)
                

    #stdscr.addstr(2, 0, "Both transfers complete!")
    stdscr.refresh()
    time.sleep(2)



'''
input_string = "[16:27:26] STATUS: [i0]   |###########x....____|__________| 6.161 GB/s (4.106 kHz) FLES E001"

pattern = r'(\d+\.\d+)\sGB/s'


match = re.search(pattern, input_string)

if match:
    data_rate = match.group(1)  # Extract the numerical part of the data rate
    print(f"Data rate: {data_rate} GB/s")
else:
    print("Data rate not found.")
'''
