import numpy as np
import pandas as pd
from pyrolite.plot import pyroplot
from pyrolite.util.plot.transform import xy_to_tlr, tlr_to_xy
import plotly.graph_objects as go
import matplotlib.pyplot as plt

def add_ternary_gridlines(ax, major_step=10, minor_step=5, major_color='k', minor_color='gray'):
    """
    Adds gridlines across all three axes of a ternary plot.

    Parameters:
        ax: The ternary subplot axis to add gridlines to.
        major_step: Step size for major gridlines as a percentage.
        minor_step: Step size for minor gridlines as a percentage.
        major_color: Color of the major gridlines.
        minor_color: Color of the minor gridlines.
    """
    # Define a function to draw lines between two points in ternary coordinates
    def draw_line(ax, start, end, **line_kwargs):
        # Convert ternary coordinates (total must equal 100) to plot coordinates
        ax.plot(*np.array([start, end]).T, **line_kwargs)

    # Generate major and minor gridlines
    for step, color, linestyle in [(major_step, major_color, '-'), (minor_step, minor_color, ':')]:
        for i in range(0, 101, step):
            # Ensure lines are only drawn within the ternary plot
            if i != 100:
                # Lines parallel to AB
                draw_line(ax, [i, 0, 100-i], [0, i, 100-i], color=color, linestyle=linestyle)
                # Lines parallel to AC
                draw_line(ax, [i, 100-i, 0], [0, 100-i, i], color=color, linestyle=linestyle)
                # Lines parallel to BC
                draw_line(ax, [100-i, i, 0], [100-i, 0, i], color=color, linestyle=linestyle)


df = pd.read_csv('Harrison2.csv')
dfm = df.mean()
fig, ax = plt.subplots(1, 1, figsize=(8, 8), subplot_kw=dict(projection='ternary'))
cs = df.pyroplot.density(ax=ax, contours=[0.68], fontsize=1, mode='density', cmap='viridis', label_contours=False, bins=100)
for c in cs.collections:
    c.set_label(None)

add_ternary_gridlines(ax)

plt.savefig('output_with_gridlines.png')
plt.close(fig)  

# Extract the path collections from the matplotlib ContourSet
contour_paths = cs.collections[0].get_paths()
main_contour_path = contour_paths[0].vertices
main_contour_path[:, 0] *= 0.866 # Weird scale factor, not sure why it works?
tlr_path = xy_to_tlr(main_contour_path)
tlr_path[:, 1] -= 0.5 # Weird offsets, not sure why needed?
tlr_path[:, 2] += 0.5

A_ternary = tlr_path[:, 0]
B_ternary = tlr_path[:, 1]
C_ternary = tlr_path[:, 2]

sum_values = A_ternary + B_ternary + C_ternary
A_ternary /= sum_values
B_ternary /= sum_values
C_ternary /= sum_values

# Create the Plotly figure
plotly_fig = go.Figure()

plotly_fig.add_trace(go.Scatterternary({'a': df['A'], 'b': df['B'], 'c': df['C'], 'marker': {'symbol': 'circle', 'color': 'red', 'opacity': 0.02}, 'mode': 'markers'}))
plotly_fig.add_trace(go.Scatterternary({'a': [dfm['A']], 'b': [dfm['B']], 'c': [dfm['C']], 'marker': {'opacity': 1, 'color': 'black'}}))

plotly_fig.add_trace(go.Scatterternary({
    'mode': 'lines',
    'a': A_ternary,
    'b': B_ternary,
    'c': C_ternary,
    'line': {'color': 'green', 'width': 2},
}))

tickinfo = {'ticks': 'inside', 'tickmode': 'linear', 'tick0': 0, 'dtick': 0.1}
#tickinfo = {'ticks': 'outside', 'tickmode': 'array', 'tickvals': [0.05* x for x in range(21)], 'ticktext': [f'{y:.2}' if idx%2 == 0 else '' for idx, y in enumerate([0.05* x for x in range(21)])]}
plotly_fig.update_layout({
    'ternary': {
        'sum': 1,
        'aaxis': {'title': 'Component A', 'min': 0.00, 'linewidth': 2} | tickinfo,
        'baxis': {'title': 'Component B', 'min': 0.00, 'linewidth': 2} | tickinfo,
        'caxis': {'title': 'Component C', 'min': 0.00, 'linewidth': 2} | tickinfo,
    },
    'title': 'Ternary Plot with Centered Contour Lines',
})

plotly_fig.show()

