from dash import Input, Output
import pandas as pd

# queries
import data.query as dq

# utils
import utils.utils as u

# config
import config.config as c

# components
from components.sidebar.build_sidebar  import build_sidebar
from components.plots.build_spectrum_plot import build_spec_plot
from components.plots.build_polar_plot import build_polar_plot
from components.empty_figs import empty_fig, empty_fig_spec

def register_plot_callbacks(app):

    # callback for updating the spectrum plot when a buoy deployment is selected
    @app.callback(
    Output("spectrum-plot", "figure"),
    Output("station-info", "children"),
    Input("stored-timestep", "data"),
    Input("stored-buoy", "data"),
    Input("stored-freq", "data"),
    prevent_initial_call=True
    )   
    def update_spectrum_plot(timestep_id, selected_buoy, selected_freq):

        # get spectrum for selected time_step
        df = dq.get_spectrum_for_timestep(timestep_id)

        # get station parameters for selected timestep
        df_ts_param = dq.get_param_for_timestep(timestep_id)

        # get the station name and id for the sidebar
        station_name = dq.get_station_name(selected_buoy)
        station_id = dq.get_station_id(selected_buoy)

        # fetch timestamp for plot titles
        if df.empty == False:
            #timestamp = dq.get_timestamp(timestep_id)
            
            # build the data that goes to the sidebar
            sidebar_out = build_sidebar(df_ts_param, station_id, station_name)

            fig = build_spec_plot(df,selected_freq)

            return fig, sidebar_out
        else:
            return empty_fig, None

    # callback for updating the polar plot when a frequency bin is selected
    @app.callback(
    Output("polar-plot","figure"),
    Output("stored-freq", "data"),
    Input("spectrum-plot","clickData"),
    Input("stored-timestep", "data"),
    prevent_initial_call = True
    )
    def update_polar_plot(clickData, timestep_id):
        # handle nonclicks and no timesteps available
        if not clickData or timestep_id is None:
            return empty_fig_spec, None

        # extract frequency bin from click
        freq_bin = clickData["points"][0]["x"]

        # dirspec.spectra_directional is gone -- D(theta) is rebuilt from the
        # stored Fourier parameters every time. One code path, so the plot can no
        # longer disagree with what the pipeline computed.
        spec_params = dq.get_spectral_parameters(timestep_id, freq_bin)
        if spec_params.empty:
            return empty_fig_spec, None

        row = spec_params.iloc[0]

        D = u.reconstrust_directional_spectrum(
            alpha1 = row["alpha1"],
            alpha2 = row["alpha2"],
            r1 = row["r1"],
            r2 = row["r2"],
            directions_deg = c.directional_pnts_deg
        )

        # alpha/r are NULL for bins the buoy could not resolve, and MEM is
        # undefined as r1 approaches 1
        if D is None:
            return empty_fig_spec, None

        polar_df = pd.DataFrame({
            "direction": c.directional_pnts_deg,
            "spreading": D
        })

        fig = build_polar_plot(
            polar_df,
            freq_bin,
            alpha1 = row["alpha1"],
            energy_density = row["energy_density"],
        )

        return fig, freq_bin
    
        