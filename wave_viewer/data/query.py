from sqlalchemy import create_engine, text
import pandas as pd

CONN_STR = "postgresql+psycopg2://Jacob:@localhost:5432/postgres"
engine = create_engine(CONN_STR)

def get_station_id(buoy_id):
    with engine.connect() as conn:
        df = pd.read_sql(text("""
            SELECT
                station_id
            FROM dirspec.buoys b
            WHERE b.id = :buoy_id
        """), conn, params={"buoy_id": buoy_id})
        return df.iloc[0]["station_id"]

# get buoy data for map plot
def get_buoy_locations():
    with engine.connect() as conn:
        df = pd.read_sql("""
            SELECT DISTINCT ON (buoy_id)
                bd.buoy_id, 
                bd.deployment_id, 
                bd.start_time, 
                bd.end_time, 
                bd.lat, 
                bd.lon, 
                bd.deployment_type, 
                bd.notes, 
                bd.depth, 
                b.station_id, 
                b.name, 
                b.project
            FROM dirspec.buoy_deployments bd
            JOIN dirspec.buoys b 
                ON bd.buoy_id = b.id
            ORDER BY bd.buoy_id, bd.start_time DESC;
        """, conn)
        return df

# get buoy deployments for selected buoy
def get_buoy_deployments(buoy_id):
    with engine.connect() as conn:
        df = pd.read_sql(text("""
            SELECT
                deployment_id,
                start_time,
                end_time,
                lat,
                lon
            FROM dirspec.buoy_deployments
            WHERE buoy_id = :buoy_id
            ORDER BY start_time DESC
        """), conn, params={"buoy_id": buoy_id})
        return df

# get all timesteps for deployment
def get_deployment_timesteps(deployment_id):
    with engine.connect() as conn:
        df = pd.read_sql(text("""
            SELECT DISTINCT DATE(ts.timestamp) AS date
            FROM dirspec.time_steps ts
            JOIN dirspec.buoy_deployments bd
                ON ts.buoy_id = bd.buoy_id
                AND ts.timestamp >= bd.start_time
                AND (
                    bd.end_time IS NULL
                    OR ts.timestamp <= bd.end_time
                )
            JOIN dirspec.spectra_parameters sp
                ON sp.time_step_id = ts.id
            WHERE bd.deployment_id = :deployment_id
            ORDER BY date
        """), conn, params={"deployment_id": deployment_id})
        return df

# get timesteps for deployment and a given date
def get_timesteps_for_date(deployment_id, selected_date):
    with engine.connect() as conn:
        df = pd.read_sql(
            text("""
                SELECT DISTINCT
                    ts.id,
                    ts.timestamp,
                    ts.is_storm,
                    ts.storm_name,
                    ts.storm_type
                FROM dirspec.time_steps ts
                JOIN dirspec.buoy_deployments bd
                    ON ts.buoy_id = bd.buoy_id
                    AND ts.timestamp >= bd.start_time
                    AND (
                        bd.end_time IS NULL
                        OR ts.timestamp <= bd.end_time
                    )
                JOIN dirspec.spectra_parameters sp
                    ON sp.time_step_id = ts.id
                WHERE bd.deployment_id = :deployment_id
                  AND ts.timestamp >= CAST(:selected_date AS date)
                  AND ts.timestamp < CAST(:selected_date AS date) + INTERVAL '1 day'
                ORDER BY ts.timestamp
            """),
            conn,
            params={
                "deployment_id": deployment_id,
                "selected_date": selected_date
            }
        )
        return df

# get buoy deployment information for selected deployment
def get_deployment_info(deployment_id):
    with engine.connect() as conn:
        df = pd.read_sql(text("""
            SELECT
                bd.buoy_id, 
                bd.start_time, 
                bd.end_time, 
                bd.lat, 
                bd.lon, 
                bd.deployment_type, 
                bd.notes, 
                bd.depth, 
                b.station_id, 
                b.name, 
                b.project
            FROM dirspec.buoy_deployments bd
            JOIN dirspec.buoys b 
                ON bd.buoy_id = b.id
            WHERE bd.deployment_id = :deployment_id
        """), conn, params={"deployment_id": deployment_id})
        return df

def get_spectrum_for_timestep(timestep_id):
    with engine.connect() as conn:
        df = pd.read_sql(text("""
            SELECT 
                frequency, 
                energy_density, 
                alpha1, 
                alpha2, 
                r1, 
                r2
            FROM dirspec.spectra_parameters
            WHERE time_step_id = :timestep_id
            ORDER BY frequency
        """), conn, params={"timestep_id": timestep_id})
        return df

def get_param_for_timestep(timestep_id):
    with engine.connect() as conn:
        df_ts_param = pd.read_sql(text("""
            SELECT 
                wdir, 
                wspd, 
                gst, 
                wvht, 
                dpd, 
                apd, 
                mwd, 
                pres, 
                atmp, 
                wtmp, 
                dewp, 
                vis, 
                ptdy, 
                tide, 
                hm0, 
                te, 
                p
            FROM dirspec.time_steps
            WHERE id = :timestep_id
        """), conn, params={"timestep_id": timestep_id})
        return df_ts_param

def get_station_name(buoy_id):
    with engine.connect() as conn:
        station_name = pd.read_sql(text("""
            SELECT 
                b.name
            FROM dirspec.buoys b
            WHERE b.id = :buoy_id
        """), conn, params={"buoy_id": buoy_id})
        return station_name.iloc[0]['name']

def get_timestamp(timestep_id): 
    with engine.connect() as conn:
        timestamp = pd.read_sql(text(
            "SELECT timestamp FROM dirspec.time_steps WHERE id = :id"),
            conn,params={"id": timestep_id})["timestamp"].iloc[0]
        return timestamp

def get_ts_data(buoy_id):
    with engine.connect() as conn:
        results = conn.execute(
            text("""
            SELECT 
                ts.id, 
                ts.timestamp
            FROM dirspec.time_steps ts
            JOIN dirspec.buoys b 
                ON ts.buoy_id = b.id
            WHERE b.buoy_id = :buoy_id
            ORDER BY ts.timestamp DESC
            """), {"buoy_id": buoy_id}
        ).fetchall()
    return results


# def get_timesteps_for_dd(station_id):
#     engine = create_engine(CONN_STR)
#     with engine.connect() as conn:
#         results = conn.execute(
#             text("""
#             SELECT 
#                 ts.id, 
#                 ts.timestamp
#             FROM dirspec.time_steps ts
#             JOIN dirspec.buoys b 
#                 ON ts.buoy_id = b.id
#             WHERE b.station_id = :station_id
#             ORDER BY ts.timestamp DESC
#             """), {"station_id": station_id}
#         ).fetchall()
#     return results

# get_spectral_data() removed: dirspec.spectra_directional no longer exists.
# D(theta) is reconstructed from get_spectral_parameters() on demand.

def get_spectral_parameters(timestep_id, freq_bin):
    with engine.connect() as conn:
        df = pd.read_sql(
            text("""
                SELECT
                    frequency,
                    alpha1,
                    alpha2,
                    r1,
                    r2,
                    energy_density
                FROM dirspec.spectra_parameters
                WHERE time_step_id = :ts
                AND ABS(frequency - :f) < 0.000001
                LIMIT 1
            """),
            conn,
            params={
                "ts": timestep_id,
                "f": float(freq_bin)
            }
        )

    return df