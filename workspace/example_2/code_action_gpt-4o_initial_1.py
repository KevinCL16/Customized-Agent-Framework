import matplotlib
matplotlib.use('Agg')  # Use a non-interactive backend
import matplotlib.pyplot as plt
import numpy as np

# Create a range of values for z and w
z = np.linspace(-10, 10, 100)
w = np.linspace(-10, 10, 100)

# Create the figure and 3x3 subplots
fig, axs = plt.subplots(3, 3, figsize=(10, 10), sharex='col', sharey='row')
fig.subplots_adjust(wspace=0, hspace=0)
fig.suptitle('Sharing x per column, y per row')

# Plot the data on each subplot with specified colors

# Top row
axs[0, 0].plot(z, w, color='red')
axs[0, 1].plot(z, z**3, color='blue')
axs[0, 2].plot(-z, w + 1, color='yellow')

# Middle row
axs[1, 0].plot(-z**3, w + 2, color='purple')
axs[1, 1].plot(z**2, w**2, color='brown')
axs[1, 2].plot(-z**2, w**2 + 1, color='pink')

# Bottom row
axs[2, 0].plot(z**2, -w**2 + 2, color='grey')
axs[2, 1].plot(-z**2, -w**2 + 3, color='black')
axs[2, 2].plot(z, -w, color='white')

# Label only the outermost subplots
for ax in axs.flat:
    ax.label_outer()

# Save the plot to a file
plt.savefig("novice.png")

# Display the plot
plt.show()