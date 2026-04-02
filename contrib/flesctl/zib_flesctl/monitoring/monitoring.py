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

# =============================================================================
# Gives the prefix of the progress bars
# =============================================================================
def calc_outout_str(input_string):
    pattern = r"logs/collectl/(build|entry)_nodes/(build|entry)_node_(.+?)\.csv"
    match = re.search(pattern, input_string)
    if match:
        node_type = match.group(1) 
        node_id = match.group(3)
        formatted_output = f"{node_type} node: {node_id}"
        return formatted_output

    # Log unmatched string
    with open("debug.log", "a") as debug_log:
        debug_log.write(f"calc_outout_str: input={input_string}, no match, returning input\n")
    #return input_string


# =============================================================================
# draws the progress bars of the entry and build nodes, by using the curses 
# colours 
# =============================================================================
def draw_progress_bar_V2(stdscr, data_dict, num_entry_nodes, num_build_nodes):
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
        
# ==========================
# Draw progress bar (top 1/3)
# ==========================
def draw_progress_bar_V3(stdscr, data_dict, num_entry_nodes, num_build_nodes,
                      scroll_offset, height):
    max_y, max_x = stdscr.getmaxyx()
    all_lines = []

    # Header lines
    all_lines.append("Number of nodes:")
    all_lines.append(f"  entry nodes: {num_entry_nodes}")
    all_lines.append(f"  build nodes: {num_build_nodes}")

    # Progress bars
    bar_width = 50
    for key, val in data_dict.items():
        progress = val['current_data'] / max(1e-6, val['total_data'])
        output_str = calc_outout_str(key)

        green = u'\u2500' * int(progress * bar_width)
        red = u'\u2500' * (bar_width - len(green))
        line = f"{output_str}: {green}{red} {val['current_data']:.2f}/{val['total_data']:.2f}"
        all_lines.append(line)

    # Clamp scroll
    content_height = len(all_lines)
    scroll_offset = max(0, min(scroll_offset, max(0, content_height - height)))

    # Draw visible lines
    visible_lines = all_lines[scroll_offset:scroll_offset + height]
    for i, line in enumerate(visible_lines):
        try:
            stdscr.addstr(i, 0, line[:max_x])
        except curses.error:
            pass

    return content_height

def draw_progress_bar(stdscr, data_dict, num_entry_nodes, num_build_nodes,
                      scroll_offset, height):
    """
    Draws scrollable progress bars with original colors.
    """
    max_y, max_x = stdscr.getmaxyx()
    all_lines = []

    # Build all lines as tuples (text, color)
    all_lines.append([("Number of nodes:", 0)])
    all_lines.append([("  entry nodes: " + str(num_entry_nodes), 4)])
    all_lines.append([("  build nodes: " + str(num_build_nodes), 5)])

    # Progress bars
    bar_width = 50
    for key, val in data_dict.items():
        progress = val['current_data'] / max(1e-6, val['total_data'])
        output_str = calc_outout_str(key)

        green_len = int(progress * bar_width)
        red_len = bar_width - green_len
        green = u'\u2500' * green_len
        red = u'\u2500' * red_len

        # Decide color for node label
        if 'entry node' in output_str:
            node_color = 4
        elif 'build node' in output_str:
            node_color = 5
        else:
            node_color = 0

        line = [
            (f"{output_str}: ", node_color),
            (green, 2),
            (red, 1),
            (f" {val['current_data']:.2f}/{val['total_data']:.2f}", 3)
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
def init_color_pairs_v2():
    curses.use_default_colors()
    for i in range(0, curses.COLORS):
        curses.init_pair(i, i, -1)

# =============================================================================
# This function draws the graph in the terminal. For this it uses plotext.
# Since plotext and ncurses does not work well together, the output 
# of plotext is redirected into a buffer. The output is then
# line by line translated and given to ncurses for the displaying
# =============================================================================
def draw_Graph_V2(stdscr, data_dict):
    curses.start_color()

    plt.clf()
    for idx, (key,val) in enumerate(data_dict.items()):
        data = val['data_array'][: ]
        while True:
            if len(data) > 20:
                data.pop(0)
            else:
                break
        lbl = calc_outout_str(key)
        plt.plot(data, label=lbl)
        
    plt.theme("dark")
    plt.title("data rate")
    plt.plot_size(60,15)
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


def draw_Graph_V3(stdscr, data_dict, scroll_offset):
    curses.start_color()

    stdscr.erase()
    max_y, max_x = stdscr.getmaxyx()

    all_lines = []

    # 🔹 Build full "virtual screen"
    for key, val in data_dict.items():
        plt.clf()

        data = val['data_array'][:]
        while len(data) > 20:
            data.pop(0)

        lbl = calc_outout_str(key)
        plt.plot(data, label=lbl)

        plt.theme("dark")
        plt.title(f"{lbl}")
        plt.plot_size(60, 10)

        buf = io.StringIO()
        with redirect_stdout(buf):
            plt.show()

        lines = buf.getvalue().splitlines()
        all_lines.extend(lines)
        all_lines.append("")  # spacing between plots

    # 🔹 Clamp scrolling
    content_height = len(all_lines)
    scroll_offset = max(0, min(scroll_offset, content_height - max_y))

    # 🔹 Render visible window
    visible_lines = all_lines[scroll_offset:scroll_offset + max_y]

    for i, line in enumerate(visible_lines):
        result_arr = strip_and_translate_ansi_escape_sequences(line)
        x = 0
        color_pair = 0

        for tup in result_arr:
            if tup[0] == 'color':
                color_pair = tup[1]
            elif tup[0] == 'text':
                try:
                    stdscr.addstr(i, x, tup[1],
                                  curses.color_pair(int(color_pair)))
                except curses.error:
                    pass
                x += len(tup[1])

    return content_height


def draw_Graph(stdscr, data_dict, scroll_offset, start_y, height):
    """
    Draws the graphs in two columns: entry nodes (left) and build nodes (right)
    with unified scrolling.
    """
    max_y, max_x = stdscr.getmaxyx()
    padding = 2  # space between columns
    col_width = (max_x - padding) // 2

    # Separate nodes
    entry_nodes = [(key,val) for key, val in data_dict.items() if 'entry node' in calc_outout_str(key)]
    build_nodes = [(key,val) for key, val in data_dict.items() if 'build node' in calc_outout_str(key)]

    # Generate all graph lines per node
    def generate_graph_lines(node_list):
        all_lines = []
        for key,val in node_list:
            plt.clf()
            data = val['data_array'][:]
            if len(data) > 20:
                data = data[-20:]
            lbl = calc_outout_str(key)

            plt.plot(data, label=lbl)
            plt.theme("dark")
            plt.title(lbl)
            plt.plot_size(min(60, col_width), min(10, height))
            
            buf = io.StringIO()
            with redirect_stdout(buf):
                plt.show()
            lines = buf.getvalue().splitlines()
            all_lines.append(lines)
        return all_lines

    entry_lines = generate_graph_lines(entry_nodes)
    build_lines = generate_graph_lines(build_nodes)

    # Determine max lines for each row
    max_rows = max(len(entry_lines), len(build_lines))
    all_lines_combined = []
    
    # Add overall bottom title
    all_lines_combined.append(' ' * ((max_x - len("Data rate in GB/s")) // 2) + "Data rate in GB/s")
    all_lines_combined.append("")  # extra blank line below
    
    # Add column labels centered over their columns
    entry_label = "Entry Nodes"
    build_label = "Build Nodes"
    entry_centered = entry_label.center(col_width)
    build_centered = build_label.center(col_width)
    col_labels = entry_centered + ' ' * padding + build_centered
    all_lines_combined.append(col_labels)
    all_lines_combined.append("")  # extra blank line below
    for i in range(max_rows):
        left_lines = entry_lines[i] if i < len(entry_lines) else []
        right_lines = build_lines[i] if i < len(build_lines) else []

        # Pad shorter one to match length
        max_len = max(len(left_lines), len(right_lines))
        left_lines += [''] * (max_len - len(left_lines))
        right_lines += [''] * (max_len - len(right_lines))

        # Combine line by line with padding
        for l_line, r_line in zip(left_lines, right_lines):
            l_line = l_line.ljust(col_width)
            combined = l_line + ' ' * padding + r_line.ljust(col_width)
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

# ==========================
# Draw graphs (bottom 2/3)
# ==========================
def draw_Graph_V4(stdscr, data_dict, scroll_offset, start_y, height):
    max_y, max_x = stdscr.getmaxyx()
    all_lines = []

    # Generate plots for each entry
    for key, val in data_dict.items():
        plt.clf()
        data = val['data_array'][:]
        if len(data) > 20:
            data = data[-20:]
        lbl = calc_outout_str(key)
        plt.plot(data, label=lbl)
        plt.theme("dark")
        plt.title(lbl)
        plt.plot_size(min(60, max_x), min(10, height))  # limit to region size

        buf = io.StringIO()
        with redirect_stdout(buf):
            plt.show()
        plot_str = buf.getvalue()
        lines = plot_str.splitlines()
        all_lines.extend(lines + [""])  # empty line between graphs

    # Clamp scroll
    content_height = len(all_lines)
    scroll_offset = max(0, min(scroll_offset, max(0, content_height - height)))

    # Draw visible portion in the bottom region
    visible_lines = all_lines[scroll_offset:scroll_offset + height]
    for i, line in enumerate(visible_lines):
        result_arr = strip_and_translate_ansi_escape_sequences(line)
        x = 0
        color_pair = 0
        for tup in result_arr:
            if tup[0] == 'color':
                color_pair = tup[1]
            elif tup[0] == 'text':
                try:
                    stdscr.addstr(start_y + i, x, tup[1],
                                  curses.color_pair(int(color_pair)))
                except curses.error:
                    pass
                x += len(tup[1])

    return content_height
    
# =============================================================================
# Currently not used due to bad running time
# =============================================================================
def tail_file_v2(file_path):
    f = subprocess.Popen(['tail','-F',file_path],\
            stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    p = select.poll()
    p.register(f.stdout)
    
    while True:
        if p.poll(1):
            yield str(f.stdout.readline())
        time.sleep(0.5)
    
# =============================================================================
# mimics the tail function
# =============================================================================
def tail_file(file_path):
    f = subprocess.Popen(['tail', '-F', file_path],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        while not terminate_program:
            rlist, _, _ = select.select([f.stdout], [], [], 1) 
            line = str(f.stdout.readline(), 'utf-8').strip()
            if rlist:
                if "STATUS:" in line or "INFO:" in line:
                    yield line
    finally:
        f.terminate()
        
def tail_csv(file_path):
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

# =============================================================================
# This function is the main funxtion in of this file. It adds 
# the current data rate to the data dict and the starts the functions
# draw_Graph and draw_progress_bar
# =============================================================================
def main(stdscr,file_names, num_entry_nodes, num_build_nodes,enable_graph,enable_progress_bar):
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
    init_color_pairs_v2()
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
        entry_or_build = calc_outout_str(file_name[0])
        if 'entry node' in entry_or_build:
            USE_COLUMN = "[IB]OutKB"   
            COL_INDEX = COLUMN_MAP[USE_COLUMN]
        elif 'build node' in entry_or_build:
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
                        parts = next(val['tail'])
                        data_rate = get_data_rate(parts, val['COL_INDEX'])
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
                    stdscr, data_dict, num_entry_nodes, num_build_nodes,
                    progress_scroll, progress_height
                )
                progress_scroll = max(0, min(progress_scroll, content_height - progress_height))
        
            # Draw graphs
            if enable_graph:
                content_height = draw_Graph(
                    stdscr, data_dict, graph_scroll,
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
   
# =============================================================================
# Defines the signal handler for a clean end of the experiment. Currently only
# ctrl+c and sigterm are implemented. For safety reasons sigkill is not 
# implemented so it is recommended to only use it if the other two fails
# May be changed in the furture
# ============================================================================
def signal_handler_V2(signum, frame,stdscr):
    if signum == signal.SIGINT:
        cleanup(stdscr)
       #logger.error(f'received signal {signum}. Handling termination')
       #print(f'received signal {signum}. Handling termination')
    #elif signum == signal.SIGTERM:
        #logger.error(f'received signal {signum}. Handling termination')
        #print(f'received signal {signum}. Handling termination')
    #cleanup(stdscr)

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
        finally:
            curses.endwin()
            
def cleanup_V2(stdscr):
    global terminate_program
    if stdscr is not None:
        curses.endwin()
    terminate_program = True
