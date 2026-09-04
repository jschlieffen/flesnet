#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 24 21:21:02 2026

@author: jschlieffen
"""

import curses
import interface.interface as interface
import interface.button as bu
import time
import interface.interface_params as inp

def draw_main_frame(stdscr):
    h, w = stdscr.getmaxyx()
    buttons = {
        "Start": {
            "y": 5,
            "x": 10,
        },
        "Stop": {
            "y": 8,
            "x": 10,
        },
        "Show nodes": {
            "y": 11,
            "x": 10,
        },
    }
    bu.draw_frame(
        stdscr,
        3,
        5,
        14,
        30,
    )
    for name, pos in buttons.items():
        stdscr.addstr(
            pos["y"],
            pos["x"],
            f"[ {name} ]"
        )
    return buttons

def init_color_pairs():
    curses.use_default_colors()

    # Exit
    curses.init_pair(
        1,
        curses.COLOR_WHITE,
        curses.COLOR_RED
    )

    # Active button
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

    # Input field
    curses.init_pair(
        5,
        curses.COLOR_WHITE,
        curses.COLOR_BLUE
    )

    # Selected input field
    curses.init_pair(
        6,
        curses.COLOR_BLACK,
        curses.COLOR_CYAN
    )


def main_frame(stdscr, filenames, parameters):
    show_nodes = False
    buttons_dict = None
    max_label_ = len("start simmulation")
    init_color_pairs()
    curses.mousemask(curses.ALL_MOUSE_EVENTS)
    stdscr.keypad(True)
    while True:
        h, w = stdscr.getmaxyx()
        stdscr.clear()
        stdscr.addstr(4, 5, "stop simulation")
        stop_y,stop_x, stop_w = bu.button(stdscr,4, 5+max_label_ +2, False)
        stdscr.addstr(6, 5, "Show nodes")
        show_y, show_x, show_w = bu.button(stdscr,6, 5+max_label_ +2, show_nodes)
        exit_text = "[ X ]"
        exit_y = 0
        exit_x = (w - len(exit_text)) 
        stdscr.attron(curses.color_pair(1))
        stdscr.addstr(exit_y,exit_x,exit_text)
        stdscr.attroff(curses.color_pair(1))
        if show_nodes:
            if buttons_dict is None:
                buttons_dict = interface.create_buttons_dict(filenames,**parameters)
            interface.draw_nodes(stdscr, buttons_dict)
        stdscr.refresh()
        key = stdscr.getch()
        if key == curses.KEY_MOUSE:
            _, mx, my, _, state = curses.getmouse()
            if state & curses.BUTTON1_CLICKED:
                if (my == exit_y and exit_x <= mx < exit_x + len(exit_text)):
                    return 'nan'
                if (my == stop_y) and stop_x <= mx < stop_x + stop_w:
                    return 'stop'
                if (my == show_y and show_x <= mx < show_x + show_w):
                    show_nodes = not show_nodes
                elif show_nodes:

                    interface.handle_nodes_click(stdscr,buttons_dict, mx, my)
                    
                    
def main_start_frame(stdscr):
    init_color_pairs()
    curses.mousemask(curses.ALL_MOUSE_EVENTS)
    stdscr.keypad(True)
    interface = inp.interface_params()
    interface.scroll_offset = 0
    interface.max_scroll = 0

    while True:
        h, w = stdscr.getmaxyx()
        stdscr.erase()
        top_height = h // 3
        bottom_y = top_height
        bottom_height = h - bottom_y
        for x in range(w):
            try:
                stdscr.addch(bottom_y, x, curses.ACS_HLINE)
            except curses.error:
                pass
        max_label_ = len("start simmulation")
        stdscr.addstr(2,5,"start simmulation")
        start_y, start_x, start_w = bu.button(stdscr,2, 5 + max_label_ + 2, False)
        stdscr.addstr(4,5,"allocate nodes")
        alloc_y, alloc_x, alloc_w = bu.button(stdscr,4, 5 + max_label_ + 2, False)
        exit_text = "[ X ]"
        exit_y = 0
        exit_x = w - len(exit_text) - 1
        stdscr.attron(curses.color_pair(1))
        stdscr.addstr(exit_y, exit_x, exit_text)
        stdscr.attroff(curses.color_pair(1))
        parameter_x = 2
        parameter_y = bottom_y + 1
        parameter_width = w - 4
        parameter_height = bottom_height - 2
        fields = []
        if parameter_height > 2:
            bottom_y = h // 3
            parameter_y = bottom_y + 1
            parameter_height = h - parameter_y - 1
            parameter_width = w - 1
            parameter_win = stdscr.derwin(parameter_height, parameter_width,parameter_y, 0)
            parameter_win.erase()
            actual_height, actual_width = parameter_win.getmaxyx()
            fields, content_bottom = interface.display_parameter_groups(parameter_win, 0, 0, actual_width, actual_height, interface.scroll_offset)
            content_height = content_bottom
            interface.max_scroll = max(0, content_bottom - actual_height)
            interface.scroll_offset = max(0, min(interface.scroll_offset,interface.max_scroll))
            parameter_win.noutrefresh()
            if interface.max_scroll > 0:
                scrollbar_x = w - 1
                for y in range(parameter_y, parameter_y + parameter_height):
                    try:
                        stdscr.addch(y,scrollbar_x,curses.ACS_VLINE)
                    except curses.error:
                        pass
                thumb_height = max(1, int(parameter_height* parameter_height/ content_height))
                max_thumb_position = (parameter_height - thumb_height)
                thumb_position = int((interface.scroll_offset / interface.max_scroll)* max_thumb_position)
                for y in range(parameter_y + thumb_position, parameter_y + thumb_position + thumb_height):
                    try:
                        stdscr.addch(y,scrollbar_x,curses.ACS_BLOCK)
                    except curses.error:
                        pass
        stdscr.refresh()
        key = stdscr.getch()
        parameter_y = bottom_y + 1
        parameter_height = h - parameter_y - 1
        parameter_top = parameter_y
        parameter_bottom = parameter_y + parameter_height - 1
        if key == curses.KEY_MOUSE:
            try:
                _, mx, my, _, state = curses.getmouse()
            except curses.error:
                continue
            if state & curses.BUTTON4_PRESSED:
                if parameter_top <= my <= parameter_bottom:
                    interface.scroll_offset = max(0,interface.scroll_offset - 2)        
                continue        
            if state & curses.BUTTON5_PRESSED:
                if parameter_top <= my <= parameter_bottom:
                    interface.scroll_offset = min(interface.max_scroll,interface.scroll_offset + 2)
                continue
            if state & curses.BUTTON1_CLICKED:
                if (my == exit_y and exit_x <= mx < exit_x + len(exit_text)):
                    return 'exit'
                if (start_y <= my < start_y + 1 and start_x <= mx < start_x + start_w):
                    return 'start'
                if (alloc_y <= my < alloc_y + 1) and alloc_x <= mx < alloc_x + alloc_w:
                    return 'alloc'
            elif (parameter_y <= my < parameter_y + parameter_height):
                local_x = mx
                local_y = my - parameter_y
                interface.handle_parameter_mouse(local_x,local_y,fields)
                continue
        else:
            if key == 27:
                return
            elif key == curses.KEY_UP:
                interface.scroll_offset = max(0,interface.scroll_offset - 1)
            elif key == curses.KEY_DOWN:
                interface.scroll_offset = min(interface.max_scroll,interface.scroll_offset + 1)
            elif key == curses.KEY_PPAGE:
                interface.scroll_offset = max(0,interface.scroll_offset - parameter_height)
            elif key == curses.KEY_NPAGE:
                interface.scroll_offset = min(interface.max_scroll,interface.scroll_offset + parameter_height)
            elif key == curses.KEY_HOME:
                interface.scroll_offset = 0
            elif key == curses.KEY_END:
                interface.scroll_offset = interface.max_scroll
            else:
                interface.handle_parameter_key(key)
                
                
def main_intermediate_frame(stdscr):
    max_label_ = len("start simmulation")
    init_color_pairs()

    curses.mousemask(curses.ALL_MOUSE_EVENTS)
    stdscr.keypad(True)
    stdscr.nodelay(True)
    msg = ''
    while msg != '0: done starting':
        h, w = stdscr.getmaxyx()
        stdscr.clear()
        with open('tmp/interface/interface_response.txt','r') as f:
            msg = f.read()
        stdscr.addstr(h//2,w//2,"starting simulatation")
        stdscr.addstr(h//2 + 2,w//2,"to see the current state open a new terminal, connect to cluster and enter tmux attach-session")
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

        stdscr.refresh()

        key = stdscr.getch()


        if key == curses.KEY_MOUSE:
            

            _, mx, my, _, state = curses.getmouse()

            if state & curses.BUTTON1_CLICKED:
                if (my == exit_y and exit_x <= mx < exit_x + len(exit_text)):
                    return 'exit'
        time.sleep(0.1)
    return 'start'
                
                    
    