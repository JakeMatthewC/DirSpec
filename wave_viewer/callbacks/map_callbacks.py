import pandas as pd
from dash import Input, Output, State, Patch
from dash.exceptions import PreventUpdate

import data.query as dq

# create the dropdown for timestep selection and store selected buoy
def register_map_callbacks(app):

    # callback for selecting a buoy from the map and storing
    @app.callback(
        Output("stored-buoy", "data"),
        Input("buoy-map", "clickData"),
        prevent_initial_call = True
    )
    def update_selected_buoy(clickData):
        if not clickData:
            raise PreventUpdate
        
        buoy_id = clickData["points"][0]["customdata"][0]
                            
        return buoy_id

    # callback to populate the deployment dropdown for selected buoy
    @app.callback(
            Output("deployment-dropdown", "options"),
            Output("deployment-dropdown", "value"),
            Input("stored-buoy", "data"),
            prevent_initial_call = True
    )
    def update_deployment_dropdown(buoy_id):

        df = dq.get_buoy_deployments(buoy_id)

        if df.empty:
            return [], None

        options = [
            {
                "label": (
                    f"{row.start_time:%Y-%m-%d} to "
                    f"{row.end_time:%Y-%m-%d}"
                    if pd.notna(row.end_time)
                    else f"{row.start_time:%Y-%m-%d} to Present"
                ),
                "value": row.deployment_id
            }
            for _, row in df.iterrows()
        ]

        latest_deployment = df.iloc[0]['deployment_id']

        return options, latest_deployment

    # callback for storing the selected deployment
    @app.callback(
        Output("stored-deployment", "data"),
        Input("deployment-dropdown", "value"),
        prevent_initial_call = True
    )
    def store_deployment(deployment_id):
        return deployment_id

    # callback for updating map plot when a deployment is selected from the deployment list
    @app.callback(
        Output("buoy-map", "figure"),
        Input("stored-deployment", "data"),
        State("stored-buoy", "data"),
        prevent_initial_call = True
        )
    def update_map(selected_deployment, selected_buoy):

        if selected_deployment is None:
            raise PreventUpdate
    
        deployment = dq.get_deployment_info(selected_deployment)

        if deployment.empty:
            raise PreventUpdate

        row = deployment.iloc[0]   

        lat = float(row["lat"])
        lon = float(row["lon"])

        start_display = pd.to_datetime(
            row["start_time"], utc=True
        ).strftime("%Y-%m-%d")

        if pd.notna(row["end_time"]):
            end_display = pd.to_datetime(
                row["end_time"], utc=True
            ).strftime("%Y-%m-%d")
        else:
            end_display = "Present"

        patched_fig = Patch()

        patched_fig["data"][1]["lat"] = [lat]
        patched_fig["data"][1]["lon"] = [lon]
    
        patched_fig["data"][1]["customdata"] = [[
            selected_buoy,          # 0
            row["station_id"],      # 1
            selected_deployment,    # 2
            row["name"],            # 3
            lat,                    # 4
            lon,                    # 5
            start_display,          # 6
            end_display,            # 7
            row["depth"],           # 8
            row["project"]          # 9
        ]]
    
        return patched_fig

    # callback for populating the date picker
    @app.callback(
        Output("date-picker", "min_date_allowed"),
        Output("date-picker", "max_date_allowed"),
        Output("date-picker", "date"),
        Input("stored-deployment", "data"),
        prevent_initial_call = True
    )
    def update_date_picker(deployment_id):
        if deployment_id is None:
            return None, None, None

        df = dq.get_deployment_timesteps(deployment_id)

        if df.empty:
            return None, None, None

        dates = pd.to_datetime(df["date"])

        min_date = dates.min().date()
        max_date = dates.max().date()

        selected_date = max_date

        return min_date, max_date, selected_date

    # callback for populating the timestep selector
    @app.callback(
        Output("timestep-dropdown", "options"),
        Output("timestep-dropdown", "value"),
        Input("date-picker", "date"),
        Input("stored-deployment", "data"),
        prevent_initial_call = True        
    )
    def update_timestep_selector(selected_date, deployment_id):
        if selected_date is None or deployment_id is None:
            return [], None

        df = dq.get_timesteps_for_date(deployment_id, selected_date)

        if df.empty:
            return [], None

        options = []

        for _, row in df.iterrows():
            timestamp = pd.to_datetime(row["timestamp"])

            label = timestamp.strftime("%H:%M")

            if row["is_storm"]:
                storm_name = row["storm_name"] or "Storm"
                label += f" Hurricane {storm_name}"

            options.append({
                "label": label,
                "value": int(row['id'])
            })

        return options, options[0]["value"]

    # callback for pushing the stored timestep to stored-timestep
    @app.callback(
        Output("stored-timestep", "data"),
        Input("timestep-dropdown", "value"),
        prevent_initial_call = True
    )
    def store_timestep(timestep_id):
        return timestep_id    

