import plotly.graph_objects as go

fig_width = 600
fig_height = 600

# Hard-code the figure size so that pixel offsets remain consistent
fig = go.Figure()
fig.update_layout(
    width=fig_width,
    height=fig_height,
    margin=dict(l=0, r=0, t=40, b=0),  # minimal margins
    ternary=dict(
        domain=dict(x=[0,1], y=[0,1]),
        sum=1,
        aaxis=dict(title="A"),
        baxis=dict(title="B"),
        caxis=dict(title="C")
    ),
    title="Static Annotation Arrow (Paper + Pixel Offsets)"
)

# Draw some reference points so we can see the triangle
fig.add_trace(go.Scatterternary(
    mode='markers',
    a=[1, 0, 0],
    b=[0, 1, 0],
    c=[0, 0, 1],
    marker=dict(size=8, color='black'),
    name='Apexes'
))

# Suppose (through trial & error) that B is near (0.92, 0.07) in "paper" coordinates,
# and the midpoint of A–C is near (0.28, 0.53). 
# You *must* tweak these guesses to match how Plotly actually draws the triangle!
# Then we convert the difference into pixel offsets for ax, ay.

arrow_head_paper = (0.75, 0.5)   # "Tip" (midpoint of AC)
arrow_tail_paper = (0.0, 0.935)   # "Base" (B)

dx = arrow_tail_paper[0] - arrow_head_paper[0]
dy = arrow_tail_paper[1] - arrow_head_paper[1]

offset_x = dx * fig_width   # horizontal offset in pixels
offset_y = dy * fig_height  # vertical offset in pixels

fig.add_annotation(
    x=arrow_head_paper[0], y=arrow_head_paper[1],
    xref="paper", yref="paper",
    ax=offset_x, ay=offset_y,   # tail is pixel offset from tip
    text="",
    showarrow=True,
    arrowhead=3,
    arrowwidth=2,
    arrowcolor="red"
)

fig.show()
