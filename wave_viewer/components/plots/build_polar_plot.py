import plotly.graph_objects as go
from scipy.ndimage import gaussian_filter1d

def build_polar_plot(df,freq_bin):
    # rolling smoothing of D
    df["dir_smooth"] = gaussian_filter1d(df["spreading"], sigma=2)

    # get the max value so that the plot can be sized
    max_val = df['dir_smooth'].max()
    radial_limit = max_val*1.1

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r = df['spreading'],
        theta = df['direction'],
        mode = "lines",
        line = dict(color="royalblue", width=2),
        name = f"S(f={freq_bin:.3f})",
    ))

    fig.update_layout(
        title=f"Directional Distribution for f = {freq_bin:.3f} Hz",
        polar = dict(
            angularaxis= dict(
                direction="clockwise", 
                rotation=90,
                tickmode='array',
                tickvals=[0,30,60,90,120,150,180,210,240,270,300,330],
                ticktext=['0','30','60','90','120','150','180','210','240','270','300','330']
            ),
            radialaxis = dict(
                showticklabels=True,
                angle = 90,
                tickangle=90,
                tickfont=dict(size=10, color='gray'),
                ticks='outside',
                showline=False,
                showgrid=True,
                gridcolor='lightgray',
                gridwidth=0.5,
                range = [0, radial_limit],
            ),

        ),
        showlegend = False,
        margin = {"l": 30, "r": 30, "t":40, "b": 30}
    )
    return fig