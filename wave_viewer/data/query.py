from sqlalchemy import create_engine, text
import pandas as pd

CONN_STR = "postgresql+psycopg2://Jacob:@localhost:5432/postgres"

# get buoy data for map plot
def get_buoy_locations():
    engine = create_engine(CONN_STR)
    conn = engine.connect()
    df = pd.read_sql("""
        SELECT b.station_id, b.name, b.lat, b.lon
        FROM buoys b
        JOIN time_steps ts ON ts.buoy_id = b.id
        JOIN spectra_parameters sp ON sp.time_step_id = ts.id
        GROUP BY b.station_id, b.name, b.lat, b.lon;
    """, conn)
    conn.close()
    return df

def get_spectrum_for_timestep(timestep_id):
    engine = create_engine(CONN_STR)
    conn = engine.connect()
    df = pd.read_sql(text("""
        SELECT frequency, energy_density, alpha1, alpha2, r1, r2
        FROM spectra_parameters
        WHERE time_step_id = :timestep_id
        ORDER BY frequency
    """), conn, params={"timestep_id": timestep_id})
    return df

def get_param_for_timestep(timestep_id):
    engine = create_engine(CONN_STR)
    conn = engine.connect()
    df_ts_param = pd.read_sql(text("""
        SELECT wdir, wspd, gst, wvht, dpd, apd, mwd, pres, atmp, wtmp, dewp, vis, ptdy, tide, hm0, te, p
        FROM time_steps
        WHERE id = :timestep_id
    """), conn, params={"timestep_id": timestep_id})
    return df_ts_param

def get_station_name(station_id):
    engine = create_engine(CONN_STR)
    conn = engine.connect()
    station_name = pd.read_sql(text("""
        SELECT b.name
        FROM buoys b
        WHERE b.station_id = :station_id
    """), conn, params={"station_id": station_id})
    return station_name

def get_timestamp(timestep_id):
    engine = create_engine(CONN_STR)
    conn = engine.connect() 
    timestamp = pd.read_sql(text(
        "SELECT timestamp FROM time_steps WHERE id = :id"),
        conn,params={"id": timestep_id})["timestamp"].iloc[0]
    return timestamp

def get_timesteps_for_dd(station_id):
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
    return results

def get_spectral_data(timestep_id, freq_bin):
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
        """), conn, params={"ts": timestep_id, "f": freq_bin})
        return df