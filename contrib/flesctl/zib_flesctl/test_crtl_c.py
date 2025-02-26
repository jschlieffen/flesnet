#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 26 13:55:57 2025

@author: jschlieffen
"""

import time

try:
    while True:
        print("Running... Press Ctrl+C to stop.")
        time.sleep(1)
except KeyboardInterrupt:
    print("\nCaught Ctrl+C! Exiting gracefully.")
