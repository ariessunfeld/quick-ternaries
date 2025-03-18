import plotly.graph_objects as go

# Create the ternary figure
fig = go.Figure()

# Add a scatterternary trace to draw the line and mark the endpoints
fig.add_trace(go.Scatterternary(
    mode='lines+markers',
    a=[0, 0.5],
    b=[1, 0],
    c=[0, 0.5],
    marker=dict(size=8, color='red'),
    line=dict(width=2, color='blue'),
    name='Line'
))

# Update layout settings for the ternary plot
fig.update_layout(
    title="Line on Ternary Plot: Lower Right Apex to Midpoint of Left-Top Tie Line",
    ternary=dict(
        sum=1,
        aaxis=dict(title="A"),
        baxis=dict(title="B"),
        caxis=dict(title="C")
    )
)

# Display the plot in the browser
fig.show()
