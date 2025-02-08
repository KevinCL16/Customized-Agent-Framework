import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
import matplotlib.transforms as transforms
import matplotlib

# Set the matplotlib backend to avoid issues with certain environments
matplotlib.use('Agg')

# Set the figure size
plt.figure(figsize=(6, 6))

# Generate correlated data
np.random.seed(0)
mean1 = [1, 1]
mean2 = [7, 6]
cov1 = [[1, 0.75], [0.75, 1]]  # Correlation ~0.75
cov2 = [[1, -0.2], [-0.2, 1]]  # Correlation ~-0.2

data1 = np.random.multivariate_normal(mean1, cov1, 350)
data2 = np.random.multivariate_normal(mean2, cov2, 350)
data = np.vstack((data1, data2))

# Create scatter plot
plt.scatter(data[:, 0], data[:, 1], alpha=0.5)

# Add vertical and horizontal lines at the mean of the data
mean_data = np.mean(data, axis=0)
plt.axhline(y=mean_data[1], color='grey', linestyle='--')
plt.axvline(x=mean_data[0], color='grey', linestyle='--')

# Function to draw confidence ellipses
def confidence_ellipse(mean, cov, ax, n_std=1.0, facecolor='none', **kwargs):
    pearson = cov[0, 1] / np.sqrt(cov[0, 0] * cov[1, 1])
    ell_radius_x = np.sqrt(1 + pearson)
    ell_radius_y = np.sqrt(1 - pearson)
    ellipse = Ellipse((0, 0), width=ell_radius_x * 2, height=ell_radius_y * 2, facecolor=facecolor, **kwargs)
    scale_x = np.sqrt(cov[0, 0]) * n_std
    scale_y = np.sqrt(cov[1, 1]) * n_std
    transf = transforms.Affine2D().rotate_deg(45).scale(scale_x, scale_y).translate(mean[0], mean[1])
    ellipse.set_transform(transf + ax.transData)
    return ax.add_patch(ellipse)

# Overlay confidence ellipses
ax = plt.gca()
confidence_ellipse(mean_data, np.cov(data, rowvar=False), ax, n_std=1, edgecolor='firebrick', label='$1\sigma$')
confidence_ellipse(mean_data, np.cov(data, rowvar=False), ax, n_std=2, edgecolor='fuchsia', linestyle='--', label='$2\sigma$')
confidence_ellipse(mean_data, np.cov(data, rowvar=False), ax, n_std=3, edgecolor='blue', linestyle=':', label='$3\sigma$')

# Highlight specific point
plt.scatter(1, 1, color='red', label='Point (1, 1)')

# Add title and legend
plt.title('Different standard deviations')
plt.legend()

# Save the plot
plt.savefig("novice_final.png")

# Note: Use plt.show() only if running in an interactive environment, not needed for saving files with 'Agg' backend