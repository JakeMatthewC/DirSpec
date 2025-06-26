import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def build_spec_plot(df,selected_freq):
    fig = make_subplots(rows=3, cols=1, 
        shared_xaxes=True, 
        subplot_titles=("Spectral Energy Density", "Directional Mean (α₁, α₂)", "Directional Spread (r₁, r₂)"),
        row_heights=[1,1,1])

    fig.update_layout(
        margin=dict(t=30,b=30,l=50,r=20),
        height=300)

    # add energy density
    fig.add_trace(go.Scatter(x=df["frequency"], y=df["energy_density"], mode='lines+markers', name='Ef', line=dict(color='royalblue')), row=1, col=1)

    # 2. α₁, α₂ vs Frequency
    fig.add_trace(go.Scatter(x=df["frequency"], y=np.rad2deg(df["alpha1"]), mode='lines+markers', name='α₁', line=dict(color='orange')), row=2, col=1)
    fig.add_trace(go.Scatter(x=df["frequency"], y=np.rad2deg(df["alpha2"]), mode='lines+markers', name='α₂', line=dict(color='green')), row=2, col=1)

    # 3. r₁, r₂ vs Frequency
    fig.add_trace(go.Scatter(x=df["frequency"], y=df["r1"], mode='lines+markers', name='r₁', line=dict(color='red')), row=3, col=1)
    fig.add_trace(go.Scatter(x=df["frequency"], y=df["r2"], mode='lines+markers', name='r₂', line=dict(color='purple')), row=3, col=1)

    # Axis labels
    fig.update_xaxes(title_text="Frequency (Hz)", row=3, col=1)
    fig.update_yaxes(title_text="Ef (m²/Hz)", row=1, col=1, automargin=False)
    fig.update_yaxes(title_text="α values", row=2, col=1, automargin=False)
    fig.update_yaxes(title_text="r values", row=3, col=1, automargin=False)

    if selected_freq:
        fig.add_shape(
            type="line",
            x0=selected_freq,
            x1=selected_freq,
            y0=0,
            y1=1,
            line=dict(color="red", dash="dash"),
            xref="x",
            yref="paper",
            layer="above"
                )
    return fig