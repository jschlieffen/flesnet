import matplotlib.pyplot as plt
import numpy as np

# Example data: list of lists (e.g., multiple measurements over time)
data = [
    [1, 2, 3, 4, 5],
    [2, 3, 4, 3, 4],
    [1, 3, 2, 5, 3],
    [2, 2, 4, 4, 5]
]

# Convert to numpy array for easier manipulation
data_array = np.array(data)

# Compute statistics across the lists
mean_values = np.mean(data_array, axis=0)
min_values = np.min(data_array, axis=0)
max_values = np.max(data_array, axis=0)

# Create x-axis (e.g., indices)
x = np.arange(data_array.shape[1])

# Plotting
plt.figure(figsize=(10, 6))

# Light grey fill between min and max
plt.fill_between(x, min_values, max_values, color='lightgrey', label='Range (min-max)')

# Plot mean line
plt.plot(x, mean_values, color='blue', label='Mean', linewidth=2)

# Plot min and max lines
plt.plot(x, min_values, color='grey', linestyle='--', label='Min')
plt.plot(x, max_values, color='grey', linestyle='--', label='Max')

# Final touches
plt.xlabel('Index')
plt.ylabel('Value')
plt.title('Mean, Min, and Max with Shaded Range')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
