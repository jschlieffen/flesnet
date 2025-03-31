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


def ansi_to_curses_color(ansi_code):
    """Convert an ANSI color code to a curses color code."""
    # Mapping of basic ANSI color codes to curses color pairs
    '''
    basic_color_map = {
        30: curses.COLOR_BLACK,
        31: curses.COLOR_RED,
        32: curses.COLOR_GREEN,
        33: curses.COLOR_YELLOW,
        34: curses.COLOR_BLUE,
        35: curses.COLOR_MAGENTA,
        36: curses.COLOR_CYAN,
        37: curses.COLOR_WHITE
    }
    '''
    #return ansi_code
    basic_color_map = {
        0: curses.COLOR_BLACK,
        1: curses.COLOR_RED,
        2: curses.COLOR_GREEN,
        3: curses.COLOR_YELLOW,
        4: curses.COLOR_BLUE,
        5: curses.COLOR_MAGENTA,
        6: curses.COLOR_CYAN,
        7: curses.COLOR_WHITE
    }
    
    bright_color_map = {
        8: curses.COLOR_BLACK,
        9: curses.COLOR_RED,
        10: curses.COLOR_GREEN,
        11: curses.COLOR_YELLOW,
        12: curses.COLOR_BLUE,
        13: curses.COLOR_MAGENTA,
        14: curses.COLOR_CYAN,
        15: curses.COLOR_WHITE
    }
    # Ensure valid ANSI color code
    if not (0 <= ansi_code <= 255):
        raise ValueError(f"Invalid ANSI color code: {ansi_code}")

    #if ansi_code == 0:
       # return basic_color_map.get(ansi_code, curses.COLOR_CYAN)
    
    if 0 <= ansi_code <= 7:
        return basic_color_map[ansi_code]
    
    if 8 <= ansi_code <= 15:
        # Map bright colors to the same color with a brighter effect if your terminal supports it.
        # Curses doesn't differentiate basic from bright, so we may just use the same mapping here.
        return bright_color_map[ansi_code]  
        
    # Handle 256-color palette (optional enhancement, mapping directly to curses)
    if ansi_code >= 16 and ansi_code < 256:
        return ansi_code  # For simplicity, return the same number in the 256-color range.
    
    # If it's a basic color, map to curses basic colors
    return basic_color_map.get(ansi_code, curses.COLOR_WHITE)  # Default to white if no match

def strip_and_translate_ansi_escape_sequences_v2(text):
    # This regex will match ANSI escape sequences like ^[38;5;10m or ^[31m
    ansi_escape = re.compile(r'\x1b\[[0-9;]*[m]')
    color_codes = []
    # Function to replace ANSI codes with curses equivalent color codes
    def replace_with_curses(match):
        # Extract the ANSI escape sequence (like 31m, 32m, or 38;5;10m)
        code_str = match.group(0)

        # Case 1: Basic ANSI color (like 31m, 32m)
        if ';' not in code_str:  # Simple 30-37 color codes
            try:
                # Extract the color code directly before the 'm'
                color_code = int(code_str[2][:-1])  # Correctly slice to get the color number
                curses_color = ansi_to_curses_color(color_code)
                color_codes.append(curses_color)
                return ''  # Return the curses color code
            except ValueError:
                return ''  # In case the code is malformed, just return an empty string

        # Case 2: 256 color (like 38;5;10m)
        elif '38;5;' in code_str:
            try:
                # Extract the 256 color code after '38;5;'
                color_code = int(code_str.split(';')[2][:-1])  # Strip the trailing 'm'
                curses_color = ansi_to_curses_color(color_code)
                color_codes.append(curses_color)
                return '' # Return the curses color code
            except ValueError:
                return ''  # In case the code is malformed, just return an empty string
        
        # In case no color code matches, return the string unmodified
        return ''
    
    processed_txt = ansi_escape.sub(replace_with_curses, text)
    # Replace all ANSI escape sequences with curses color codes
    return processed_txt, color_codes



def strip_and_translate_ansi_escape_sequences(text):
    # This regex will match ANSI escape sequences like ^[38;5;10m or ^[31m
    ansi_escape = re.compile(r'\x1b\[[0-9;]*[m]')
    color_codes = []
    result_text = []
    last_pos = 0
    # Function to replace ANSI codes with curses equivalent color codes
    def replace_with_curses(match):
        code_str = match.group(0)
        color_code = None
        nonlocal last_pos
        # Case 1: Basic ANSI color (like 31m, 32m)
        if ';' not in code_str:  # Simple 30-37 color codes
            try:
                color_code = int(code_str[2][:-1])  # Extract color code
                #curses_color = ansi_to_curses_color(color_code)
                curses_color = color_code
                color_codes.append(curses_color)
                #result_text.append(('color', curses_color))
                #return ''  # Return empty, as we only want the color code
            except ValueError:
                return ''  # Return empty if the code is malformed

        # Case 2: 256 color (like 38;5;10m)
        elif '38;5;' in code_str:
            try:
                color_code = int(code_str.split(';')[2][:-1])  # Extract 256 color code
                #curses_color = ansi_to_curses_color(color_code)
                curses_color = color_code
                color_codes.append(curses_color)
                #result_text.append(('color', curses_color))
                #return ''
            except ValueError:
                return '' # Return empty if the code is malformed
            
        if color_code is not None:
            # Append the text between the last color code and the current one
            text_segment = text[last_pos:match.start()]
            clean_segment = ansi_escape.sub('', text_segment)
            if text_segment:
                result_text.append(('text', clean_segment))  # Add text before the color
            result_text.append(('color', color_code))  # Add the color
            last_pos = match.end()  # Update the position of the last color code
            return '' 

        # In case no color code matches, just return empty
        return ''
    
    #def get_interval(text):
        

    # Process the text and strip out ANSI escape sequences
    processed_txt = ansi_escape.sub(replace_with_curses, text)

    if last_pos < len(text):
        text_segment = text[last_pos:]
        clean_segment = ansi_escape.sub('', text_segment)  # Remove any remaining escape sequences
        if clean_segment:
            result_text.append(('text', clean_segment))
    # Now, to retain the original text while applying the colors
    #result_text.append(('text', processed_txt))  # Append the remaining text (without escape codes)

    return result_text

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

def init_color_pairs_v2():
    curses.use_default_colors()
    for i in range(0, curses.COLORS):
        curses.init_pair(i, i, -1)

def main(stdscr):
    #stdscr.clear()
    curses.start_color()
    # Initialize basic colors (0-15)
    #for i in range(8):  # Init basic colors (0-7)
        #curses.init_pair(i + 1, i, curses.COLOR_BLACK)
        
    #for i in range(16, 256):  # Initialize colors from 16 to 255
        #curses.init_color(i, i * 10 // 255, i * 10 // 255, i * 10 // 255)  # You can customize RGB here
        #curses.init_pair(i - 15, i, curses.COLOR_BLACK)
    init_color_pairs_v2()
    #init_color_pairs()
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
        plt.plot(data)
        plt.plot(data_2)
        plt.plot(data_3)
        plt.theme("dark")
        plt.title("random num")
        plt.plot_size(80,20)
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
                #plot_line = strip_and_translate_ansi_escape_sequences(line)
                #stdscr.addstr(i+10, 0,line)  # Cut lines if too wide
                processed_text, color_codes = strip_and_translate_ansi_escape_sequences(line)
                
                # Display the processed text with colors in curses
                y, x = 0, 0
                for char in processed_text:
                    # Apply the corresponding color to each character
                    if char != ".":
                        if color_codes:
                            color_pair = color_codes[0]
                            stdscr.addstr(i+10, x, char, curses.color_pair(int(color_pair))) 
                            #stdscr.addstr(i+10,x,char)
                            # Apply the color pair
                            color_codes.pop(0)
                            #stdscr.addstr(i+10,x,str(color_pair))
                        else:
                            stdscr.addstr(i+10, x, char)
                    else:
                        stdscr.addstr(i+10, x, char)# No color applied
                    x += 1
                    if char == '\n':
                        y += 1
                        x = 0
                        line_idx = 0  # Line index for accessing color sequences
                        
        '''
        for i, line in enumerate(lines):
            if i < max_y - 1:  # Make sure we don't go out of bounds
                #if color_idx < l    
                #line = line.replace("[","")
                #plot_line = strip_and_translate_ansi_escape_sequences(line)
                #stdscr.addstr(i+10, 0,line)  # Cut lines if too wide
                result_arr = strip_and_translate_ansi_escape_sequences(line)
                
                color_pair = 0
                char = ''
                # Display the processed text with colors in curses
                y, x = 0, 0
                #stdscr.addstr(str(len(result_arr)))
                was_prev_color = False
                count = 0
                for j,tup in enumerate(result_arr):
                    if tup[0] == 'color':
                        color_pair = tup[1]
                        #stdscr.addstr(i+10,90, str(j))
                        #if was_prev_color:
                            #stdscr.addstr(i+10, 100,str(color_pair))
                        was_prev_color = True
                    # Apply the corresponding color to each character
                    elif tup[0] == 'text':
                        char = tup[1]
                        #stdscr.addstr(i+10,90,str(color_pair))
                        stdscr.addstr(i+10,x,char, curses.color_pair(int(color_pair)))
                        #stdscr.addstr(str(len(char)))
                        was_prev_color = False
                        #stdscr.addstr(i+10,110, str(count))
                        count += 1
                        
                        x += len(char)
                x = 0

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
                #stdscr.addstr(line[tup[0]:tup[1]])
                stdscr.addstr(str(tup[2]))
                #stdscr.addstr(str(len(line[tup[0]:tup[1]])))
                #stdscr.addstr(str(len(colour_tups)))
                #stdscr.addstr(str(len(plot_char)))
                #stdscr.addstr(i+10,0,line,curses.color_pair(tup[2]))
            #stdscr.addstr((str(prev_pos)))
        '''
        '''
        #Take colour segment from line/convert colour segment and then find indices
        for i, line in enumerate(lines):
            if i >= max_y - 1:  # Skip if we exceed the screen height
                break
        
            # Strip ANSI escape sequences to get the actual line text
            #plot_line = strip_ansi_escape_sequences(line)
        
            # Initialize position tracking
            prev_pos = 0
            color_segment = extract_colors_with_curses(line)
            #color_segment = extract_colors_with_curses(line)
            # Process each color segment in the line
            for tup in color_segment:
                # Print the previous segment (if any) with the previous color
                start_index, end_index, color_code = int(tup[0]), int(tup[1]), int(tup[2])
                #if prev_pos == 0:
                    #stdscr.addstr(i + 10, start_index, line[start_index:end_index]) 
                plot_line = strip_ansi_escape_sequences(line[start_index: end_index])
                if prev_pos < start_index:
                    stdscr.addstr(i + 10, prev_pos, plot_line)
                
                # Print the current segment with the new color
                stdscr.attron(curses.color_pair(color_code))
                #stdscr.addstr(i + 10, start_index, plot_line[start_index:end_index])
                stdscr.addstr(i + 10, prev_pos, plot_line)  # Keep using 'line' for color handling
                stdscr.attroff(curses.color_pair(color_code))
                #stdscr.addstr(str(len(line[start_index: end_index])))
                #stdscr.addstr(line[start_index: end_index])
                stdscr.addstr(str((start_index)))
                #stdscr.addstr(str(end_index))
                # Update the previous position
                prev_pos = len(plot_line)
        
            # If there's any remaining text after the last color segment, print it
            #if prev_pos < len(line):
                #stdscr.addstr(i + 10, prev_pos, plot_line[prev_pos:])
        
        #stdscr.refresh()
        '''
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
        '''
        for i, line in enumerate(lines):
            if i >= max_y - 1:  # Skip if we exceed the screen height
                break

            # Strip ANSI escape sequences to get the actual line text
            plot_line = strip_ansi_escape_sequences(line)
            
            current_pos_coded = 0
            current_pos = 0
            color_idx = 0  # Default color

            while current_pos < len(line):
                # If the current position exceeds the screen width, truncate the text
                part_to_print_coded = line[current_pos_coded:current_pos_coded + max_x]
                part_to_print = strip_ansi_escape_sequences(part_to_print_coded)
                # If part_to_print is longer than max_x, truncate it
                if len(part_to_print) > max_x:
                    part_to_print = part_to_print[:max_x]

                # Find the next color escape code
                for color_code in color_sequences:
                    start_pos = line.find(color_code, current_pos)
                    end_pos = start_pos + len(color_code)

                    if start_pos == current_pos:
                        # Apply the color for this segment
                        color_idx = get_curses_color_from_code(color_code)
                        stdscr.attron(curses.color_pair(color_idx))
                        part_to_print = plot_line[start_pos:end_pos]
                        stdscr.addstr(i + 10, current_pos, part_to_print)
                        stdscr.attroff(curses.color_pair(color_idx))
                        current_pos = end_pos
                        break

                # If we still have remaining text, print it as part of the plot line
                if current_pos < len(line):
                    #print(current_pos)
                    stdscr.addstr(i + 10, current_pos, part_to_print)
                    current_pos += len(part_to_print)
        '''
        stdscr.refresh()
        
        time.sleep(1)
        

#main()
curses.wrapper(main)