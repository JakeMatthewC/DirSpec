import xml.etree.ElementTree as ET
import pandas as pd
import psycopg2

# Load local XML file
tree = ET.parse(r"D:\WavePow\data\activestations.xml")
root = tree.getroot()

# Extract buoy metadata
buoy_data = []
for station in root.findall('station'):
    buoy_data.append({
        'station_id': station.attrib.get('id'),
        'name': station.attrib.get('name'),
        'lat': float(station.attrib.get('lat')),
        'lon': float(station.attrib.get('lon')),
        'depth': float(station.attrib.get('depth', 0)) or None
    })

df_buoys = pd.DataFrame(buoy_data)
print(df_buoys.head())

def insert_buoys(df_buoys, cur):
    for _, row in df_buoys.iterrows():
        cur.execute("""
            INSERT INTO buoys (buoy_id, name, lat, lon, depth)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (buoy_id) DO NOTHING;
        """, (row['station_id'], row['name'], row['lat'], row['lon'], row.get('depth')))


conn = psycopg2.connect(
    dbname="postgres",
    user="Jacob",
    password="",
    host="localhost",
    port="5432"
)
cur = conn.cursor()
insert_buoys(df_buoys, cur)

conn.commit()
cur.close()
conn.close()
