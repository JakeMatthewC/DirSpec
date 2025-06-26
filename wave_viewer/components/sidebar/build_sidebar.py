from dash import dcc, html, Output, Input, State

def build_sidebar(df_ts_param,station_id,station_name):
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
        sidebar_built = html.Div([
        html.H4(f"Station {station_id}: {station_name.iloc[0,0]}"), 
        *info_items
        ])
    return sidebar_built