#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 19 17:22:50 2025

@author: jschlieffen
"""

import plotext as plt
import time
import random

data = []

try:
    while True:
        # Simulate new data point
        new_value = random.randint(0, 100)
        data.append(new_value)
        
        # Keep only the latest 20 data points
        if len(data) > 20:
            data.pop(0)

        plt.clt()  # Clear terminal
        plt.plot(data)
        plt.title("Real-Time Data Plot")
        plt.ylim(0, 100)  # Adjust y-axis limits if necessary
        plt.show()
        
        # Display additional info below the graph
        print(f"Latest Value: {new_value}")
        print(f"Average Value: {sum(data) / len(data):.2f}")
        print(f"Data Points: {data}")

        time.sleep(1)  # Refresh every second

except KeyboardInterrupt:
    print("Plotting stopped.")
