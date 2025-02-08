import matplotlib.pyplot as plt

# Explicitly set the backend to 'Agg' to handle environments that may not be set up for interactive plotting
plt.switch_backend('Agg')

# Data for the pie chart
fruit_labels = ['Apples', 'Oranges', 'Bananas']
fruit_sizes = [35, 45, 20]
fruit_explode = (0.1, 0, 0)  # Explode the 'Apples' slice

# Data for the stacked bar chart
age_groups = ['Under 18', '18-30', '30-50', 'Over 50']
apple_distribution = [25, 40, 20, 15]

# Create a figure with two subplots
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))

# Plot the pie chart
ax1.pie(fruit_sizes, explode=fruit_explode, labels=fruit_labels, autopct='%1.1f%%', startangle=90)
ax1.set_title('Fruit Distribution in Basket')

# Plot the stacked bar chart
ax2.bar(age_groups, apple_distribution, color='skyblue', label='Apples')
ax2.set_title('Distribution of People Favoring Apples')
ax2.set_ylabel('Percentage')
ax2.set_ylim(0, 100)
ax2.legend()

# Adjust layout for clarity and aesthetics
plt.tight_layout()

# Save the plot to a file
plt.savefig('novice.png')

# Display the plot (optional if running with a non-interactive backend)
# plt.show()