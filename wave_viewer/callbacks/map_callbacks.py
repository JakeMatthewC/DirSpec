import pandas as pd
from dash import Input, Output
from components.plots import build_spectrum_plot, build_polar_plot
from sqlalchemy import create_engine, text

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

        CONN_STR = "postgresql+psycopg2://Jacob:@localhost:5432/postgres"

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