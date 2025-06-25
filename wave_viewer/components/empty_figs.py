import plotly.graph_objects as go

# create empty placeholder figures
empty_fig = go.Figure()
empty_fig.update_layout(
    xaxis=dict(visible=False),
    yaxis=dict(visible=False),
    annotations=[dict(text="Click a buoy to see data.", showarrow=False, font=dict(size=16))],
    plot_bgcolor='white'
)

empty_fig_spec = go.Figure()
empty_fig_spec.update_layout(
    xaxis=dict(visible=False),
    yaxis=dict(visible=False),
    annotations=[dict(text="Click a buoy and frequency bin to see data.", showarrow=False, font=dict(size=16))],
    plot_bgcolor='white'
)