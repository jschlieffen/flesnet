#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 23 18:23:09 2026

@author: jschlieffen
"""
import curses
import curses.textpad
import button as bu

def nodes_info(stdscr, node_type, node):
    switch_on = False
    buttons_index = ["node info","check active", "kill node","revieve node", "remove node"]
    button_states = [False] * 5
    start_y, start_x = 5,5
    buttons = []
    max_len_buttons = max(len(i) for i in buttons_index)
    while True:
        stdscr.clear()

        h, w = stdscr.getmaxyx()

        # Number display
        text = f"{node_type} {node}"

        stdscr.addstr(
            1,
            (w - len(text)) // 2,
            text
        )

        button_spacing = 3
        switch_width = 7

        x = start_x

        for i,index in enumerate(buttons_index):
            #x = start_x + i * spacing
            y = start_y
        
            label = f"{index}:"
        
            stdscr.addstr(y, x, label)
        
            by, bx, bw = bu.button(
                stdscr,
                y,
                x + len(label) + 1,
                button_states[i]
            )
        
            buttons.append((by, bx, bw, i))
            x += len(label) + 1 + switch_width + button_spacing
        # Return button
        return_text = "[ Return ]"

        ry = h // 2 + 3
        rx = (w - len(return_text)) // 2

        stdscr.attron(curses.color_pair(1))
        stdscr.addstr(
            ry,
            rx,
            return_text
        )
        stdscr.attroff(curses.color_pair(1))

        frame_left = start_x - 2
        frame_top = start_y - 1
        
        frame_right = x - button_spacing + 1
        frame_bottom = start_y + 1
        
        bu.draw_frame(
            stdscr,
            frame_top,
            frame_left,
            frame_bottom,
            frame_right
        )
        stdscr.refresh()

        key = stdscr.getch()

        if key == curses.KEY_MOUSE:
            try:
                _, mx, my, _, state = curses.getmouse()

                if state & curses.BUTTON1_CLICKED:

                    # Toggle switch
                    for by, bx, bw, index in buttons:

                        if (
                            my == by
                            and bx <= mx < bx + bw
                        ):
                            button_states[index] = not button_states[index]
                            with open('tmp/interface/interface_commands.txt','w') as f:
                                f.write(f'{node_type}_{node}: {buttons_index[index]}')

                    # Return
                    if (
                        my == ry
                        and rx <= mx < rx + len(return_text)
                    ):
                        return

            except curses.error:
                pass

