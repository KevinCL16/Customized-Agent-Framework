# -*- coding: utf-8 -*-
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Data
fruits = ['Apples', 'Oranges', 'Bananas']
fruit_distribution = [35, 45, 20]
age_groups = ['Under 18', '18-30', '30-50', 'Over 50']
apple_favorability = [25, 40, 20, 15]
orange_favorability = [30, 30, 20, 20]  # Added for stackability
banana_favorability = [5, 10, 15, 20]  # Added for stackability

# Setup figure and axes
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))

# Plot pie chart
explode = (0.1, 0, 0)  # Only "explode" the 1st slice (i.e. 'Apples')
ax1.pie(fruit_distribution, labels=fruits, autopct='%1.1f%%', explode=explode, startangle=140)
ax1.set_title('Fruit Distribution in Basket')

# Plot stacked bar chart
ax2.bar(age_groups, apple_favorability, color='lightgreen', label='Apples')
ax2.bar(age_groups, orange_favorability, bottom=apple_favorability, color='orange', label='Oranges')
ax2.bar(age_groups, banana_favorability, bottom=[i+j for i,j in zip(apple_favorability, orange_favorability)], color='yellow', label='Bananas')
ax2.set_title('Fruit Favorability by Age Group')
ax2.set_xlabel('Age Groups')
ax2.set_ylabel('Percentage (%)')
ax2.legend()

# Add connecting lines
x_center_pie = -1.6
x_bar_start = 0.3
y_pie = [-0.45, -0.1]  # Adjusted positions based on pie positions
y_bar = [28, 18]       # Approx matching values for pie connections to bar

for i, yb in zip(y_pie, y_bar):
    ax2.plot([x_center_pie, x_bar_start], [yb, yb], 'k-', lw=1)

# Adjust layout for clarity
plt.tight_layout()

# Save the final plot to a file
plt.savefig('novice_final.png')