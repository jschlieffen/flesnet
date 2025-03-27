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
import re
from contextlib import redirect_stdout

#os.environ["NCURSES_NO_UTF8_ACS"] = "1"
# Function to generate random data
def generate_data():
    return [random.uniform(0, 7) for _ in range(20)]

def strip_ansi_escape_sequences(text):
    # This regex will match ANSI escape sequences like ^[38;5;10m
    ansi_escape = re.compile(r'(?:\x1b\[[0-9;]*[mGKHfaboA-DX]?)')
    return ansi_escape.sub('', text)

def extract_colors(text):
    # This regex will match color escape sequences in plotext
    color_escape = re.compile(r'(\x1b\[[0-9;]*m)')
    return color_escape.findall(text)

def extract_colors_with_curses(text):
    # This regex will match color escape sequences in plotext, including the reset code
    color_escape = re.compile(r'(\x1b\[[0-9;]*m)')
    
    # Find all matches for color escape sequences
    color_codes = color_escape.findall(text)
    
    result = []
    position = 0  # Track the current position in the text
    active_color_code = None  # Track the active color code
    
    # Process the text and its escape sequences
    for color_code in color_codes:
        start_index = text.find(color_code, position)
        position = start_index + len(color_code)  # Update position after the match
        
        # If it's a reset code, use the default color
        if color_code == '\x1b[0m':
            curses_code = 0
        else:
            curses_code = get_curses_color_from_code(color_code)
        
        # If the color sequence is a reset code, assign the next start/end to reset
        if color_code != '\x1b[0m':
            end_index = start_index + len(color_code)
            result.append((start_index, end_index, curses_code))
        else:
            result.append((start_index, position, curses_code))  # Append reset
        
    return result


# Function to map plotext colors to curses color pairs
def get_curses_color_from_code(color_code):
    """Maps plotext color codes to curses color pairs."""
    # Extract the color number from the code (e.g., 38;5;10 -> 10)
    match = re.match(r'\x1b\[38;5;(\d+)m', color_code)
    if match:
        color_number = int(match.group(1))
        return color_number + 1  # Curses color pair indices start from 1
    return 0  # Default color (black)

# Function to initialize all color pairs for 256-color mode
def init_color_pairs():
    # Initialize colors in curses for 256 colors
    for i in range(256):
        curses.init_pair(i + 1, i, curses.COLOR_BLACK)

def main(stdscr):
    #stdscr.clear()
    curses.start_color()
    init_color_pairs()
    #curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
    #curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
    #curses.init_pair(3, curses.COLOR_BLUE, curses.COLOR_BLACK)
    #curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    #curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
    #curses.init_pair(6, curses.COLOR_CYAN, curses.COLOR_BLACK)
    #curses.init_pair(7, curses.COLOR_WHITE, curses.COLOR_BLACK)
    while True:
        data = generate_data()
        data_2 = generate_data()
        data_3 = generate_data()
        plt.clf()
        plt.plot(data,)
        #plt.plot(data_2)
        #plt.plot(data_3)
        plt.theme("dark")
        plt.title("random num")
        plt.plot_size(50,20)
        #plt.show()
        #plt.clear_color()
        
        
        time.sleep(1)
        buf = io.StringIO()

        # Use contextlib.redirect_stdout to capture plt.show() output
        with redirect_stdout(buf):
            #plt.figtext()  # This will print the plot to the StringIO buffer
            plt.show()
        # Get the plot as a string from the buffer
        plot_str = buf.getvalue()
        #print(plot_output)
        color_sequences = extract_colors(plot_str)
        
        #plot_output = strip_ansi_escape_sequences(plot_str)
        #color_sequence = extract_colors(plot_output)
        # Display the plot inside the curses window
        #stdscr.addstr(0, 0, plot_output)  # Add the plot output to the curses window
        max_y, max_x = stdscr.getmaxyx()  # Get the terminal dimensions
        lines = plot_str.splitlines()
        color_idx =0
        '''
        for i, line in enumerate(lines):
            if i < max_y - 1:  # Make sure we don't go out of bounds
                #if color_idx < l    
                #line = line.replace("[","")
                #plot_line = strip_ansi_escape_sequences(line)
                stdscr.addstr(i+10, 0, line)  # Cut lines if too wide

        line_idx = 0  # Line index for accessing color sequences
        '''
        '''
        for i, line in enumerate(lines):
            start_idx = 0  # Keep track of where we are in the line
            #color_idx = 0
            while start_idx < len(line):
                # Check if we have a color sequence to apply
                if color_idx < len(color_sequences):
                    color_code = color_sequences[color_idx]
                    color_pair = get_curses_color_from_code(color_code)
                    if color_pair != 0:
                        stdscr.attron(curses.color_pair(color_pair))  # Apply the color
                    # Apply the color sequence to the next part of the line
                    end_idx = line.find('\x1b', start_idx)  # Find next color code or end of line
                    if end_idx == -1:
                        end_idx = len(line)
                    stdscr.addstr(i, start_idx, line[start_idx:end_idx])  # Print the colored part
                    start_idx = end_idx
                    if color_pair != 0:
                        stdscr.attroff(curses.color_pair(color_pair))  # Reset color
                    color_idx += 1
                else:
                    # No more color sequences, print the remaining text
                    stdscr.addstr(i, start_idx, line[start_idx:])
                    break
        '''
        
        for i, line in enumerate(lines):
            colour_tups = extract_colors_with_curses(line)
            #start_index = 0
            prev_pos = 0
            for tup in colour_tups:
                start_index = tup[0]
                end_index = tup[1]
                
            #for j,char in enumerate(line):
                #stdscr()
                plot_char = strip_ansi_escape_sequences(str(line[start_index:end_index]))
                #colour = get_curses_color_from_code(char)
                #stdscr.addstr(str(colour))
                #stdscr.addstr(i+10,0,line[tup[0]:tup[1]])
                #stdscr.addstr(i+10,j,plot_char, curses.color_pair(colour))                
                stdscr.addstr(i+10,prev_pos,plot_char,curses.color_pair(tup[2]))
                #stdscr.addstr(str(tup[2]))
                #stdscr.addstr(str(prev_pos))
                prev_pos = len(plot_char)
                stdscr.addstr(line[tup[0]:tup[1]])
                #stdscr.addstr(str(tup[2]))
                #stdscr.addstr(str(len(line[tup[0]:tup[1]])))
                #stdscr.addstr(str(len(colour_tups)))
                #stdscr.addstr(str(len(plot_char)))
                #stdscr.addstr(i+10,0,line,curses.color_pair(tup[2]))
            #stdscr.addstr((str(prev_pos)))
        '''
        line_idx=0
        start_idx=0
        while start_idx < len(plot_output):
            # Find the next color sequence, if it exists
            color_start = plot_output.find('\x1b', start_idx)
            #stdscr.addstr(str(color_start))
            if color_start == -1:
                # No more color sequences, just print the rest of the text
                stdscr.addstr(line_idx, 0, plot_output[start_idx:])
                break
            else:
                # Print text before the color sequence
                text = plot_output[start_idx:color_start]
                stdscr.addstr(line_idx, 0, text)
                
                # Now handle the color sequence
                color_end = plot_output.find('m', color_start) + 1  # End of the color sequence
                color_code = plot_output[color_start:color_end]
                color_pair = get_curses_color_from_code(color_code)
                if color_pair != 0:
                    stdscr.attron(curses.color_pair(color_pair))  # Apply color
                
                # Print the rest of the line with this color
                start_idx = color_end
                text_after_color = plot_output[start_idx:]
                next_color_start = text_after_color.find('\x1b')
        
                if next_color_start == -1:
                    stdscr.addstr(line_idx, 0, text_after_color)
                    break
                else:
                    # Print the part of the text until the next color change
                    next_color_end = text_after_color.find('m', next_color_start) + 1
                    stdscr.addstr(line_idx, 0, text_after_color[:next_color_start])
                    start_idx += next_color_end  # Continue from after the next color code
        
                if color_pair != 0:
                    stdscr.attroff(curses.color_pair(color_pair))  # Reset color
        
            line_idx += 1
            if line_idx >= max_y:
                break
        '''
        
        stdscr.refresh()
        
        time.sleep(1)
        

#main()
curses.wrapper(main)