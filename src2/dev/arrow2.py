
import plotly.graph_objects as go

# Define a fixed figure size (in pixels) for consistent coordinate conversion
fig_width = 700
fig_height = 700

# Define the arrow head and tail in paper coordinates.
# Using Plotly's default mapping for ternary plots:
#   Vertex B: (a=0, b=1, c=0) maps to (1, 0) in paper coordinates.
#   Midpoint of side AC: (a=0.5, b=0, c=0.5) maps to (0.25, 0.5) in paper coordinates.
arrow_head = (0.25, 0.5)  # Target: midpoint of side AC
arrow_tail = (1.0, 0.0)   # Source: vertex B

# Compute the pixel offset for the arrow tail relative to the arrow head.
# Offset (in pixels) = (tail_paper_coordinate - head_paper_coordinate) * figure_dimension.
offset_x = (arrow_tail[0] - arrow_head[0]) * fig_width   # Horizontal offset
offset_y = (arrow_tail[1] - arrow_head[1]) * fig_height    # Vertical offset

fig = go.Figure()

# Add scatterternary trace for the vertices for context.
fig.add_trace(go.Scatterternary(
    mode='markers',
    a=[1, 0, 0],
    b=[0, 1, 0],
    c=[0, 0, 1],
    marker=dict(size=10, color='black'),
    name='Vertices'
))

# Optionally, mark the arrow endpoints (the midpoint of AC and vertex B) on the ternary plot.
fig.add_trace(go.Scatterternary(
    mode='markers',
    a=[0, 0.5],
    b=[1, 0],
    c=[0, 0.5],
    marker=dict(size=8, color='blue'),
    name='Arrow Endpoints'
))

# Add an annotation with an arrow.
# The arrow head is placed at (arrow_head) in paper coordinates.
# The arrow tail is given by pixel offsets (ax, ay) relative to the arrow head.
fig.add_annotation(
    x=arrow_head[0], y=arrow_head[1],  # Arrow head in paper coordinates.
    xref="paper", yref="paper",
    ax=offset_x, ay=offset_y,          # Offsets in pixels (default reference is "pixel").
    text="",                         # No text; just the arrow.
    showarrow=True,
    arrowhead=3, arrowsize=1, arrowwidth=2, arrowcolor="red"
)

# Update the layout with ternary settings and the fixed figure size.
fig.update_layout(
    title="Ternary Plot with an Arrow from B to the Midpoint of AC",
    width=fig_width,
    height=fig_height,
    ternary=dict(
        sum=1,
        aaxis=dict(title="A"),
        baxis=dict(title="B"),
        caxis=dict(title="C")
    )
)

# Open the plot in your default browser.
fig.show()
