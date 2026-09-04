#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 23 17:08:02 2026

@author: jschlieffen
"""

import curses


def button(stdscr, y, x, on_off):
    width = 7

    if on_off:
        # ON | OFF
        stdscr.attron(curses.color_pair(2))
        stdscr.addstr(y, x, " ON ")
        stdscr.attroff(curses.color_pair(2))

        stdscr.attron(curses.color_pair(3))
        stdscr.addstr(y, x + 4, "OFF")
        stdscr.attroff(curses.color_pair(3))

    else:
        # ON | OFF
        stdscr.attron(curses.color_pair(3))
        stdscr.addstr(y, x, " ON ")
        stdscr.attroff(curses.color_pair(3))

        stdscr.attron(curses.color_pair(2))
        stdscr.addstr(y, x + 4, "OFF")
        stdscr.attroff(curses.color_pair(2))

    return y, x, width

def draw_frame(stdscr, y1, x1, y2, x2):
    h, w = stdscr.getmaxyx()
    if y2 < 0 or y1 >= h:
        return
    if x2 < 0 or x1 >= w:
        return
    y1 = max(0, y1)
    x1 = max(0, x1)
    y2 = min(h - 1, y2)
    x2 = min(w - 1, x2)
    if y1 >= y2 or x1 >= x2:
        return
    try:
        stdscr.attron(curses.color_pair(4))
        curses.textpad.rectangle(stdscr, y1,x1, y2, x2 )
    except curses.error:
        pass
    finally:
        stdscr.attroff(curses.color_pair(4))