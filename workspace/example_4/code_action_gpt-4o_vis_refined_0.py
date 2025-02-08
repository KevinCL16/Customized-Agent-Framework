# -*- coding: utf-8 -*-

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse

# 1. Set figure size
plt.figure(figsize=(6, 6))

# 2. Generate correlated dataset
np.random.seed(0)

# Use specified correlation parameters and center points
cor1_mean = [1, 1]
cor2_mean = [7, 6]
cov1 = [[0.6, 0.85], [0.85, 1.0]]
cov2 = [[-0.3, 0.25], [0.25, 0.4]]

group1_data = np.random.multivariate_normal(cor1_mean, cov1, 350)
group2_data = np.random.multivariate_normal(cor2_mean, cov2, 350)

combined_data = np.vstack((group1_data, group2_data))

# 3. Scatter plot
plt.scatter(combined_data[:, 0], combined_data[:, 1], alpha=0.5, label='Data Points')

# 4. Vertical and horizontal lines
plt.axhline(y=0, color='grey', linestyle='-')
plt.axvline(x=0, color='grey', linestyle='-')

# 5. Confidence ellipses
def plot_confidence_ellipse(mean, cov_matrix, ax, n_std, facecolor='none', **kwargs):
    eigvals, eigvecs = np.linalg.eigh(cov_matrix)
    order = eigvals.argsort()[::-1]
    eigvals, eigvecs = eigvals[order], eigvecs[:, order]
    theta = np.degrees(np.arctan2(*eigvecs[:, 0][::-1]))
    width, height = 2 * n_std * np.sqrt(eigvals)
    ellipse = Ellipse(xy=mean, width=width, height=height, angle=theta,
                      facecolor=facecolor, **kwargs)
    ax.add_patch(ellipse)
    return ellipse

ax = plt.gca()
plot_confidence_ellipse(cor1_mean, cov1, ax, n_std=1, edgecolor='firebrick', label='$1\sigma$')
plot_confidence_ellipse(cor1_mean, cov1, ax, n_std=2, edgecolor='fuchsia', linestyle='--', label='$2\sigma$')
plot_confidence_ellipse(cor1_mean, cov1, ax, n_std=3, edgecolor='blue', linestyle=':', label='$3\sigma$')

# 6. Highlight specific point
plt.scatter(1, 1, color='red', label='(1, 1) point')

# 7. Title and legend
plt.title('Different standard deviations')
plt.legend()

# 8. Display and save plot
plt.savefig('novice_final.png')
plt.show()