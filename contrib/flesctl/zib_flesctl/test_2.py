#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 26 18:30:25 2025

@author: jschlieffen
"""
import plotext as plt
import random
import subprocess
import time

# Function to generate random data
def generate_data():
    return [random.uniform(0, 7) for _ in range(20)]

# Function to display plot in a second terminal (same script)
def open_new_terminal():
    # Use subprocess to open a new terminal and run the same script
    subprocess.Popen(["mate-terminal", "--", "python3", "test_2.py", "second"])

# Function to plot data in the terminal
def plot_data():
    while True:
        data = generate_data()
        data_2 = generate_data()
        data_3 = generate_data()
        
        plt.clf()
        plt.plot(data)
        plt.plot(data_2)
        plt.plot(data_3)
        plt.theme("dark")
        plt.title("Random Numbers")
        plt.show()
        plt.clear_color()
        time.sleep(1)  # Update plot every 1 second

# Main function
def main():
    # If running as the main script, we open a new terminal
    if len(sys.argv) < 2 or sys.argv[1] != "second":
        open_new_terminal()  # Launch a new terminal for the second plot window
    else:
        plot_data()
    # Start plotting in the current terminal (first terminal)
    

if __name__ == "__main__":
    import sys
    main()
