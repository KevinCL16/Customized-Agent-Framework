# -*- coding: utf-8 -*-

import matplotlib
matplotlib.use('Agg')  # Use a non-interactive backend suitable for scripts
import matplotlib.pyplot as plt
import numpy as np

# Data preparation
z = np.linspace(-10, 10, 400)  # create 400 points from -10 to 10
w = np.linspace(-5, 5, 400)    # create 400 points from -5 to 5

# Create subplots with shared axes
fig, axs = plt.subplots(nrows=3, ncols=3, sharex='col', sharey='row', figsize=(8, 8))

# Adjust layout to remove spacing between subplots
fig.subplots_adjust(hspace=0, wspace=0)

# Plot in each subplot with specified colors
axs[0, 0].plot(z, w, color='b')          # Plot z against w
axs[0, 1].plot(z**3, w, color='blue')    # Plot z cubed against w
axs[0, 2].plot(-z, w + 1, color='yellow')    # Plot negative z against w + 1
axs[1, 0].plot(-z**3, w + 2, color='purple') # Plot negative z cubed against w + 2
axs[1, 1].plot(z**2, w**2, color='brown')    # Plot z squared against w squared
axs[1, 2].plot(-z**2, w**2 + 1, color='pink') # Plot negative z squared against w squared + 1
axs[2, 0].plot(z**2, -w**2 + 2, color='grey') # Plot z squared against negative w squared + 2
axs[2, 1].plot(-z**2, -w**2 + 3, color='black') # Plot negative z squared against negative w squared + 3
axs[2, 2].plot(z, -w, color='white')        # Plot z against negative w

# Hide tick labels for non-outermost plots
for i in range(2):
    for j in range(3):
        axs[i, j].label_outer()

for j in range(1, 3):
    for i in range(3):
        axs[i, j].label_outer()

# Set overall title for the figure
fig.suptitle('Sharing x per column, y per row')

# Save the plot to a PNG file
plt.savefig('novice.png')