import plotly.graph_objects as go

fig = go.Figure(data=[go.Scatterternary({
    'mode': 'markers',
    'a': [0.2, 0.1, 0.3],
    'b': [0.4, 0.2, 0.5],
    'c': [0.4, 0.7, 0.2],
    'marker': {'size': 12}
})])

fig.update_layout(
    ternary={
        'aaxis': {'title': 'Component A'},
        'baxis': {'title': 'Component B'},
        'caxis': {'title': 'Component C'}
    },
    annotations=[
        go.layout.Annotation(
            x=0.2,  # x-coordinate of the arrow's end
            y=0.4,  # y-coordinate of the arrow's end
            xref="paper",
            yref="paper",
            text="",  
            showarrow=True,
            ax=0.1,  # x-coordinate of the arrow's start
            ay=0.2,  # y-coordinate of the arrow's start
            axref="paper",
            ayref="paper",
            arrowhead=3,
            arrowwidth=1,
            arrowcolor="black"
        )
    ]
)

fig.show()