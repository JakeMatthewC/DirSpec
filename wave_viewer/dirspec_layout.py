from dash import html
from dash import dcc, html

# components
from components.empty_figs import empty_fig, empty_fig_spec
from components.map.map_fig import fig

layout = html.Div(style={"height": "95vh", "display": "flex", "flexDirection": "column", "margin": "0px", "padding": "0px"}, children=[
    
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