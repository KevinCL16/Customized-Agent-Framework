# -*- coding: utf-8 -*-

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

# Pie chart data
fruit_labels = ['Apples', 'Oranges', 'Bananas']
fruit_sizes = [35, 45, 20]
explode = (0.1, 0, 0)  # Exploding the 'Apples' slice

# Stacked bar chart data
age_groups = ['Under 18', '18-30', '30-50', 'Over 50']
apples_distribution = [25, 40, 20, 15]

# Set up the figure and axes
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6), gridspec_kw={'width_ratios': [1, 1.5]})

# Create the Pie Chart
ax1.pie(fruit_sizes, explode=explode, labels=fruit_labels, autopct='%1.1f%%', startangle=90, shadow=True)
ax1.set_title('Fruit Distribution in Basket')

# Create the Stacked Bar Chart
bar = ax2.bar(age_groups, apples_distribution, color='lightgreen')
ax2.set_title('Apples Favorability by Age Group')
ax2.set_ylabel('Percentage (%)')
ax2.set_ylim(0, 100)  # Ensuring the y-axis limit is 100 for percentage
ax2.set_xlabel('Age Groups')

# Draw connection lines (manual adjustment for visual clarity)
# These lines start from the 'Apples' segment tip of the pie chart to the respective age group on the bar chart.
line1 = plt.Line2D([0.22, 1.05], [0.4, apples_distribution[0]/100 + 0.03], color='black', linewidth=1)
line2 = plt.Line2D([0.22, 1.05], [0.4, apples_distribution[-1]/100 + 0.03], color='black', linewidth=1)
fig.add_artist(line1)
fig.add_artist(line2)

# Adjust layout
plt.tight_layout()

# Save the plot to a PNG file
plt.savefig("novice.png")