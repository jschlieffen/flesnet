#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 26 17:34:35 2025

@author: jschlieffen
"""

import plotext as plt
import curses
import re
from contextlib import redirect_stdout
import io

# Function to strip ANSI escape sequences (for plain text display)
def strip_ansi_escape_sequences(text):
    ansi_escape = re.compile(r'(?:\x1b\[[0-9;]*[mGKHfaboA-DX]?)')
    return ansi_escape.sub('', text)

# Function to extract the color codes from the plotext string
def extract_colors(text):
    # This regex will match color escape sequences in plotext
    color_escape = re.compile(r'(\x1b\[[0-9;]*m)')
    return color_escape.findall(text)

def main(stdscr):
    # Clear the screen
    stdscr.clear()

    # Initialize curses color support
    curses.start_color()
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_BLUE, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
    curses.init_pair(6, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(7, curses.COLOR_WHITE, curses.COLOR_BLACK)

    # Data for the plot
    x = [i for i in range(10)]
    y = [i ** 2 for i in range(10)]  # Simple quadratic data

    # Create the plot using plotext
    plt.plot(x, y)

    # Set plot title and labels
    plt.title("Quadratic Function")
    plt.xlabel("X-axis")
    plt.ylabel("Y-axis")

    buf = io.StringIO()
    with redirect_stdout(buf):
        #plt.figtext()  # This will print the plot to the StringIO buffer
        plt.show()
    # Get the plot as a string from the buffer
    plot_str = buf.getvalue()
    # Extract color sequences to preserve
    color_sequences = extract_colors(plot_str)
    
    # Strip color codes to get plain text
    plot_str = strip_ansi_escape_sequences(plot_str)

    # Split the plot into lines
    plot_lines = plot_str.splitlines()

    # Display the plot line-by-line using curses
    color_idx = 0
    for i, line in enumerate(plot_lines):
        for char in line:
            # Check if we have a color to apply
            if color_idx < len(color_sequences):
                # Activate the color for this character
                color_code = color_sequences[color_idx]
                if '38;5;10' in color_code:
                    stdscr.attron(curses.color_pair(2))  # Green
                elif '38;5;9' in color_code:
                    stdscr.attron(curses.color_pair(1))  # Red
                elif '38;5;11' in color_code:
                    stdscr.attron(curses.color_pair(4))  # Yellow
                # Add more color mappings as needed

                stdscr.addstr(i, len(line) + color_idx, char)
                stdscr.attroff(curses.color_pair(0))  # Reset color

            else:
                # Print the regular characters if no color is specified
                stdscr.addstr(i, color_idx, char)
            color_idx += 1

    # Refresh the screen to display the plot
    stdscr.refresh()

    # Wait for user input to exit
    stdscr.getch()

# Initialize the curses application
curses.wrapper(main)

