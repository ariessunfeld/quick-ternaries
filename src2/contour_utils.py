from typing import List

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde

def transform_to_cartesian(
        df: pd.DataFrame, 
        colA: str, 
        colB: str, 
        colC: str) -> np.array:
    """Transform ternary (A, B, C) data into 2D Cartesian coordinates for plotting and KDE."""
    # Normalization might not be needed if df is already normalized
    total = df.sum(axis=1)
    A = df[colA] / total
    B = df[colB] / total
    C = df[colC] / total
    x = 0.5 * (2*B + C) / (A + B + C)
    y = (np.sqrt(3)/2) * C / (A + B + C)
    return np.vstack([x, y]).T

def compute_kde_contours(
        data: np.array, 
        levels: List[float]=[0.68], 
        grid_points: int=400):
    """Compute KDE on 2D data and determine contour lines for specific data coverage levels."""
    kde = gaussian_kde(data.T)
    default_bandwith = kde.factor
    kde.set_bandwidth(default_bandwith*2)
    # Define a dense grid for evaluation
    x = np.linspace(data[:, 0].min(), data[:, 0].max(), grid_points)
    y = np.linspace(data[:, 1].min(), data[:, 1].max(), grid_points)
    X, Y = np.meshgrid(x, y)
    Z = kde(np.vstack([X.ravel(), Y.ravel()]))
    Z = Z.reshape(X.shape)

    # Calculate the threshold density levels to capture the specified proportions of the data
    total_kde_volume = Z.sum()  # Total sum of KDE evaluations over the grid
    sorted_Z = np.sort(Z.ravel())[::-1]  # Sort densities in descending order
    cumulative_Z = np.cumsum(sorted_Z)
    
    # Convert levels to capture the densest regions first
    density_levels = []
    try:
        for level in levels:
            target_volume = level * total_kde_volume
            idx = np.argmax(cumulative_Z >= target_volume)
            density_levels.append(sorted_Z[idx] if idx < len(sorted_Z) else sorted_Z[-1])
    except TypeError:
        return False, []

    fig, ax = plt.subplots()
    CS = ax.contour(X, Y, Z, levels=sorted(density_levels))
    plt.close(fig)

    # Check if contours are generated and are sufficiently smooth
    min_segment_length = 12  # Minimum number of points in a valid contour segment
    valid_contours = []
    for segs in CS.allsegs:
        if any(len(seg) >= min_segment_length for seg in segs):
            valid_contours.append(segs)

    # Return True if valid contours are found, False otherwise
    success = len(valid_contours) == len(levels)
    return success, valid_contours

    #return CS.allsegs  # Returns all contour segments for each requested level

def convert_contour_to_ternary(contour: List[np.array]):
    """Convert 2D contour coordinates back to ternary coordinates."""
    # Assume contour is a list of arrays; convert each contour segment
    ternary_contours = []
    for _ in contour:
        for path in _:
            x, y = path[:, 0], path[:, 1]
            C = 2 * y / np.sqrt(3)
            B = x - 0.5 * C
            A = 1 - B - C
            ternary_contours.append(np.vstack([A, B, C]).T)
    return ternary_contours