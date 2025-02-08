# -*- coding: utf-8 -*-
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
import matplotlib

# Use Agg backend for non-GUI rendering
matplotlib.use('Agg')

# Step 2: Generate Correlated Dataset
np.random.seed(0)  # For reproducibility

mean1 = [1, 1]
cov1 = [[0.6, -0.3], [-0.3, 0.25]]
data1 = np.random.multivariate_normal(mean1, cov1, 350)

mean2 = [7, 6]
cov2 = [[0.85, 0.25], [0.25, 0.6]]
data2 = np.random.multivariate_normal(mean2, cov2, 350)

data = np.vstack((data1, data2))

# Step 3: Create the Scatter Plot
fig, ax = plt.subplots(figsize=(6, 6))
ax.scatter(data[:, 0], data[:, 1], s=10, color='b', alpha=0.5, label='Data Points')

# Step 4: Add Vertical and Horizontal Lines
ax.axhline(0, color='grey', lw=1)
ax.axvline(0, color='grey', lw=1)

# Step 5: Overlay Confidence Ellipses
def plot_confidence_ellipse(mean, cov, ax, n_std, facecolor, edgecolor, linestyle, label):
    pearson = cov[0, 1] / np.sqrt(cov[0, 0] * cov[1, 1])
    ellipse_radius_x = np.sqrt(1 + pearson)
    ellipse_radius_y = np.sqrt(1 - pearson)
    
    ellipse = Ellipse((0, 0), width=ellipse_radius_x * n_std * 2, height=ellipse_radius_y * n_std * 2,
                      edgecolor=edgecolor, linestyle=linestyle, facecolor=facecolor, label=label, alpha=0.2)
    
    scale_x = np.sqrt(cov[0, 0]) * n_std
    scale_y = np.sqrt(cov[1, 1]) * n_std
    t = np.arctan2(*np.linalg.eig(cov)[1][:, 0][::-1])
    
    ellipse.set_transform(
        plt.matplotlib.transforms.Affine2D().rotate(t).scale(scale_x, scale_y).translate(mean[0], mean[1]) + ax.transData)
    
    return ax.add_patch(ellipse)

# Adding ellipses
plot_confidence_ellipse(mean1, cov1, ax, n_std=1, facecolor='none', edgecolor='firebrick', linestyle='solid', label='$1\\sigma$')
plot_confidence_ellipse(mean1, cov1, ax, n_std=2, facecolor='none', edgecolor='fuchsia', linestyle='dashed', label='$2\\sigma$')
plot_confidence_ellipse(mean1, cov1, ax, n_std=3, facecolor='none', edgecolor='blue', linestyle='dotted', label='$3\\sigma$')

# Step 6: Highlight a Specific Point
ax.plot(1, 1, 'ro', label='(1,1) point')

# Step 7: Finalize the Plot
ax.set_title('Different standard deviations')
ax.legend(loc='upper right')

# Save the plot to a file
plt.savefig('novice.png')

plt.close(fig)  # Close the figure after saving to release resources