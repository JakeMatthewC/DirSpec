import dash
from dash import dcc, html, Output, Input, State
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import psycopg2
from scipy.interpolate import interp1d
from sqlalchemy import create_engine, text

# Connect to your PostgreSQL DB
def get_buoy_locations():
    conn = psycopg2.connect(
        dbname="postgres",
        user="Jacob",
        password="",
        host="localhost",
        port="5432")
    df = pd.read_sql("""
        SELECT b.station_id, b.name, b.lat, b.lon
        FROM buoys b
        JOIN time_steps ts ON ts.buoy_id = b.id
        JOIN spectra_parameters sp ON sp.time_step_id = ts.id
        GROUP BY b.station_id, b.name, b.lat, b.lon;
    """, conn)
    conn.close()
    return df

engine = create_engine("postgresql+psycopg2://Jacob:@localhost:5432/postgres")

# Initialize Dash app
app = dash.Dash(__name__)
app.title = "Wave Spectral Dashboard"

# Load buoy data
buoy_df = get_buoy_locations()

# Create a map plot using Plotly
fig = px.scatter_map(
    buoy_df,
    lat="lat",
    lon="lon",
    hover_name="name",
    hover_data=["station_id"],
    zoom=2,
    height=500
)

# Set the map style and access token
fig.update_layout(
                mapbox_style = "open-street-map",
                mapbox_zoom = 2,
                mapbox_center = {"lat": 30, "lon": -70},
                autosize = True,
                uirevision = 'constant'
)
fig.update_traces(marker=dict(size=12, color="royalblue"))

# app layout structure
app.layout = html.Div(style={"height": "90vh", "display": "flex", "flexDirection": "column", "margin": 0, "padding": 0}, children=[
    
    # Top: Map section
    html.Div(style={"flex": "2", "minHeight": "0px"}, children=[
        #html.H2("Wave Buoy Map", style={"margin": "10px"}),
        dcc.Graph(id="buoy-map", figure=fig, style={"height": "100%", "width": "100%"}, config={"displayModeBar": False}),
        dcc.Store(id="stored-buoy"),
        dcc.Store(id="stored-timestep")
    ]),

    # Bottom: Docked spectral + polar plots
    html.Div(style={
        "flex": "1",
        "borderTop": "1px solid #ccc",
        "padding": "5px",
        "backgroundColor": "#f9f9f9",
        "minHeight": "0"
    }, children=[
        html.Div(id="selected-buoy", style={"fontWeight": "bold", "marginBottom": "10px"}),
        html.Label("Select Timestep:"),
        dcc.Dropdown(id="timestep-dropdown", placeholder="Choose a timestamp", options=[]),
        
        html.Div(style={"display": "flex", "justifyContent": "space-between", "height": "100%"}, children=[
            dcc.Graph(id="spectrum-plot", style={"width": "65%", "height": "100%"}),
            dcc.Graph(id="polar-plot", style={"width": "30%", "height": "100%"})
        ])
    ])
])

CONN_STR = "postgresql+psycopg2://Jacob:@localhost:5432/postgres"

# create the dropdown for timestep selection and store selected buoy
@app.callback(
    Output("timestep-dropdown", "options"),
    Output("timestep-dropdown", "value"),
    Output("stored-buoy", "data"),
    Output("selected-buoy", "children"),
    Input("buoy-map", "clickData")
)
def update_timestep_dropdown(clickData):
    if not clickData:
        return {}, None, None, None
    
    station_id = clickData["points"][0]["customdata"][0]

    engine = create_engine(CONN_STR)
    with engine.connect() as conn:
        results = conn.execute(
            text("""
            SELECT ts.id, ts.timestamp
            FROM time_steps ts
            JOIN buoys b ON ts.buoy_id = b.id
            WHERE b.station_id = :station_id
            ORDER BY ts.timestamp DESC
            """), {"station_id": station_id}
        ).fetchall()

        sta_id_label = f"Selected station: {station_id}"

        options = [{"label": str(row[1].strftime("%Y-%m-%d %H:%M UTC")), "value": row[0]} for row in results]
        default_value = options[0]["value"] if options else None
        return options, default_value, station_id, sta_id_label

# this is to store the selected timestep into stored-timestep for grabbing spec data
@app.callback(
    Output("stored-timestep", "data"),
    Input("timestep-dropdown", "value")
)
def store_selected_timestep(timestep_id):
    return timestep_id

# callback to create the spectrum plot in bottom left pane after clicking a buoy and selecting a timestep
@app.callback(
    Output("spectrum-plot", "figure"),
    Input("stored-timestep", "data"),
    Input("stored-buoy", "data"),
    prevent_initial_call=True
)
def update_spectrum_plot(timestep_id, selected_buoy):
    station_id = selected_buoy
    # Connect to postgres
    engine = create_engine(CONN_STR)
    conn = engine.connect()

    # Now get spectrum for this time_step
    df = pd.read_sql(text("""
        SELECT frequency, energy_density
        FROM spectra_parameters
        WHERE time_step_id = :timestep_id
        ORDER BY frequency
    """), conn, params={"timestep_id": timestep_id})

    # fetch timestamp for plot titles
    if df.empty == False:
        timestamp = pd.read_sql(
            text("SELECT timestamp FROM time_steps WHERE id = :id"),
            conn,params={"id": timestep_id})["timestamp"].iloc[0]

        # Create bar plot for spectrum
        fig = {
            "data": [{
                "type": "bar",
                "x": df["frequency"],
                "y": df["energy_density"],
                "marker": {"color": "#4f81bd"},
                "name": "E(f)"
            }],
            "layout": {
                "title": f"Energy Spectrum for {station_id} ({timestamp.strftime('%Y-%m-%d %H:%M')}))",
                "xaxis": {"title": "Frequency [Hz]"},
                "yaxis": {"title": "Energy Density"},
                "height": 300,
                "margin": {"l": 60, "r": 30, "t": 40, "b": 50}
            }
    }

        return fig

@app.callback(
    Output("polar-plot","figure"),
    Input("spectrum-plot","clickData"),
    Input("stored-timestep", "data")
)
def update_polar_plot(clickData, time_step_id):
    # handle nonclicks and no timesteps available
    if not clickData or time_step_id is None:
        return {}
    
    # extract frequency bin from click
    freq_bin = clickData["points"][0]["x"]

    # pull spectral data from postgres
    engine = create_engine(CONN_STR)
    with engine.connect() as conn:
        df = pd.read_sql(
            text("""
            SELECT 
                d.direction,
                d.spreading,
                p.energy_density
            FROM spectra_directional d
            JOIN spectra_parameters p
                ON d.time_step_id = p.time_step_id
                AND d.frequency = p.frequency
            WHERE d.time_step_id = :ts
            AND d.frequency = :f
            ORDER BY d.direction             
        """), conn, params={"ts": time_step_id, "f": freq_bin})

    # handle no return from postgres
    if df.empty:
        return {}
    
    # rolling smoothing of D
    df["dir_smooth"] = df["spreading"].rolling(window=3, center=True, min_periods=1).mean()
    
    # build S = D * E(f) for the selected frequency
    E = df["energy_density"].iloc[0]
    df["S_raw"] = df["spreading"] * E
    df["S_smooth"] = df["dir_smooth"] * E

    # interpolate to 1 degree resolution
    fine_theta = np.arange(0, 360, 1)
    interp_func = interp1d(df["direction"], df["S_smooth"], kind="linear", fill_value="extrapolate")
    S_interp = interp_func(fine_theta)

    #np.savetxt(r"D:\DirSpec\data\log.txt",df.values)

    # create the figure
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r = S_interp,
        theta = fine_theta,
        mode = "lines",
        line = dict(color="royalblue", width=2),
        name = f"S(f={freq_bin:.3f})",
    ))

    fig.update_layout(
        title=f"Directional Spectrum for f = {freq_bin:.3f} Hz",
        polar = dict(
            angularaxis= dict(direction="clockwise", rotation=90),
            radialaxis = dict(title="S(θ)", ticksuffix=""),
        ),
        showlegend = False,
        margin = {"l": 30, "r": 30, "t":40, "b": 30}
    )

    return fig

if __name__ == "__main__":
    app.run(debug=True)