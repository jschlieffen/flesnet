#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 23 16:16:29 2026

@author: jschlieffen
"""

import curses
import curses.textpad
import re
import interface.button as bu
import interface.nodes_info as ni
import traceback

def calc_output_str(input_string):
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
        (
            r"logs/collectl/timeslice_forwarding/central_manager/central_manager_(.+?)\.csv",
            lambda m: f"Central manager: {m.group(1)}"
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


def create_buttons_dict(filenames, num_receiver_nodes, num_input_nodes, 
                        num_output_nodes, num_cm, use_GSI_TS_forwarding, use_ZIB_TS_forwarding):
    buttons_dict = {}


    if use_GSI_TS_forwarding:
        if not use_flesnet:
            sender_nodes = [(calc_output_str(filename),filename) for filename in filenames if 'sender node' in calc_output_str(filename)]
        else: 
            sender_nodes = [(calc_output_str(filename).replace('build','sender'),filename) for filename in filenames if 'build node' in calc_output_str(filename)]
        receiver_nodes = [(calc_output_str(filename),filename) for filename in filenames if 'receiving node' in calc_output_str(filename)]
        buttons_dict["Timeslice forwarding"] = {
            "Sender nodes": {
                "num_nodes": num_receiver_nodes,
                "states": [False] * num_receiver_nodes,
                "buttons": [],
                'nodes' : sender_nodes
            },
            "Receiver nodes": {
                "num_nodes": num_receiver_nodes,
                "states": [False] * num_receiver_nodes,
                "buttons": [],
                'nodes' : receiver_nodes
            },
        }

    if use_ZIB_TS_forwarding:

        input_nodes = [(calc_output_str(filename),filename)  for filename in filenames if 'input node' in calc_output_str(filename)]
        output_nodes = [(calc_output_str(filename),filename)  for filename in filenames if 'output node' in calc_output_str(filename)]
        cm_nodes = [(calc_output_str(filename),filename) for filename in filenames if "Central manager" in calc_output_str(filename)]
        buttons_dict["ZIB TS forwarding"] = {
            "Central manager": {
                "num_nodes": num_cm,
                "states": [False] * num_cm,
                "buttons": [],
                'nodes' : cm_nodes
            },
            "Input nodes": {
                "num_nodes": num_input_nodes,
                "states": [False] * num_input_nodes,
                "buttons": [],
                'nodes' : input_nodes
            },
            "Output nodes": {
                "num_nodes": num_output_nodes,
                "states": [False] * num_output_nodes,
                "buttons": [],
                'nodes' : output_nodes
            },
        }

    return buttons_dict


def init_color_pairs():
    curses.use_default_colors()

    # Exit
    curses.init_pair(
        1,
        curses.COLOR_WHITE,
        curses.COLOR_RED
    )

    # Active
    curses.init_pair(
        2,
        curses.COLOR_BLACK,
        curses.COLOR_GREEN
    )

    # Inactive
    curses.init_pair(
        3,
        curses.COLOR_WHITE,
        curses.COLOR_BLACK
    )

    # Golden frame
    curses.init_pair(
        4,
        curses.COLOR_YELLOW,
        -1
    )

def draw_button_group(stdscr,title,start_y,start_x,states,node_names):
    buttons = []
    #max_label = len(f"Button {num_buttons-1}:")
    max_label = max(len(node_name[0]) for node_name in node_names)
    stdscr.addstr(
        start_y - 2,
        start_x,
        title
    )

    for i,node_name in enumerate(node_names) :
        y = start_y + i
        label = node_name[0]
        stdscr.addstr(
            y,
            start_x,
            label
        )
        by, bx, bw = bu.button(
            stdscr,
            y,
            start_x + max_label + 1,
            states[i]
        )
        buttons.append(
            (by, bx, bw, i)
        )
    frame_left = start_x - 2
    frame_right = start_x + max_label + 1 + 7 + 2

    frame_top = start_y - 1
    frame_bottom = start_y + len(node_names)

    bu.draw_frame(
        stdscr,
        frame_top,
        frame_left,
        frame_bottom,
        frame_right
    )

    return {
        "buttons": buttons,
        "top": start_y - 2,       # includes title
        "bottom": frame_bottom,
        "left": frame_left,
        "right": frame_right,
    }


            
def handle_nodes_click(stdscr, buttons_dict, mx, my):

    for column_name, groups in buttons_dict.items():

        for node_type, info in groups.items():

            for by, bx, bw, index in info["buttons"]:

                if my == by and bx <= mx < bx + bw:
                    tmp,node = info['nodes'][index][0].split(': ')
                    if ni.nodes_info(
                        stdscr,
                        node_type,
                        node
                    ) == 1:
                        return True

    return False


def draw_nodes(stdscr, buttons_dict):

    start_x = 5
    start_y = 10        
    column_spacing = 4

    current_x = start_x

    for column_name, groups in buttons_dict.items():

        column_top = None
        column_bottom = None
        column_left = None
        column_right = None

        current_y = start_y

        for group_name, info in groups.items():
            with open('debu2.log','w') as f:
                f.write(group_name)
                f.close()
            result = draw_button_group(
                stdscr,
                group_name,
                current_y,
                current_x,
                info["states"],
                info["nodes"]
            )

            info["buttons"] = result["buttons"]

            if column_top is None:
                column_top = result["top"]
                column_left = result["left"]

            column_bottom = result["bottom"]

            column_right = max(
                column_right or 0,
                result["right"]
            )

            current_y = result["bottom"] + 3


        bu.draw_frame(
            stdscr,
            column_top - 1,
            column_left - 1,
            column_bottom + 1,
            column_right + 1
        )

        current_x = column_right + column_spacing
        
        
def main(stdscr, filenames,num_entry_nodes, num_build_nodes, num_receiver_nodes, num_input_nodes, num_output_nodes, num_cm,
         use_flesnet, use_GSI_TS_forwarding, use_ZIB_TS_forwarding):

    buttons_dict = create_buttons_dict(filenames,num_entry_nodes, num_build_nodes, num_receiver_nodes, num_input_nodes, 
                                       num_output_nodes, num_cm, use_flesnet, use_GSI_TS_forwarding, use_ZIB_TS_forwarding)
    curses.curs_set(0)
    curses.start_color()

    init_color_pairs()

    curses.mousemask(curses.ALL_MOUSE_EVENTS)
    stdscr.keypad(True)
    
    
    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        exit_text = "[ X ]"
        exit_y = 0
        exit_x = (w - len(exit_text)) 
        stdscr.attron(curses.color_pair(1))
        stdscr.addstr(
            exit_y,
            exit_x,
            exit_text
        )
        stdscr.attroff(curses.color_pair(1))
        start_x = 5
        start_y = 4
        column_spacing = 4
        current_x = start_x
        for column_name, groups in buttons_dict.items():
            column_top = None
            column_bottom = None
            column_left = None
            column_right = None
            current_y = start_y
            with open('debug.log','w') as f:
                f.write(str(groups))
            for group_name, info in groups.items():
                result = draw_button_group(
                    stdscr,
                    group_name,
                    current_y,
                    current_x,
                    info["states"],
                    info['nodes']
                )
                info["buttons"] = result["buttons"]
                if column_top is None:
                    column_top = result["top"]
                    column_left = result["left"]
                column_bottom = result["bottom"]
                column_right = max(
                    column_right or 0,
                    result["right"]
                )
                current_y = result["bottom"] + 3
            bu.draw_frame(
                stdscr,
                column_top - 1,
                column_left - 1,
                column_bottom + 1,
                column_right + 1,
            )
            current_x = column_right + column_spacing

        stdscr.refresh()

        key = stdscr.getch()


        if key == curses.KEY_MOUSE:
            try:
                _, mx, my, _, state = curses.getmouse()

                if state & curses.BUTTON1_CLICKED:

                    # Exit
                    if (
                        my == exit_y
                        and exit_x <= mx < exit_x + len(exit_text)
                    ):
                        return

                    
                    for column_name, groups in buttons_dict.items():
                    
                        for node_type, info in groups.items():
                    
                            for by, bx, bw, index in info["buttons"]:
                    
                                if my == by and bx <= mx < bx + bw:
                    
                                    #info["states"][index] = not info["states"][index]
                    
                                    if ni.nodes_info(
                                        stdscr,
                                        node_type,
                                        index
                                    ) == 1:
                                        return
            except curses.error:
                pass
            
if __name__ == "__main__":
    file_names = []
    with open('mon_parameters.txt', 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith("file_name:"):
                _, data = line.split("file_name: ")
                logfile, file_data = data.split(", ")
                file_names.append(logfile)
            elif line.startswith("num_buildnodes:"):
                num_buildnodes = int(line.split(": ")[1])
            elif line.startswith("num_entrynodes:"):
                num_entrynodes = int(line.split(": ")[1])
            elif line.startswith("num_receivers: "):
                num_receivers = int(line.split(": ")[1])
            elif line.startswith("num_inputnodes: "):
                num_inputnodes = int(line.split(": ")[1])
            elif line.startswith("num_outputnodes: "):
                num_outputnodes = int(line.split(": ")[1])
            elif line.startswith("num_cm: "):
                num_cm = int(line.split(": ")[1])
            elif line.startswith("enable_graph:"):
                enable_graph = line.split(": ")[1] == '1'
            elif line.startswith("enable_progess_bar:"):
                enable_progess_bar = line.split(": ")[1] == '1'
            elif line.startswith("use_flesnet:"):
                use_flesnet = line.split(": ")[1] == '1'
            elif line.startswith("use_GSI_TS_forwarding: "):
                use_GSI_TS_forwarding = line.split(": ")[1] == '1'
            elif line.startswith("use_ZIB_TS_forwarding: "):
                use_ZIB_TS_forwarding = line.split(": ")[1] == '1'

    curses.wrapper(main,file_names,num_entrynodes, num_buildnodes, num_receivers, num_inputnodes, num_outputnodes, num_cm,
             use_flesnet, use_GSI_TS_forwarding, use_ZIB_TS_forwarding)

