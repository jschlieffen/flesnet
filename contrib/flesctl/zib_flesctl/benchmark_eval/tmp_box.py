import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Generate 40 different groups of data using lists
np.random.seed(42)
data = []

for i in range(1, 41):  # 40 groups
    values = np.random.normal(loc=i, scale=2.0, size=20)  # 20 values per group
    data.append(values)

# Plot
plt.figure(figsize=(20, 6))
sns.boxplot(data=data)
plt.xticks(range(40), [f'Group {i}' for i in range(1, 41)], rotation=90)
plt.title("Boxplot of 40 Groups")
plt.xlabel("Group")
plt.ylabel("Value")
plt.tight_layout()
plt.show()
