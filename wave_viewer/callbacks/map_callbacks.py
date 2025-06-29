import pandas as pd
from dash import Input, Output
from components.plots import build_spectrum_plot, build_polar_plot
from sqlalchemy import create_engine, text
from data.query import get_ts_data

# create the dropdown for timestep selection and store selected buoy
def register_map_callbacks(app):
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

        results = get_ts_data(station_id)
        #sta_id_label = f"Selected station: {station_id}"

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