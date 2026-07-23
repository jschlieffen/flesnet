#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 23 16:16:29 2026

@author: jschlieffen
"""

import curses
import curses.textpad

import button as bu

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


def detail_window(stdscr, index):
    switch_on = False

    while True:
        stdscr.clear()

        h, w = stdscr.getmaxyx()

        # Number display
        text = f"Button {index}"

        stdscr.addstr(
            h // 2 - 3,
            (w - len(text)) // 2,
            text
        )

        # ON/OFF switch
        sy = h // 2 - 1
        sx = (w - 7) // 2

        by, bx, bw = bu.button(
            stdscr,
            sy,
            sx,
            switch_on
        )

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

        # Frame
        bu.draw_frame(
            stdscr,
            h // 2 - 5,
            (w // 2) - 15,
            h // 2 + 5,
            (w // 2) + 15
        )

        stdscr.refresh()

        key = stdscr.getch()

        if key == curses.KEY_MOUSE:
            try:
                _, mx, my, _, state = curses.getmouse()

                if state & curses.BUTTON1_CLICKED:

                    # Toggle switch
                    if (
                        my == by
                        and bx <= mx < bx + bw
                    ):
                        switch_on = not switch_on

                    # Return
                    elif (
                        my == ry
                        and rx <= mx < rx + len(return_text)
                    ):
                        return

            except curses.error:
                pass


def main(stdscr):

    num_buttons = 5

    button_states = [False] * num_buttons

    curses.curs_set(0)
    curses.start_color()

    init_color_pairs()

    curses.mousemask(curses.ALL_MOUSE_EVENTS)
    stdscr.keypad(True)

    while True:

        stdscr.clear()

        h, w = stdscr.getmaxyx()

        # Exit button
        exit_text = "[ Exit ]"
        exit_y = 1
        exit_x = (w - len(exit_text)) // 2

        stdscr.attron(curses.color_pair(1))
        stdscr.addstr(
            exit_y,
            exit_x,
            exit_text
        )
        stdscr.attroff(curses.color_pair(1))


        buttons = []

        start_y = 4

        for i in range(num_buttons):

            y = start_y + i
            x = 5

            label = f"Button {i}:"

            stdscr.addstr(
                y,
                x,
                label
            )

            by, bx, bw = bu.button(
                stdscr,
                y,
                x + len(label) + 1,
                button_states[i]
            )

            buttons.append(
                (by, bx, bw, i)
            )


        # Golden frame around buttons
        frame_left = 3
        frame_right = 5 + len("Button 0:") + 1 + 7 + 2
        
        bu.draw_frame(
            stdscr,
            start_y - 1,
            frame_left,
            start_y + num_buttons,
            frame_right
        )

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


                    # Buttons
                    for by, bx, bw, index in buttons:

                        if (
                            my == by
                            and bx <= mx < bx + bw
                        ):
                            button_states[index] = not button_states[index]

                            detail_window(
                                stdscr,
                                index
                            )

            except curses.error:
                pass


if __name__ == "__main__":
    curses.wrapper(main)
