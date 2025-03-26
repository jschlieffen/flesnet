#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 19 17:22:50 2025

@author: jschlieffen
"""
import plotext as plt
import numpy as np
import pandas as pd

# Set date range
plt.date_form("d/m/Y")
start = plt.string_to_datetime("01/01/2023")
end = plt.today_datetime()
dates = pd.date_range(start=start, end=end, freq='B').strftime('%d/%m/%Y')  # Generate business days dates

# Generate random stock data
np.random.seed(42)  # For reproducibility
open_prices = np.random.rand(len(dates)) * 100 + 200  # Random open prices between 200 and 300
high_prices = open_prices + np.random.rand(len(dates)) * 10  # High prices slightly above open
low_prices = open_prices - np.random.rand(len(dates)) * 10  # Low prices slightly below open
close_prices = np.random.rand(len(dates)) * 100 + 200  # Random close prices between 200 and 300

# Combine data into a DataFrame
data = pd.DataFrame({
    'Open': open_prices,
    'High': high_prices,
    'Low': low_prices,
    'Close': close_prices
}, index=pd.to_datetime(dates, format='%d/%m/%Y'))

# Plotting
plt.clf()
plt.theme("dark")
plt.candlestick(dates, data)
plt.title("Random Stock Price CandleSticks")

plt.show()
