# -*- coding: utf-8 -*-

import matplotlib
matplotlib.use('Agg')  # Using Agg backend for non-GUI rendering
import matplotlib.pyplot as plt
import numpy as np

# Define data
z = np.linspace(-10, 10, 400)
w = np.linspace(-10, 10, 400)

# Create 3x3 grid of subplots
fig, axs = plt.subplots(3, 3, figsize=(9, 9), sharex='col', sharey='row')
plt.subplots_adjust(hspace=0, wspace=0)  # Ensure no spacing between subplots

# Overall title
fig.suptitle('Sharing x per column, y per row')

# Populate subplots with specific data
# Row 1
axs[0, 0].plot(z, w, color='blue')
axs[0, 1].plot(z**3, w, color='blue')
axs[0, 2].plot(-z, w + 1, color='yellow')

# Row 2
axs[1, 0].plot(-z**3, w + 2, color='purple')
axs[1, 1].plot(z**2, w**2, color='brown')
axs[1, 2].plot(-z**2, w**2 + 1, color='pink')

# Row 3
axs[2, 0].plot(z**2, -w**2 + 2, color='grey')
axs[2, 1].plot(-z**2, -w**2 + 3, color='black')
axs[2, 2].plot(z, -w, color='white')

# Only outermost subplots should have labels
for ax in axs.flat:
    ax.label_outer()

# Save the plot as a png file
plt.savefig('novice_final.png')