import dash
from dash import dcc, html, Output, Input, State
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import psycopg2
from scipy.interpolate import interp1d
from scipy.ndimage import gaussian_filter1d
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

# app layout structure
app.layout = html.Div(style={"height": "95vh", "display": "flex", "flexDirection": "column", "margin": "0px", "padding": "0px"}, children=[
    
    # Top: Map + sidebar section
    html.Div(style={"flex": "2", "display": "flex"}, children=[
        # Map
        html.Div(style={"flex": "3", 
                        "minHeight": "0px", 
                        "minWidth": "0px", 
                        "height": "100%", 
                        "width": "100%", 
                        "margin": "0", 
                        "padding": "0"}, children=[
            #html.H2("Wave Buoy Map", style={"margin": "10px"}),
            dcc.Graph(id="buoy-map", figure=fig, style={"height": "100%", "width": "100%"}, config={"displayModeBar": False}),
            dcc.Store(id="stored-buoy"),
            dcc.Store(id="stored-timestep"),
            dcc.Store(id="stored-freq")
    ]),

        # Sidebar
        html.Div(id="station-sidebar", style={
            "flex": "1",
            "padding": "10px",
            "borderLeft": "1px solid #ccc",
            "backgroundColor": "#f9f9f9",
            "overflowY": "auto",
            "height": "100%",
            "display": "flex",
            "flexDirection": "column"
        }, children=[
            # top section for timestep selection
            html.Div([
                html.Label("Select Timestep:"),
                dcc.Dropdown(
                    id="timestep-dropdown", 
                    placeholder="Choose a timestamp", 
                    options=[],
                    style={"width": "100%"},
                    clearable=False
                )
            ]),
            # bottom for station stats
            html.Div(id="station-stats", children=[
                #html.H4("Station Info"),
                html.Div(id="station-info", children="Click a buoy to view details.")
            ])
        ])
    ]),

    # Bottom: Docked spectral + polar plots
    html.Div(style={
        "flex": "1",
        "borderTop": "1px solid #ccc",
        "backgroundColor": "#f9f9f9",
        "minHeight": "0",
        "height": "100%",
        "margin": "0",
        "padding": "0"
    }, children=[       
        html.Div(style={"display": "flex", "justifyContent": "space-between", "height": "100%"}, children=[
            dcc.Graph(id="spectrum-plot", style={"flex": "3", "height": "100%"}, figure=empty_fig),
            dcc.Graph(id="polar-plot", style={"flex": "1", "height": "100%", "borderLeft": "1px solid #ccc", "marginRight": "20px"}, figure=empty_fig_spec)
        ])
    ])
])

CONN_STR = "postgresql+psycopg2://Jacob:@localhost:5432/postgres"

# create the dropdown for timestep selection and store selected buoy
@app.callback(
    Output("timestep-dropdown", "options"),
    Output("timestep-dropdown", "value"),
    Output("stored-buoy", "data"),
    Input("buoy-map", "clickData")
)
def update_timestep_dropdown(clickData):
    if not clickData:
        return {}, None, None
    
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
        return options, default_value, station_id

# this is to store the selected timestep into stored-timestep for grabbing spec data
@app.callback(
    Output("stored-timestep", "data"),
    Input("timestep-dropdown", "value")
)
def store_selected_timestep(timestep_id):
    return timestep_id

# callback to create the spectrum plot in bottom left pane and populate sidebar
@app.callback(
    Output("spectrum-plot", "figure"),
    Output("station-info", "children"),
    Input("stored-timestep", "data"),
    Input("stored-buoy", "data"),
    Input("stored-freq", "data"),
    prevent_initial_call=True
)
def update_spectrum_plot(timestep_id, selected_buoy, selected_freq):
    station_id = selected_buoy
    # Connect to postgres
    engine = create_engine(CONN_STR)
    conn = engine.connect()

    # Now get spectrum for this time_step
    df = pd.read_sql(text("""
        SELECT frequency, energy_density, alpha1, alpha2, r1, r2
        FROM spectra_parameters
        WHERE time_step_id = :timestep_id
        ORDER BY frequency
    """), conn, params={"timestep_id": timestep_id})

    df_ts_param = pd.read_sql(text("""
        SELECT wdir, wspd, gst, wvht, dpd, apd, mwd, pres, atmp, wtmp, dewp, vis, ptdy, tide, hm0, te, p
        FROM time_steps
        WHERE id = :timestep_id
    """), conn, params={"timestep_id": timestep_id})

    station_name = pd.read_sql(text("""
        SELECT b.name
        FROM buoys b
        WHERE b.station_id = :station_id
    """), conn, params={"station_id": station_id})

    # fetch timestamp for plot titles
    if df.empty == False:
        timestamp = pd.read_sql(
            text("SELECT timestamp FROM time_steps WHERE id = :id"),
            conn,params={"id": timestep_id})["timestamp"].iloc[0]
        
        sidebar_data = {
            "Wind Direction (Degrees)": df_ts_param.loc[0,"wdir"],
            "Wind Speed (m/s)": df_ts_param.loc[0,"wspd"],
            "Max Gust (m/s)": df_ts_param.loc[0,'gst'],
            "Signigicant Wave Height (m)": df_ts_param.loc[0,'wvht'],
            "Dominant Wave Period (sec)": df_ts_param.loc[0,'dpd'],
            "Average Wave Period (sec)": df_ts_param.loc[0,'apd'],
            "Calculated Significant Wave Height (m)": f"{df_ts_param.loc[0,'hm0']:.2f}",
            "Calculated Wave Energy Period (s)": f"{df_ts_param.loc[0,'te']:.2f}",
            "Calculated Wave Potential Power (kW/m)": f"{df_ts_param.loc[0,'p']:.2f}",
        }

        info_items = []
        for label, value in sidebar_data.items():
            val_str = "-" if value is None else f"{value:.2f}" if isinstance(value, (float, int)) else str(value)
            info_items.append(html.P(f"{label}: {val_str}"))
            sidebar_out = html.Div([
            html.H4(f"Station {station_id}: {station_name.iloc[0,0]}"), 
            *info_items
        ])

        '''fig = go.Figure()
        fig.add_trace(go.Bar(x=df["frequency"], y=df["energy_density"]))
        fig.update_layout(
            xaxis_title="Frequency (Hz)",
            yaxis_title="Energy Density (m²/Hz)",
            title=f"Energy Spectrum for Station {station_id} ({timestamp.strftime('%Y-%m-%d %H:%M')})"
        )'''

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

        return fig, sidebar_out
    else:
        return empty_fig, None

@app.callback(
    Output("polar-plot","figure"),
    Output("stored-freq", "data"),
    Input("spectrum-plot","clickData"),
    Input("stored-timestep", "data")
)
def update_polar_plot(clickData, time_step_id):
    # handle nonclicks and no timesteps available
    if not clickData or time_step_id is None:
        return empty_fig_spec, None
    
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
        return {}, None
    
    # rolling smoothing of D
    df["dir_smooth"] = gaussian_filter1d(df["spreading"], sigma=2)

    # get the max value so that the plot can be sized
    max_val = df['dir_smooth'].max()
    radial_limit = max_val*1.1

    # build S = D * E(f) for the selected frequency
    #E = df["energy_density"].iloc[0]
    #df["S_raw"] = df["spreading"] * E
    #df["S_smooth"] = df["dir_smooth"] * E

    # create the figure
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

    return fig, freq_bin

if __name__ == "__main__":
    app.run(debug=True)