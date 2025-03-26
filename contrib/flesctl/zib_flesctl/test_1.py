#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 26 17:34:35 2025

@author: jschlieffen
"""
import curses
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import time
import io

def plot_to_ascii(fig, width, height):
    # Convert the plot to a PNG image in memory
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=80)
    buf.seek(0)
    
    # Open the image with Pillow
    img = Image.open(buf)
    img = img.resize((width, height))  # Resize image to fit the terminal
    
    # Convert to grayscale
    img = img.convert('L')
    
    # Convert the image to ASCII characters
    ascii_chars = "@%#*+=-:. "  # List of characters for gradient representation
    pixels = np.array(img)
    ascii_art = ""
    
    for row in pixels:
        for pixel in row:
            ascii_art += ascii_chars[pixel // 32]  # Map pixel value to one of the ASCII characters
        ascii_art += "\n"
    
    return ascii_art

def update_plot(stdscr):
    # Get terminal size
    height, width = stdscr.getmaxyx()

    # Create an initial figure for plotting
    fig, ax = plt.subplots(figsize=(width / 10, height / 10))
    
    # Set plot limits
    ax.set_xlim(0, 4 * np.pi)
    ax.set_ylim(-1.5, 1.5)
    
    # Generate some x-values for plotting
    x_vals = np.linspace(0, 4 * np.pi, 100)
    
    # Set plot appearance
    ax.set_facecolor('white')
    ax.plot(x_vals, np.sin(x_vals), label='Sine Wave')

    while True:
        # Create new data (sine wave with shifting phase)
        ax.clear()  # Clear the previous plot
        x_vals = np.linspace(0, 4 * np.pi, 100)
        ax.plot(x_vals, np.sin(x_vals + time.time()), label='Sine Wave')

        # Update the plot with the new data
        fig.canvas.draw()

        # Convert the plot to ASCII
        ascii_art = plot_to_ascii(fig, width - 2, height - 2)  # Reduce width and height for padding
        
        # Ensure that the ASCII art fits in the terminal size
        # Only display up to terminal height and width
        ascii_art_lines = ascii_art.split("\n")
        ascii_art_lines = ascii_art_lines[:height-3]  # Leave space for header

        # Clear the screen and print the ASCII art line by line
        stdscr.clear()
        stdscr.addstr(0, 0, f"Updating plot... Press 'q' to quit.\n")
        for idx, line in enumerate(ascii_art_lines):
            if idx < height - 3:  # Make sure it doesn't exceed the terminal height
                stdscr.addstr(idx + 2, 0, line)  # Start printing from line 2
        stdscr.refresh()

        # Wait for 1 second before updating again
        time.sleep(1)

        # Allow user to quit the loop by pressing 'q'
        key = stdscr.getch()
        if key == ord('q'):
            break

# Start the curses application
curses.wrapper(update_plot)

