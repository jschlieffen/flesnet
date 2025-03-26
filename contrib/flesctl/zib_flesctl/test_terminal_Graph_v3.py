#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 26 15:34:31 2025

@author: jschlieffen
"""

#import plotext as plt
#import matplotlib.pyplot as plt
import plotext as plt
import random
import curses
import time
import io
import os
from contextlib import redirect_stdout

#os.environ["NCURSES_NO_UTF8_ACS"] = "1"
# Function to generate random data
def generate_data():
    return [random.uniform(0, 7) for _ in range(20)]

def main():
    #stdscr.clear()
    while True:
        data = generate_data()
        data_2 = generate_data()
        data_3 = generate_data()
        plt.clf()
        plt.plot(data,)
        plt.plot(data_2)
        plt.plot(data_3)
        plt.theme("dark")
        plt.title("random num")
        #plt.plot_size(10,10)
        plt.show()
        plt.clear_color()
        
        '''
        time.sleep(1)
        buf = io.StringIO()

        # Use contextlib.redirect_stdout to capture plt.show() output
        with redirect_stdout(buf):
            #plt.figtext()  # This will print the plot to the StringIO buffer
            plt.show()
        # Get the plot as a string from the buffer
        plot_output = buf.getvalue()

        # Display the plot inside the curses window
        #stdscr.addstr(0, 0, plot_output)  # Add the plot output to the curses window
        max_y, max_x = stdscr.getmaxyx()  # Get the terminal dimensions
        lines = plot_output.splitlines()
    
        for i, line in enumerate(lines):
            if i < max_y - 1:  # Make sure we don't go out of bounds
                line = line.replace("[","")
                stdscr.addstr(i+10, 0, line)  # Cut lines if too wide
                 
        stdscr.refresh()
        '''
        time.sleep(1)
        

main()
#curses.wrapper(main)