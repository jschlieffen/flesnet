#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 26 16:53:41 2025

@author: jschlieffen
"""

import re
import time
import curses
import select
import subprocess
import plotext as plt
import io
from contextlib import redirect_stdout
import signal
#import sys
#sys.path.append('../')
#from log_msg import *


# =============================================================================
# This file deals with the monotoring by using a mixture of curses for the 
# terminal control and plotext for the terminal printing.
# NOTE: Due to technical reasons related to ncurses, this file consists
# of its own signal handler
# =============================================================================

# Used for the signal handler
terminate_program = False

# =============================================================================
# Gets the data rate from a line in the logfile
# =============================================================================
def get_data_rate_V2(log_line):
    match = re.search(r'(\d+\.\d+)\sGB/s', log_line)
    if match:
        return float(match.group(1))
    match = re.search(r'(\d+\.\d+)\sMB/s', log_line)
    if match:
        return float(match.group(1))/1000
    return 0.0 # This line returns 0

def get_data_rate(parts, col_index):
    try:
        return float(parts[col_index])/1000000
    except (IndexError, ValueError):
        return 0.0 #This line returns 0

def calculate_progress(current_data, total_data):
    return current_data / total_data

def calc_outout_str(input_string):
    patterns = [
        (
            r"logs/collectl/(build|entry)_nodes/(build|entry)_node_(.+?)\.csv",
            lambda m: f"{m.group(1)} node: {m.group(3)}"
        ),
        (
            r"logs/collectl/tsclient/sender_node_(.+?)\.csv",
            lambda m: f"sender node: {m.group(1)}"
        ),
        (
            r"logs/collectl/tsclient/receiving_node_(.+?)\.csv",
            lambda m: f"receiving node: {m.group(1)}"
        ),
        (
            r"logs/collectl/timeslice_forwarding/input_nodes/input_node_(.+?)\.csv",
            lambda m: f"input node: {m.group(1)}"
        ),
        (
            r"logs/collectl/timeslice_forwarding/output_nodes/output_node_(.+?)\.csv",
            lambda m: f"output node: {m.group(1)}"
        ),
    ]

    for pattern, formatter in patterns:
        match = re.search(pattern, input_string)
        if match:
            return formatter(match)

    # Log unmatched string
    with open("debug.log", "a") as debug_log:
        debug_log.write(
            f"calc_outout_str: input={input_string}, no match, returning input\n"
        )


# =============================================================================
# draws the progress bars of the entry and build nodes, by using the curses 
# colours 
# =============================================================================
def draw_progress_bar(stdscr, data_dict, num_entry_nodes, num_build_nodes, num_receiver_nodes, num_input_nodes, num_output_nodes, 
                    use_flesnet, use_GSI_TS_forwarding, use_ZIB_TS_forwarding, scroll_offset, height):
    """
    Draws scrollable progress bars with original colors.
    """
    max_y, max_x = stdscr.getmaxyx()
    all_lines = []

    # Build all lines as tuples (text, color)
    all_lines.append([("Number of nodes:", 0)])
    if use_flesnet:
        all_lines.append([("  entry nodes: " + str(num_entry_nodes), 4)])
        all_lines.append([("  build nodes: " + str(num_build_nodes), 5)])
    if use_GSI_TS_forwarding:
        if not use_flesnet:
            all_lines.append([("  sender nodes:   " + str(num_receiver_nodes), 4)])
            all_lines.append([("  reciever nodes: " + str(num_receiver_nodes), 5)])
        else:
            all_lines.append([("  receiver nodes: " + str(num_receiver_nodes), 6)])
    if use_ZIB_TS_forwarding:
        if not use_flesnet:
            all_lines.append([("  input nodes:  " + str(num_input_nodes), 4)])
            all_lines.append([("  output nodes: " + str(num_output_nodes), 5)])
        else:
            all_lines.append([("  output nodes: " + str(num_output_nodes), 6)])


    # Progress bars
    bar_width = 50
    for key, val in data_dict.items():
        output_str = calc_outout_str(key)
        if 'build node' in output_str and (use_GSI_TS_forwarding or use_ZIB_TS_forwarding):
            progress = val['current_data_input'] / max(1e-6, val['total_data'])
            progress_num = f" {val['current_data_input']:.2f}/{val['total_data']:.2f}"
        else:
            progress = val['current_data'] / max(1e-6, val['total_data'])
            progress_num = f" {val['current_data']:.2f}/{val['total_data']:.2f}"
        progress = max(0.0, min(progress, 1.0))


        green_len = int(progress * bar_width)
        red_len = bar_width - green_len
        green = u'\u2500' * green_len
        red = u'\u2500' * red_len

        # Decide color for node label
        if 'entry node' in output_str or 'input node' in output_str or 'sender node' in output_str:
            node_color = 4
        elif 'build node' in output_str:
            node_color = 5
        elif 'output node' in output_str or 'receiving node' in output_str:
            node_color = 6
        else:
            node_color = 0
        
        line = [
            (f"{output_str}: ", node_color),
            (green, 2),
            (red, 1),
            (progress_num, 3)
        ]
        all_lines.append(line)

    # Clamp scroll
    content_height = len(all_lines)
    scroll_offset = max(0, min(scroll_offset, max(0, content_height - height)))

    # Draw visible portion
    visible_lines = all_lines[scroll_offset:scroll_offset + height]
    for i, line in enumerate(visible_lines):
        x = 0
        for text, color in line:
            try:
                stdscr.addstr(i, x, text[:max_x - x], curses.color_pair(color))
            except curses.error:
                pass
            x += len(text)

    return content_height



# =============================================================================
# Translate the plotext output, which is written in ANSI to something ncurses 
# understands (ACS, colour pairs, etc.)
# =============================================================================
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

# =============================================================================
# initialization of all ncurses colours. Maximum is 256
# =============================================================================


def init_color_pairs():
    curses.use_default_colors()
    for i in range(0, curses.COLORS):
        curses.init_pair(i, i, -1)

# =============================================================================
# This function draws the graph in the terminal. For this it uses plotext.
# Since plotext and ncurses does not work well together, the output 
# of plotext is redirected into a buffer. The output is then
# line by line translated and given to ncurses for the displaying
# =============================================================================
def draw_Graph(stdscr, data_dict, use_flesnet,use_GSI_TS_forwarding, use_ZIB_TS_forwarding, scroll_offset, start_y, height):
    """
    Draws the graphs in two columns: entry nodes (left) and build nodes (right)
    with unified scrolling.
    """
    max_y, max_x = stdscr.getmaxyx()
    
    columns = []
    padding = 2  # space between columns
    if (use_flesnet and use_GSI_TS_forwarding) or (use_flesnet and use_ZIB_TS_forwarding):
        num_cols = 3
    else:
        num_cols = 2
    col_width = (max_x - padding * (num_cols - 1)) // num_cols
    def generate_graph_lines(node_list):
        all_lines = []
        for key,val in node_list:
            plt.clf()
            lbl = calc_outout_str(key)
            if 'build node' in lbl and (use_GSI_TS_forwarding or use_ZIB_TS_forwarding):
                data_input = val['data_array_input'][:]
                data_output = val['data_array_output'][:]
                if len(data_input) > 20:
                    data_input = data_input[-20:]
                if len(data_output) > 20:
                    data_output = data_output[-20:]
                lbl_input = 'in'
                lbl_output ='out'
                plt.plot(data_input, label=lbl_input)
                plt.plot(data_output, label=lbl_output)
            else:
                data = val['data_array'][:]
                if len(data) > 20:
                    data = data[-20:]
                plt.plot(data)
            plt.theme("dark")
            plt.title(lbl)
            plt.plot_size(min(60, col_width), min(10, height))
            
            buf = io.StringIO()
            with redirect_stdout(buf):
                plt.show()
            lines = buf.getvalue().splitlines()
            all_lines.append(lines)
        return all_lines
    # Separate nodes
    columns = []
    if use_flesnet:
    
        entry_nodes = [(key,val) for key, val in data_dict.items() if 'entry node' in calc_outout_str(key)]
        build_nodes = [(key,val) for key, val in data_dict.items() if 'build node' in calc_outout_str(key)]
        entry_lines = generate_graph_lines(entry_nodes)
        build_lines = generate_graph_lines(build_nodes)
        columns.append(("Entry Nodes", entry_lines))
        columns.append(("Build Nodes", build_lines))
    if use_GSI_TS_forwarding:
        if not use_flesnet:
            sender_nodes = [(key,val) for key, val in data_dict.items() if 'sender node' in calc_outout_str(key)]
            sender_lines = generate_graph_lines(sender_nodes)
            columns.append(("Sender Nodes", sender_lines))
        receiver_nodes = [(key,val) for key, val in data_dict.items() if 'receiving node' in calc_outout_str(key)]
        receiver_lines = generate_graph_lines(receiver_nodes)
        columns.append(("Receiver Nodes", receiver_lines))

    if use_ZIB_TS_forwarding:
        if not use_flesnet:
            input_nodes = [(key,val) for key, val in data_dict.items() if 'input node' in calc_outout_str(key)]
            input_lines = generate_graph_lines(input_nodes)
            columns.append(("Input Nodes", input_lines))
        output_nodes = [(key,val) for key, val in data_dict.items() if 'output node' in calc_outout_str(key)]
        output_lines = generate_graph_lines(output_nodes)
        columns.append(("Output Nodes", output_lines))




    # Determine max lines for each row
    #max_rows = max(len(entry_lines), len(build_lines))
    max_rows = max(len(lines) for _, lines in columns)
    all_lines_combined = []
    
    
    label_line = (" " * padding).join(
        label.center(col_width)
        for label, _ in columns
    )
    # Add overall bottom title
    all_lines_combined.append(' ' * ((max_x - len("Data rate in GB/s")) // 2) + "Data rate in GB/s")
    all_lines_combined.append("")  # extra blank line below
    all_lines_combined.append("")
    all_lines_combined.append(label_line)
    all_lines_combined.append("")
    for row_idx in range(max_rows):
    
        # Find tallest graph block in this row
        row_height = 0
        row_columns = []
    
        for _, lines in columns:
            graph = lines[row_idx] if row_idx < len(lines) else []
            row_columns.append(graph)
            row_height = max(row_height, len(graph))
    
        # Pad all graphs to same height
        padded_columns = []
        for graph in row_columns:
            padded_columns.append(
                graph + [''] * (row_height - len(graph))
            )
    
        # Emit line-by-line
        for line_idx in range(row_height):
            combined = (" " * padding).join(
                graph[line_idx].ljust(col_width)
                for graph in padded_columns
            )
            all_lines_combined.append(combined)
            

    # Clamp scroll
    content_height = len(all_lines_combined)
    scroll_offset = max(0, min(scroll_offset, max(0, content_height - height)))

    # Draw visible portion
    visible_lines = all_lines_combined[scroll_offset:scroll_offset + height]
    for i, line in enumerate(visible_lines):
        result_arr = strip_and_translate_ansi_escape_sequences(line)
        x = 0
        color_pair = 0
        for tup in result_arr:
            if tup[0] == 'color':
                color_pair = tup[1]
            elif tup[0] == 'text':
                try:
                    stdscr.addstr(start_y + i, x, tup[1], curses.color_pair(int(color_pair)))
                except curses.error:
                    pass
                x += len(tup[1])

    return content_height

        
def tail_csv_V2(file_path):
    with open(file_path, "r") as f:
        f.seek(0, 2)  # go to end of file
        while not terminate_program:
            line = f.readline()
            if not line:
                time.sleep(0.1)
                continue

            line = line.strip()

            if not line or line.startswith("#"):
                continue

            yield line.split(",")
            
def tail_csv(file_path):
    f = open(file_path, "r")
    f.seek(0, 2)

    def poll():
        line = f.readline()
        if not line:
            return None

        line = line.strip()
        if not line or line.startswith("#"):
            return None

        return line.split(",")

    return poll

# =============================================================================
# This function is the main funxtion in of this file. It adds 
# the current data rate to the data dict and the starts the functions
# draw_Graph and draw_progress_bar
# =============================================================================
def main(stdscr,file_names, num_entry_nodes, num_build_nodes, num_receiver_nodes, num_input_nodes, num_output_nodes, 
         use_flesnet, use_GSI_TS_forwarding, use_ZIB_TS_forwarding,enable_graph,enable_progress_bar):
    global terminate_program
    signal.signal(signal.SIGINT, lambda signum, frame: signal_handler(signum, frame))
    signal.signal(signal.SIGTERM, lambda signum, frame: signal_handler(signum, frame))
    stdscr.clear()
    stdscr.nodelay(True)  # non-blocking input
    curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)
    curses.mouseinterval(0)
    stdscr.keypad(True)
    scroll_offset = 0
    data_dict = {}
    init_color_pairs()
    COLUMN_MAP = {
        "[IB]InPkt": 2,
        "[IB]OutPkt": 3,
        "[IB]InKB": 4,
        "[IB]OutKB": 5,
        "[IB]Err": 6,
    }
    
    #USE_COLUMN = "[IB]InKB"   # change once depending on use case
    #COL_INDEX = COLUMN_MAP[USE_COLUMN]
    progress_scroll = 0
    graph_scroll = 0
    for file_name in file_names:
        node_type = calc_outout_str(file_name[0])
        if 'entry node' in node_type or 'input node' in node_type or 'sender node' in node_type:
            USE_COLUMN = "[IB]OutKB"   
            COL_INDEX = COLUMN_MAP[USE_COLUMN]
        elif 'output node' in node_type or 'receiving node' in node_type:
            USE_COLUMN = "[IB]InKB"   
            COL_INDEX = COLUMN_MAP[USE_COLUMN]
        if 'build node' in node_type:
            if use_GSI_TS_forwarding or use_ZIB_TS_forwarding:
                USE_COLUMN_1 = "[IB]InKB"
                USE_COLUMN_2 = "[IB]OutKB"
                COL_INDEX = (COLUMN_MAP[USE_COLUMN_1], COLUMN_MAP[USE_COLUMN_2])
                data_dict[file_name[0]] = {
                    'current_data_input' : 0.0,
                    'current_data_output' : 0.0,
                    #'tail' : tail_file(file_name[0]),
                    'tail' : tail_csv(file_name[0]),
                    'total_data' : file_name[1], 
                    'data_array_input' : [],
                    'data_array_output' : [],
                    'COL_INDEX' : COL_INDEX
                    }
            else:
                USE_COLUMN = "[IB]InKB"   
                COL_INDEX = COLUMN_MAP[USE_COLUMN]
                data_dict[file_name[0]] = {
                    'current_data' : 0.0,
                    #'tail' : tail_file(file_name[0]),
                    'tail' : tail_csv(file_name[0]),
                    'total_data' : file_name[1], 
                    'data_array' : [],
                    'COL_INDEX' : COL_INDEX
                    }
        else:
            data_dict[file_name[0]] = {
                'current_data' : 0.0,
                #'tail' : tail_file(file_name[0]),
                'tail' : tail_csv(file_name[0]),
                'total_data' : file_name[1], 
                'data_array' : [],
                'COL_INDEX' : COL_INDEX
                }
    last_update = time.time() -1
    max_y, max_x = stdscr.getmaxyx()
    try: 
        while not terminate_program:
            key = stdscr.getch()
            
            if key == curses.KEY_MOUSE:
                try:
                    _, mx, my, _, bstate = curses.getmouse()
            
                    if bstate & curses.BUTTON4_PRESSED:   # scroll up
                        if enable_progress_bar and my < max_y // 3:
                            progress_scroll -= 1
                        elif enable_graph:
                            graph_scroll -= 2
                    elif bstate & curses.BUTTON5_PRESSED: # scroll down
                        if enable_progress_bar and my < max_y // 3:
                            progress_scroll += 1
                        elif enable_graph:
                            graph_scroll += 2
            
                except curses.error:
                    pass
            if key == curses.KEY_DOWN:
                scroll_offset += 1
            elif key == curses.KEY_UP:
                scroll_offset = max(0, scroll_offset - 1)
            elif key == curses.KEY_NPAGE:  # Page Down
                scroll_offset += 10
            elif key == curses.KEY_PPAGE:  # Page Up
                scroll_offset -= 10
            if time.time() - last_update > 1:
                for key,val in data_dict.items():
                    try:
                        parts = val['tail']()
                        if parts is None:
                            if ('build_nodes' in key) and (use_GSI_TS_forwarding or use_ZIB_TS_forwarding):
                                data_rate_input = 0
                                data_rate_output = 0
                            else: 
                                data_rate = 0
                        else:
                            
                            if ('build_nodes' in key) and (use_GSI_TS_forwarding or use_ZIB_TS_forwarding):
                                data_rate_input = get_data_rate(parts, val['COL_INDEX'][0])
                                data_rate_output = get_data_rate(parts, val['COL_INDEX'][1])
                            else:
                                data_rate = get_data_rate(parts, val['COL_INDEX'])
                        if ('build_nodes' in key) and (use_GSI_TS_forwarding or use_ZIB_TS_forwarding):
                            data_dict[key]['current_data_input'] += data_rate_input
                            data_dict[key]['current_data_output'] += data_rate_output
                            data_dict[key]['data_array_input'].append(data_rate_input)
                            data_dict[key]['data_array_output'].append(data_rate_output)
                            
                        else:
                            data_dict[key]['current_data'] += data_rate
                            data_dict[key]['data_array'].append(data_rate)
                    except StopIteration:
                        data_rate = 0.0
                last_update = time.time()
           
            progress_height = max_y // 3 if enable_progress_bar else 0
            graph_height = max_y - progress_height if enable_graph else 0
            #progress_height = max_y // 3
            #graph_height = max_y - progress_height
            stdscr.erase()
            #if enable_progress_bar:
            #    draw_progress_bar(stdscr, data_dict, num_entry_nodes, num_build_nodes)
            #if enable_graph:
            #    draw_Graph(stdscr,data_dict, scroll_offset)
                #stdscr.addstr('test123')
                # Draw progress bar
            if enable_progress_bar:
                content_height = draw_progress_bar(
                    stdscr, data_dict, num_entry_nodes, num_build_nodes, num_receiver_nodes, num_input_nodes, num_output_nodes, 
                    use_flesnet, use_GSI_TS_forwarding, use_ZIB_TS_forwarding,
                    progress_scroll, progress_height
                )
                progress_scroll = max(0, min(progress_scroll, content_height - progress_height))
        
            # Draw graphs
            if enable_graph:
                content_height = draw_Graph(
                    stdscr, data_dict, use_flesnet, use_GSI_TS_forwarding, use_ZIB_TS_forwarding, graph_scroll, 
                    start_y=progress_height, height=graph_height
                )
                graph_scroll = max(0, min(graph_scroll, content_height - graph_height))

            #stdscr.addstr('test')
            stdscr.refresh()
            time.sleep(0.05)
    finally:
        cleanup(stdscr)
    total_data, avg_data_rate = calc_output_msg(data_dict)
    return total_data, avg_data_rate
    

# =============================================================================
# Calculate the total data sended and the average data rate by all entry nodes
# =============================================================================
def calc_output_msg(data_dict):
    total_data = 0
    avg_data_rate = 0
    it_counter = 1
    for key,val in data_dict.items():
        if 'entry_node' in key or 'sender_node' in key or 'input_node' in key:
            total_data += val['current_data']
            for data_rate in val['data_array']:
                if data_rate > 0:
                    avg_data_rate += data_rate
                    it_counter += 1
    avg_data_rate = avg_data_rate/it_counter
    return total_data, avg_data_rate
   
# =============================================================================
# Defines the signal handler for a clean end of the experiment. Currently only
# ctrl+c and sigterm are implemented. For safety reasons sigkill is not 
# implemented so it is recommended to only use it if the other two fails
# May be changed in the furture
# ============================================================================
def signal_handler(signum, frame):
    global terminate_program
    terminate_program = True
    with open("debug.log", "a") as f:
        f.write("SIGINT received\n")


def cleanup(stdscr):
    if stdscr is not None:
        try:
            curses.nocbreak()
            stdscr.keypad(False)
            curses.echo()
        except:
            pass
        #finally:
        #    curses.endwin()
            
