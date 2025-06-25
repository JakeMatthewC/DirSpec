from dash import Input, Output

# queries
import data.query as dq
# components
from components.sidebar.build_sidebar  import build_sidebar
from components.plots.build_spectrum_plot import build_spec_plot
from components.plots.build_polar_plot import build_polar_plot
from components.empty_figs import empty_fig, empty_fig_spec


def register_plot_callbacks(app):
    @app.callback(
    Output("spectrum-plot", "figure"),
    Output("station-info", "children"),
    Input("stored-timestep", "data"),
    Input("stored-buoy", "data"),
    Input("stored-freq", "data"),
    prevent_initial_call=True)
    
    def update_spectrum_plot(timestep_id, selected_buoy, selected_freq):
        station_id = selected_buoy

        # get spectrum for selected time_step
        df = dq.get_spectrum_for_timestep(timestep_id)

        # get station parameters for selected timestep
        df_ts_param = dq.get_param_for_timestep(timestep_id)

        # get the station name for the sidebar
        station_name = dq.get_station_name(station_id)

        # fetch timestamp for plot titles
        if df.empty == False:
            timestamp = dq.get_timestamp(timestep_id)
            
            # build the data that goes to the sidebar
            sidebar_out = build_sidebar(df_ts_param,station_id,station_name)

            fig = build_spec_plot(df)

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
    def update_polar_plot(clickData, timestep_id):
        # handle nonclicks and no timesteps available
        if not clickData or timestep_id is None:
            return empty_fig_spec, None
        
        # extract frequency bin from click
        freq_bin = clickData["points"][0]["x"]

        # pull spectral data from postgres
        df = dq.get_spectral_data(timestep_id,freq_bin)

        # handle no return from postgres
        if df.empty:
            return {}, None
        
        fig = build_polar_plot(df,freq_bin)

        return fig, freq_bin
    
        