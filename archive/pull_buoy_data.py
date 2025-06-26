import pandas as pd
import math
import numpy as np
import psycopg2
import psycopg2.extras
import sys

buoys = [46026, 41009]
url = r'https://www.ndbc.noaa.gov/data/realtime2/'
wpm_path = 'D:\WavePow\data\WPM_spectra.xlsx'

def create_tables(conn):
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS buoys (
                id SERIAL PRIMARY KEY,
                buoy_id TEXT UNIQUE NOT NULL,
                name TEXT,
                lat DOUBLE PRECISION,
                lon DOUBLE PRECISION,
                depth DOUBLE PRECISION
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS time_steps (
                id SERIAL PRIMARY KEY,
                buoy_id INTEGER REFERENCES buoys(id),
                timestamp TIMESTAMPTZ NOT NULL,

                -- Observational metadata
                station_id TEXT,                  -- NDBC ID (e.g., '46026')
                WDIR INTEGER,                     -- Wind direction (degrees)
                WSPD DOUBLE PRECISION,            -- Wind speed (m/s or knots)
                GST  DOUBLE PRECISION,            -- Wind gust (m/s or knots)
                WVHT DOUBLE PRECISION,            -- Significant wave height [m]
                DPD  DOUBLE PRECISION,            -- Dominant period [s]
                APD  DOUBLE PRECISION,            -- Average period [s]
                MWD  DOUBLE PRECISION,            -- Mean wave direction (from) [deg]
                PRES DOUBLE PRECISION,            -- Atmospheric pressure [hPa]
                ATMP DOUBLE PRECISION,            -- Air temp [°C]
                WTMP DOUBLE PRECISION,            -- Water temp [°C]
                DEWP DOUBLE PRECISION,            -- Dew point [°C]
                VIS  DOUBLE PRECISION,            -- Visibility [nmi]
                PTDY DOUBLE PRECISION,            -- Pressure tendency [hPa]
                TIDE DOUBLE PRECISION,            -- Tide level [ft or m]

                -- Derived spectral parameters
                m0   DOUBLE PRECISION,            -- Spectral moment 0
                hm0  DOUBLE PRECISION,            -- Significant wave height from spectrum
                m_1  DOUBLE PRECISION,            -- Spectral moment 1
                Te   DOUBLE PRECISION,            -- Energy period
                P    DOUBLE PRECISION,            -- Wave power [kW/m]

            UNIQUE (buoy_id, timestamp)
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS spectra (
                id SERIAL PRIMARY KEY,
                time_step_id INTEGER REFERENCES time_steps(id),
                frequency DOUBLE PRECISION,
                direction INTEGER,
                dir_dist DOUBLE PRECISION,
                energy_density DOUBLE PRECISION,
                spectra_ingested BOOLEAN DEFAULT FALSE,
                UNIQUE (time_step_id, frequency, direction)
            );
        """)

        conn.commit()

def insert_time_steps(df_time_steps, cur):
    for _, row in df_time_steps.iterrows():
        # Get buoy ID (assumes station_id already inserted in buoys)
        cur.execute("SELECT id FROM buoys WHERE station_id = %s", (row['station_id'],))
        buoy_id = cur.fetchone()
        if buoy_id:
            cur.execute("""
                INSERT INTO time_steps (
                    buoy_id, timestamp, WDIR, WSPD, GST, WVHT, DPD, APD, MWD, PRES,
                    ATMP, WTMP, DEWP, VIS, PTDY, TIDE, m0, hm0, m_1, Te, P
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (buoy_id, timestamp) DO NOTHING;
            """, (
                buoy_id[0], row['datetime'],
                safe_val(row.get('WDIR')), safe_val(row.get('WSPD')), safe_val(row.get('GST')), safe_val(row.get('WVHT')),
                safe_val(row.get('DPD')), safe_val(row.get('APD')), safe_val(row.get('MWD')), safe_val(row.get('PRES')),
                safe_val(row.get('ATMP')), safe_val(row.get('WTMP')), safe_val(row.get('DEWP')), safe_val(row.get('VIS')),
                safe_val(row.get('PTDY')), safe_val(row.get('TIDE')), safe_val(row.get('m0')), safe_val(row.get('hm0')),
                safe_val(row.get('m_1')), safe_val(row.get('Te')), safe_val(row.get('P'))
            ))

def get_unprocessed_timesteps(cur, station_id):
    # Step 1: get buoy_id from station_id
    cur.execute("SELECT id FROM buoys WHERE station_id = %s", (station_id,))
    buoy = cur.fetchone()
    if not buoy:
        return []

    buoy_id = buoy[0]

    # Step 2: get time steps where spectra_ingested is false
    cur.execute("""
        SELECT timestamp
        FROM time_steps
        WHERE buoy_id = %s AND (spectra_ingested = FALSE OR spectra_ingested IS NULL)
        ORDER BY timestamp
    """, (buoy_id,))

    return cur.fetchall()  # returns list of (timestamp)         

def get_time_step_id(cur, station_id, dt_utc):
    cur.execute("""
        SELECT ts.id
        FROM time_steps ts
        JOIN buoys b ON ts.buoy_id = b.id
        WHERE b.station_id = %s AND ts.timestamp = %s
    """, (station_id, dt_utc))
    
    result = cur.fetchone()
    return result[0] if result else None

def datetime_dfs(x,buoy_id):
    new_columns = ['year','month','day','hour','minute']
    x.rename(columns=dict(zip(x.columns[0:5], new_columns)),inplace=True)
    x.insert(0,'datetime',pd.to_datetime(x[['year', 'month', 'day', 'hour', 'minute']],utc=True))
    x.insert(0,'station_id',buoy_id)
    x.drop(['year', 'month', 'day', 'hour', 'minute'], axis='columns',inplace=True)
    return x

def safe_val(val):
    return None if pd.isna(val) else val

def met_to_math_dir(angle_deg):
    return np.deg2rad((270 - angle_deg) % 360)

def get_buoy_data():    
    for buoy_id in buoys:  
        # create the buoy filepath to request from
        txt_buoy_file = f"https://www.ndbc.noaa.gov/data/realtime2/{buoy_id}.txt"
        data_spec_buoy_file = f"https://www.ndbc.noaa.gov/data/realtime2/{buoy_id}.data_spec"
        swdir_buoy_file = f"https://www.ndbc.noaa.gov/data/realtime2/{buoy_id}.swdir"
        swr1_buoy_file = f"https://www.ndbc.noaa.gov/data/realtime2/{buoy_id}.swr1"
        swdir2_buoy_file = f"https://www.ndbc.noaa.gov/data/realtime2/{buoy_id}.swdir2"
        swr2_buoy_file = f"https://www.ndbc.noaa.gov/data/realtime2/{buoy_id}.swr2"

        # load to dataframes
        df_txt = pd.read_csv(txt_buoy_file, sep='\s+', skiprows=[1], na_values=["MM",'999.0'])
        df_data_spec = pd.read_csv(data_spec_buoy_file, sep='\s+', skiprows=[0], na_values=["MM",'999.0'], header=None)
        df_swdir = pd.read_csv(swdir_buoy_file, sep='\s+', skiprows=[0], na_values=["MM",'999.0'], header=None)
        df_swr1 = pd.read_csv(swr1_buoy_file, sep='\s+', skiprows=[0], na_values=["MM",'999.0'], header=None)
        df_swdir2 = pd.read_csv(swdir2_buoy_file, sep='\s+', skiprows=[0], na_values=["MM",'999.0'], header=None)
        df_swr2 = pd.read_csv(swr2_buoy_file, sep='\s+', skiprows=[0], na_values=["MM",'999.0'], header=None)

        # create datetime columns for dataframes (needed for matching timesteps across dataframes)
        df_list = [df_txt,df_data_spec,df_swdir,df_swr1,df_swdir2,df_swr2]
        for df in df_list:
            df = datetime_dfs(df,buoy_id)

        # remove frequency identifiers
        df_data_spec.drop(range(7,98,2),axis='columns',inplace=True)        
        df_swdir.drop(range(6,97,2),axis='columns',inplace=True)
        df_swr1.drop(range(6,97,2),axis='columns',inplace=True)
        df_swdir2.drop(range(6,97,2),axis='columns',inplace=True)
        df_swr2.drop(range(6,97,2),axis='columns',inplace=True)

        # rename frequency columns with integers for simplicity
        column_list = ['station_id','datetime','sep_freq'] + list(range(1,47))
        df_data_spec = df_data_spec.set_axis(column_list,axis=1)
        # repeat for the rest without sep_freq column
        column_list = ['station_id','datetime'] + list(range(1,47))
        df_swdir = df_swdir.set_axis(column_list,axis=1)
        df_swdir2 = df_swdir2.set_axis(column_list,axis=1)
        df_swr1 = df_swr1.set_axis(column_list,axis=1)
        df_swr2 = df_swr2.set_axis(column_list,axis=1)

        # remove unneeded timesteps from df_txt
        df_txt = df_txt[df_txt['datetime'].isin(df_data_spec['datetime'])]
        df_txt = df_txt.reset_index(drop=True)

        # remove unmatching timesteps from spec dataframes (no df_txt match)
        df_data_spec = df_data_spec[df_data_spec['datetime'].isin(df_txt['datetime'])]
        df_swdir = df_swdir[df_swdir['datetime'].isin(df_txt['datetime'])]
        df_swdir2 = df_swdir2[df_swdir2['datetime'].isin(df_txt['datetime'])]
        df_swr1 = df_swr1[df_swr1['datetime'].isin(df_txt['datetime'])]
        df_swr2 = df_swr2[df_swr2['datetime'].isin(df_txt['datetime'])]

        df_data_spec = df_data_spec.reset_index(drop=True)
        df_swdir = df_swdir.reset_index(drop=True)
        df_swdir2 = df_swdir2.reset_index(drop=True)
        df_swr1 = df_swr1.reset_index(drop=True)
        df_swr2 = df_swr2.reset_index(drop=True)

        # do calculations for specific timestep -> df_txt is timestep output table
        calc = df_data_spec.iloc[:,3:50] * bandwidths
        # zeroth moment and Hm0
        df_txt['m0'] = calc.sum(axis=1)
        df_txt['hm0'] = np.sqrt(df_txt['m0'])*4
        calc2 = calc / center_freqs
        # 1st moment, energy period, and wave power
        df_txt['m_1'] = calc2.sum(axis=1)
        df_txt['Te'] = df_txt['m_1'] / df_txt['m0']
        df_txt['P'] = (1025 * 9.81**2 * df_txt['hm0']**2 * df_txt['Te']) / (64 * np.pi * 1000)

        # convert the buoy ids to strings
        df_txt['station_id'] = df_txt['station_id'].astype(str)

        # write the new timesteps for the buoy to the timestep table
        cur = conn.cursor()
        insert_time_steps(df_txt,cur)
        conn.commit()

        # check for spectrum ingested flag across timesteps
        unprocessed_timesteps = get_unprocessed_timesteps(cur, str(buoy_id))
        flat = [row[0] for row in unprocessed_timesteps if row and row[0] is not None]
        dt_index = pd.to_datetime(flat, utc=True)

        # select timesteps from the current data where flag isn't set to true
        df_data_spec = df_data_spec[df_data_spec['datetime'].isin(dt_index)]
        df_swr1 = df_swr1[df_swr1['datetime'].isin(dt_index)]
        df_swr2 = df_swr2[df_swr2['datetime'].isin(dt_index)]
        df_swdir = df_swdir[df_swdir['datetime'].isin(dt_index)]
        df_swdir2 = df_swdir2[df_swdir2['datetime'].isin(dt_index)]

        # loop through each timestep needed (i = timestep index)
        # this builds the spectra table with concatentation
        for i,spec_row in df_data_spec.iterrows():
            # get the timestep rows for all tables needed
            swdir_row = df_swdir.iloc[i,:]
            swdir2_row = df_swdir2.iloc[i,:]
            swr1_row = df_swr1.iloc[i,:]
            swr2_row = df_swr2.iloc[i,:]

            # check that all files have the timestep
            if spec_row['datetime'] == swdir_row['datetime'] and spec_row['datetime'] == swdir2_row['datetime'] and spec_row['datetime'] == swr1_row['datetime'] and spec_row['datetime'] == swr2_row['datetime']:
                pass
            else:
                print('Datetime mismatch')
                sys.exit()
                break

            # save the datetime object for reference later
            datetime_obj = spec_row['datetime']
            
            # drop the unneeded rows for calculations
            spec_row = spec_row.iloc[3:]
            swdir_row = swdir_row.iloc[2:]
            swdir2_row = swdir2_row.iloc[2:]
            swr1_row = swr1_row.iloc[2:]
            swr2_row = swr2_row.iloc[2:]
            
            # prepare for vectorized calculation
            alpha1 = pd.to_numeric(swdir_row, errors='coerce')
            alpha1 = np.where(~np.isnan(alpha1), met_to_math_dir(alpha1), np.nan)
            alpha1.astype(float)
            alpha2 = pd.to_numeric(swdir2_row, errors='coerce')
            alpha2 = np.where(~np.isnan(alpha2), met_to_math_dir(alpha2), np.nan)
            alpha2.astype(float)

            r1 = pd.to_numeric(swr1_row,errors='coerce')
            r1 = np.array(r1)
            r2 = pd.to_numeric(swr2_row, errors='coerce')
            r2 = np.array(r2)

            Ef = pd.to_numeric(spec_row, errors='coerce')
            Ef = np.array(Ef)

            alpha1_grid = alpha1[:,None]
            alpha2_grid = alpha2[:, None]
            E = Ef[:, None]

            D = (1 / (2 * np.pi)) * (
                (1 + 2 * r1[:, None] * np.cos(theta_grid - alpha1_grid))
                + (2 * r2[:, None] * np.cos(2 * (theta_grid - alpha2_grid))
                ))
            
            row_sums = np.sum(D, axis=1, keepdims=True) * delta_theta_rad
            row_sums[row_sums == 0] = 1
            D_normalized = D / row_sums
            check = np.sum(D_normalized, axis=1, keepdims=True) * delta_theta_rad

            S = D_normalized * E

            # get the timestep id from the timesteps table
            timestep_id = get_time_step_id(cur, str(buoy_id), datetime_obj)

            # organize for exporting to postgres table
            records = []
            for m, f in enumerate(freqs):
                for n, theta in enumerate(directional_pnts):
                    spreading = D_normalized[m, n]
                    energy_density = E[m, 0]
                    records.append((int(timestep_id), float(f), int(theta), float(spreading), float(energy_density)))

            # write the spectral data to the spec table
            spectra_insert_query = """
                INSERT INTO spectra (time_step_id, frequency, direction, dir_spread, energy_density)
                VALUES %s
                ON CONFLICT (time_step_id, frequency, direction) DO NOTHING
            """

            psycopg2.extras.execute_values(
                cur, spectra_insert_query, records, page_size=100
            )
            conn.commit()

            # update flag
            cur.execute("""
                UPDATE time_steps
                SET spectra_ingested = TRUE
                WHERE id = %s
            """, (timestep_id,))
            conn.commit()

            
            
                    
# run table setup function to ensure tables exist
conn = psycopg2.connect(
    dbname="postgres",
    user="Jacob",
    password="",
    host="localhost",
    port="5432"
)
create_tables(conn)

# pull in the wpm freqs and bin sizes
wpm_data = pd.read_excel(wpm_path,header=None,skiprows=1)
center_freqs = pd.Series(wpm_data.iloc[:,1])
freqs = np.array(center_freqs)
bandwidths = pd.Series(wpm_data.iloc[:,2])

# create 72 directional points to iterate over for NOAA buoys
directional_pnts = np.arange(0,360,5)
theta_grid = directional_pnts[None, :]
delta_theta_deg = 5
delta_theta_rad = np.deg2rad(delta_theta_deg)

# pull down and process the NOAA buoy data
get_buoy_data()

conn.close()
