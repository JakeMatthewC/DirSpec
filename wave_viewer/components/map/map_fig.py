import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from data.query import get_buoy_locations

buoy_df = get_buoy_locations()

buoy_df["start_display"] = (
    pd.to_datetime(buoy_df["start_time"], utc=True)
    .dt.strftime("%Y-%m-%d")
)

buoy_df["end_display"] = (
    pd.to_datetime(buoy_df["end_time"], utc=True)
    .dt.strftime("%Y-%m-%d")
    .fillna("Present")
)

fig = px.scatter_map(
    buoy_df,
    lat="lat",
    lon="lon",
    custom_data=[
        "buoy_id",        # 0
        "station_id",     # 1
        "deployment_id",  # 2
        "name",           # 3
        "lat",            # 4
        "lon",            # 5
        "start_display",  # 6
        "end_display",    # 7
        "depth",          # 8
        "project"         # 9
    ],
    zoom=2,
    height=500,
    map_style="carto-positron",
)

fig.update_layout(
    margin=dict(l=0, r=0, t=0, b=0),
    map=dict(
        zoom=2,
        center={"lat": 30, "lon": -70}
    ),
    autosize=True,
    uirevision="constant"
)

fig.update_traces(
    marker=dict(
        size=12,
        color="royalblue"
    ),
    hovertemplate=(
        "<b>%{customdata[3]}</b><br>"
        "Station: %{customdata[1]}<br>"
        "Deployment: %{customdata[2]}<br>"
        "Latitude: %{customdata[4]}<br>"
        "Longitude: %{customdata[5]}<br>"
        "Start: %{customdata[6]}<br>"
        "End: %{customdata[7]}<br>"
        "Depth: %{customdata[8]} m<br>"
        "Project: %{customdata[9]}"
        "<extra></extra>"
    )
)

fig.add_trace(
    go.Scattermap(
        lat=[],
        lon=[],
        mode="markers",
        name="Selected deployment",
        marker=dict(
            size=16,
            color="red"
        ),
        customdata=[],
        hovertemplate=(
            "<b>%{customdata[3]}</b><br>"
            "Station: %{customdata[1]}<br>"
            "Deployment: %{customdata[2]}<br>"
            "Latitude: %{customdata[4]}<br>"
            "Longitude: %{customdata[5]}<br>"
            "Start: %{customdata[6]}<br>"
            "End: %{customdata[7]}<br>"
            "Depth: %{customdata[8]} m<br>"
            "Project: %{customdata[9]}"
            "<extra></extra>"
        ),
        showlegend=False
    )
)