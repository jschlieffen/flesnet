#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 15 15:38:16 2025

@author: jschlieffen
"""

import time 

def read_input_file():
    with open('logs/flesnet_input_file.log','r') as file:
        print(file.read())
        file.seek(0,2)
        while(True):
            line = file.readline()
            if line:
                print(line.strip())
            else:
                time.sleep(0.5)

def read_output_file():
    with open('logs/flesnet_output_file.log','r') as file:
        file.seek(0,2)
        while (True):
            line = file.readline()
            if line:
                print(line.strip())
            else:
                time.sleep(0.5)

read_input_file()
#read_output_file