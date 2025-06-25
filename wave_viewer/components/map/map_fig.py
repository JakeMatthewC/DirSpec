import plotly.express as px
from data.query import get_buoy_locations

buoy_df = get_buoy_locations()

fig = px.scatter_map(
    buoy_df,
    lat="lat",
    lon="lon",
    hover_name="name",
    hover_data=["station_id"],
    zoom=2,
    height=50,
    map_style="carto-positron",
)

# Set the map style and access token
fig.update_layout(
                margin=dict(l=0, r= 0, t=0, b=0),
                mapbox_style = "open-street-map",
                mapbox_zoom = 2,
                mapbox_center = {"lat": 30, "lon": -70},
                autosize = True,
                uirevision = 'constant')
fig.update_traces(marker=dict(size=12, color="royalblue"))