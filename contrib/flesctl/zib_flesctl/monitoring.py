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

def tail(file):
    file.seek(0, os.SEEK_END)  # Go to the end of the file
    while True:
        line = file.readline()
        if not line:  # No new line, wait for new data
            time.sleep(1)  # Wait a second before checking again
            continue
        yield line

def monitoring(file_name,data_size):
    data_sended = 0
    with open(file_name,'r') as file:
        for line in tail(file):
            string = line.strip()
            pattern = r'(\d+\.\d+)\sGB/s'
            data_rate = re.search(pattern, string)
            #print('test1224')
            if data_rate:
                #print('test123')
                data_rate_int = float(data_rate.group(1))
                data_sended += data_rate_int
                line_length = 50
                green_length = int((data_sended / data_size) * line_length)  # How many are green
                red_length = line_length - green_length  # The rest are red

                # Create the visual representation: green part and red part
                green_part = '\033[32m' + u'\u2500' * green_length  # Green part
                red_part = '\033[31m' + u'\u2500' * red_length  # Red part

                # Build the output string, including the counter value
                line = f'{green_part}{red_part} \033[35m{data_sended}/{data_size}\033[0m' # Reset color after printing

                # Print the line and overwrite it in place
                sys.stdout.write('\r' + line)
                sys.stdout.flush()
                #sys.stdout.write('\n')
                #sys.stdout.flush()
                #print('ņ')
    
'''
# Your input string
input_string = "[16:27:26] STATUS: [i0]   |###########x....____|__________| 6.161 GB/s (4.106 kHz) FLES E001"

# Regular expression to match the data rate (e.g., 6.161 GB/s)
pattern = r'(\d+\.\d+)\sGB/s'

# Search for the pattern in the input string
match = re.search(pattern, input_string)

# Check if a match is found and print the result
if match:
    data_rate = match.group(1)  # Extract the numerical part of the data rate
    print(f"Data rate: {data_rate} GB/s")
else:
    print("Data rate not found.")
'''
