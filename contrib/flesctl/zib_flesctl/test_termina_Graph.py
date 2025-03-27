#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 19 17:22:50 2025

@author: jschlieffen
"""
#import plotext as plt
import matplotlib.pyplot as plt
import curses

def main(stdscr):
    # Clear the screen
    stdscr.clear()

    # Data for the plot
    x = [i for i in range(10)]
    y = [i ** 2 for i in range(10)]  # Simple quadratic data

    # Create the plot using plotext
    plt.plot(x, y)

    # Set plot title and labels
    plt.title("Quadratic Function")
    plt.xlabel("X-axis")
    plt.ylabel("Y-axis")

    # Now, render the plot as a string and display via curses
    #plot_str = plt.figtext()

    # Display the plot in the terminal using curses
    stdscr.addstr(0, 0, plot_str)  # Positioning at the top-left corner
    stdscr.refresh()

    # Wait for user input to exit
    stdscr.getch()

# Initialize the curses application
curses.wrapper(main)


