
import plotly.graph_objects as go

# Ternary coordinates:
#   - Vertex B: (a=0, b=1, c=0)
#   - Midpoint of side A–C: (a=0.5, b=0, c=0.5)

fig = go.Figure()

# Draw the line from B to midpoint(AC)
fig.add_trace(go.Scatterternary(
    a=[0.05, 0.45],
    b=[0.95, 0.05],
    c=[0.05, 0.45],
    mode='lines',
    line=dict(width=3, color='red'),
    showlegend=False
))

# Place a “triangle” marker at the endpoint
# (Will appear as a triangle pointing up in screen space, not necessarily
# oriented along the line. You can try 'triangle-left', 'arrow-up', etc.)
fig.add_trace(go.Scatterternary(
    a=[0.45],
    b=[0.05],
    c=[0.45],
    mode='markers',
    marker=dict(
        symbol='triangle-up',  # or 'triangle-left', 'arrow-up', etc.
        size=12,
        color='red'
    ),
    showlegend=False
))

# Basic ternary layout
fig.update_layout(
    width=600,
    height=600,
    title="Line + 'Arrowhead' Marker in Ternary",
    ternary=dict(
        sum=1,
        aaxis=dict(title="A"),
        baxis=dict(title="B"),
        caxis=dict(title="C"),
        domain=dict(x=[0, 1], y=[0, 1])  # occupy entire figure
    )
)

fig.show()
