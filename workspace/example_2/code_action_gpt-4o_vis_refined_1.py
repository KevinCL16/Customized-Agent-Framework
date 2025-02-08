import matplotlib
matplotlib.use('Agg')  # Use the Agg backend for non-interactive plotting
import matplotlib.pyplot as plt
import numpy as np

# Sample data for the plots
z = np.linspace(-10, 10, 400)
w = np.linspace(-10, 10, 400)

# Set up a 3x3 grid with shared x and y axes
fig, axs = plt.subplots(3, 3, figsize=(10, 10), sharex='col', sharey='row')

# Remove the space between the plots
plt.subplots_adjust(wspace=0, hspace=0)

# Plot each specified equation in the grid with the correct color
axs[0, 0].plot(z, w, 'r')  # red
axs[0, 1].plot(z**3, w, 'b')  # blue
axs[0, 2].plot(-z, w + 1, 'y')  # yellow
axs[1, 0].plot(-z**3, w + 2, 'purple')  # purple
axs[1, 1].plot(z**2, w**2, 'brown')  # brown
axs[1, 2].plot(-z**2, w**2 + 1, 'pink')  # pink
axs[2, 0].plot(z**2, -w**2 + 2, 'grey')  # grey
axs[2, 1].plot(-z**2, -w**2 + 3, 'k')  # black
axs[2, 2].plot(z, -w, 'w')  # white

# Set the title of the figure
fig.suptitle('Sharing x per column, y per row')

# Disable axis labels for the inner plots
for i, ax in enumerate(axs.flat):
    if i % 3 != 0:  # not the first column's y-axis
        ax.yaxis.set_tick_params(labelleft=False)
    if i // 3 != 2:  # not the last row's x-axis
        ax.xaxis.set_tick_params(labelbottom=False)

# Save the figure to a png file
plt.savefig('novice_final.png')
plt.show()