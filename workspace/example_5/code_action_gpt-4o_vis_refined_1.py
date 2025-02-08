import matplotlib.pyplot as plt
import numpy as np

# Set Matplotlib backend to 'Agg' for non-GUI usage
plt.switch_backend('Agg')

# Data for pie chart
labels = ['Apples', 'Oranges', 'Bananas']
sizes = [35, 45, 20]
colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
explode = (0.1, 0, 0)  # Only explode the 1st slice (i.e., 'Apples')

# Data for stacked bar chart
age_groups = ['Under 18', '18-30', '30-50', 'Over 50']
apple_distribution = [25, 40, 20, 15]  # Example data for apples
orange_distribution = [30, 35, 25, 10]  # Example data for oranges
banana_distribution = [10, 20, 30, 40]  # Example data for bananas

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))

# Pie Chart
ax1.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%',
        shadow=True, startangle=90)
ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
ax1.set_title('Fruit Distribution in Basket')

# Stacked Bar Chart
ax2.bar(age_groups, apple_distribution, color=colors[0], label=labels[0])
ax2.bar(age_groups, orange_distribution, bottom=apple_distribution, color=colors[1], label=labels[1])
ax2.bar(age_groups, banana_distribution, bottom=np.array(apple_distribution) + np.array(orange_distribution), color=colors[2], label=labels[2])
ax2.set_ylabel('Percentage')
ax2.set_title('Distribution of People Favoring Fruits')
ax2.legend()

# Lines connecting pie and bar chart
# Calculate the coordinates for the lines
# These are example coordinates, adjust them based on your layout
ax2.plot([0.5, 0.5], [35, 25], 'k-', lw=1)  # Line for Apples
ax2.plot([0.5, 1.5], [35, 40], 'k-', lw=1)  # Line for Oranges
ax2.plot([0.5, 2.5], [35, 60], 'k-', lw=1)  # Line for Bananas

plt.subplots_adjust(wspace=0.5)  # Adjust spacing between plots
plt.savefig('novice_final.png')  # Save the figure
plt.show()  # If a GUI is available, this will display it.