import numpy as np
import pandas as pd
from pyrolite.plot import pyroplot
from pyrolite.util.plot.transform import xy_to_tlr, tlr_to_xy
import plotly.graph_objects as go
import matplotlib.pyplot as plt

def shift_to_zero(m):
    # Find the minimum values in each column
    min_vals = np.min(m, axis=0)
    
    # Subtract the minimum values from each column to shift the data
    shifted_m = m - min_vals

    return shifted_m

# Assuming 'df' is a pandas DataFrame with your ternary data
df = pd.read_csv('df8.csv')
dfm = df.mean()

# Generate a contour plot using pyrolite and matplotlib
fig, ax = plt.subplots(1, 1, figsize=(8, 8), subplot_kw=dict(projection='ternary'))
cs = df.pyroplot.density(ax=ax, contours=[0.68], fontsize=1, mode='density', cmap='viridis')
for c in cs.collections:
    c.set_label(None)
plt.close(fig)  # Close the plot as we only need the contour data

# Extract the path collections from the matplotlib ContourSet
contour_paths = cs.collections[0].get_paths()
#main_contour_path = shift_to_zero(contour_paths[0].vertices)
main_contour_path = contour_paths[0].vertices
# INSERT HERE
main_contour_path[:, 0] *= 0.866 # Weird scale factor, not sure why it works?
tlr_path = xy_to_tlr(main_contour_path)
tlr_path[:, 1] -= 0.5 # Weird offsets, not sure why needed?
tlr_path[:, 2] += 0.5

A_ternary = tlr_path[:, 0]
B_ternary = tlr_path[:, 1]
C_ternary = tlr_path[:, 2]

# Normalize the coordinates so that they sum to 1
sum_values = A_ternary + B_ternary + C_ternary
A_ternary /= sum_values
B_ternary /= sum_values
C_ternary /= sum_values

# Create the Plotly figure
plotly_fig = go.Figure()

plotly_fig.add_trace(go.Scatterternary({'a': df['A'], 'b': df['B'], 'c': df['C'], 'marker': {'symbol': 'circle', 'color': 'red', 'opacity': 0.2}, 'mode': 'markers'}))
plotly_fig.add_trace(go.Scatterternary({'a': [dfm['A']], 'b': [dfm['B']], 'c': [dfm['C']], 'marker': {'opacity': 1, 'color': 'black'}}))

# Add the contour lines to the Plotly figure
plotly_fig.add_trace(go.Scatterternary({
    'mode': 'lines',
    'a': A_ternary,
    'b': B_ternary,
    'c': C_ternary,
    'line': {'color': 'green', 'width': 2},
}))

# Set the layout for the Plotly figure
plotly_fig.update_layout({
    'ternary': {
        'sum': 1,
        'aaxis': {'title': 'Component A', 'min': 0.01, 'linewidth': 2, 'ticks': 'outside'},
        'baxis': {'title': 'Component B', 'min': 0.01, 'linewidth': 2, 'ticks': 'outside'},
        'caxis': {'title': 'Component C', 'min': 0.01, 'linewidth': 2, 'ticks': 'outside'},
    },
    'title': 'Ternary Plot with Centered Contour Lines',
})

# Show the Plotly figure
plotly_fig.show()

