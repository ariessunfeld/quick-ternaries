import plotly.graph_objects as go

# Create a ternary plot figure
fig = go.Figure()

# For context, plot the three vertices of the ternary triangle.
# Using Plotly's convention:
#   A: (a=1, b=0, c=0) → (0, 0) in paper coordinates
#   B: (a=0, b=1, c=0) → (1, 0)
#   C: (a=0, b=0, c=1) → (0.5, 1)
fig.add_trace(go.Scatterternary(
    mode='markers',
    a=[1, 0, 0],
    b=[0, 1, 0],
    c=[0, 0, 1],
    marker=dict(size=10, color='black'),
    name='Vertices'
))

# Optionally, add a scatterternary trace for the arrow endpoints.
# Here we mark the start (B) and the target (midpoint of A-C)
fig.add_trace(go.Scatterternary(
    mode='markers',
    a=[0, 0.5],
    b=[1, 0],
    c=[0, 0.5],
    marker=dict(size=8, color='blue'),
    name='Arrow Endpoints'
))

# In Plotly's default ternary subplot, the triangle is drawn with vertices:
#   A: (0,0), B: (1,0), and C: (0.5,1) in the paper coordinate system.
# We want an arrow from B (1,0) to the midpoint of AC: ((0+0.5)/2, (0+1)/2) = (0.25,0.5)
# Add an annotation with an arrow:
fig.add_annotation(
    x=0.25, y=0.5,       # Arrow tip (midpoint of side AC)
    ax=1, ay=0,          # Arrow tail (vertex B)
    xref="paper", yref="paper",
    axref="paper", ayref="paper",
    text="",             # No text displayed; only the arrow is drawn
    showarrow=True,
    arrowhead=3,         # Style of the arrow head
    arrowsize=1,
    arrowwidth=2,
    arrowcolor="red"
)

# Update the layout with a title and ternary axis labels.
fig.update_layout(
    title="Ternary Plot with an Arrow from B to Midpoint of AC",
    ternary=dict(
        sum=1,
        aaxis=dict(title="A"),
        baxis=dict(title="B"),
        caxis=dict(title="C")
    )
)

# Open the plot in your browser.
fig.show()
