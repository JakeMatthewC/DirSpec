import numpy as np
import plotly.graph_objects as go

# 5-degree bins run 0..355, so the curve has to be closed by hand or plotly
# leaves a wedge-shaped gap at north between the last bin and the first.
_CARDINALS = {0: "N", 45: "NE", 90: "E", 135: "SE",
              180: "S", 225: "SW", 270: "W", 315: "NW"}


def build_polar_plot(df, freq_bin, alpha1=None, energy_density=None):
    """Polar plot of the directional spreading D(theta) for one frequency bin.

    df             : columns 'direction' (meteorological degrees, waves FROM) and
                     'spreading' (D, units 1/radian)
    freq_bin       : bin centre frequency in Hz, used for the title
    alpha1         : optional mean wave direction for this bin, met degrees;
                     drawn as a reference spoke
    energy_density : optional E(f) in m^2/Hz, shown as context so it is obvious
                     whether this bin carries meaningful energy
    """
    d = df.dropna(subset=["spreading"]).sort_values("direction")
    theta = d["direction"].to_numpy(dtype=float)
    r = d["spreading"].to_numpy(dtype=float)

    if len(r) == 0:
        return go.Figure()

    # close the loop back to the first bin
    theta_closed = np.append(theta, theta[0] + 360.0)
    r_closed = np.append(r, r[0])

    max_val = float(np.nanmax(r))
    radial_limit = max_val * 1.15 if max_val > 0 else 1.0

    fig = go.Figure()

    # filled lobe reads far better than a bare outline
    fig.add_trace(go.Scatterpolar(
        r=r_closed,
        theta=theta_closed,
        mode="lines",
        line=dict(color="royalblue", width=2.5, shape="spline", smoothing=0.6),
        fill="toself",
        fillcolor="rgba(65,105,225,0.25)",
        name="D(θ)",
        hovertemplate="from %{theta:.0f}°<br>D = %{r:.4f} rad⁻¹<extra></extra>",
    ))

    # mean direction for this bin, as a spoke
    if alpha1 is not None and np.isfinite(alpha1):
        fig.add_trace(go.Scatterpolar(
            r=[0, radial_limit],
            theta=[float(alpha1), float(alpha1)],
            mode="lines",
            line=dict(color="crimson", width=1.5, dash="dash"),
            name="α₁",
            hovertemplate=f"α₁ = {float(alpha1):.0f}° (from)<extra></extra>",
        ))

    # Subtitle goes in the title as a second line rather than a separate
    # annotation: an annotation pinned at y=1.0 sits in the same band as the
    # title and the two collided.
    period = (1.0 / freq_bin) if freq_bin else float("nan")
    sub = "compass bearing waves arrive <b>from</b>"
    if energy_density is not None and np.isfinite(energy_density):
        sub += f"  ·  E(f) = {float(energy_density):.3g} m²/Hz"
    title = (f"Directional spreading · f = {freq_bin:.3f} Hz (T = {period:.1f} s)"
             f"<br><span style='font-size:10px;color:gray'>{sub}</span>")

    tickvals = list(range(0, 360, 45))
    fig.update_layout(
        title=dict(text=title, x=0.5, xanchor="center", y=0.96, yanchor="top",
                   font=dict(size=13)),
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            angularaxis=dict(
                direction="clockwise",
                rotation=90,
                tickmode="array",
                tickvals=tickvals,
                # names only. The two-line "N" over "0°" form was tall enough to
                # run into the ring and the radial labels; exact bearings are on
                # hover, so the degrees were costing more than they gave.
                ticktext=[_CARDINALS[t] for t in tickvals],
                tickfont=dict(size=11),
                gridcolor="rgba(0,0,0,0.12)",
                linecolor="rgba(0,0,0,0.25)",
            ),
            radialaxis=dict(
                showticklabels=True,
                # 22.5 deg puts the radial scale in the gap between the N and NE
                # spokes. It was at 90, i.e. lying directly along north, straight
                # through the "N" label -- that was the overlap.
                angle=22.5,
                tickangle=0,
                nticks=3,
                tickfont=dict(size=9, color="gray"),
                ticks="",
                showline=False,
                showgrid=True,
                gridcolor="rgba(0,0,0,0.10)",
                gridwidth=0.5,
                range=[0, radial_limit],
            ),
        ),
        showlegend=False,
        margin={"l": 45, "r": 45, "t": 72, "b": 45},
    )
    return fig
