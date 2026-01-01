import os
from pyhive import hive

def setup_hive_database():
    conn = hive.Connection(host='hive-server', port=10000, username='hive')
    cursor = conn.cursor()
    
    # Create Database
    print("Creating database mbv_africa...")
    cursor.execute("CREATE DATABASE IF NOT EXISTS mbv_africa")
    cursor.execute("USE mbv_africa")
    
    # Create Climate Table (External Table)
    print("Creating climate_data table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS climate_data (
            date_col STRING,
            region STRING,
            temperature FLOAT,
            rainfall FLOAT,
            humidity FLOAT
        )
        ROW FORMAT DELIMITED
        FIELDS TERMINATED BY ','
        STORED AS TEXTFILE
        TBLPROPERTIES ("skip.header.line.count"="1")
    """)
    
    # Create Ocean Table (External Table)
    print("Creating ocean_data table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ocean_data (
            date_col STRING,
            region STRING,
            sea_surface_temp FLOAT,
            ph_level FLOAT,
            salinity FLOAT
        )
        ROW FORMAT DELIMITED
        FIELDS TERMINATED BY ','
        STORED AS TEXTFILE
        TBLPROPERTIES ("skip.header.line.count"="1")
    """)
    
    # Load Data (Assuming data is already in HDFS or local to Hive container)
    # Ideally, we should upload files to HDFS first. For simplicity in this script, we assume
    # the files are mounted or we use LOAD DATA LOCAL INPATH if allowed.
    # Since we mounted mbv_africa, files specific path inside container:
    
    print("Loading climate data...")
    cursor.execute("LOAD DATA LOCAL INPATH '/Apache_Hive_Test_Application/mbv_africa/scripts/climate_data.csv' OVERWRITE INTO TABLE climate_data")
    
    print("Loading ocean data...")
    cursor.execute("LOAD DATA LOCAL INPATH '/Apache_Hive_Test_Application/mbv_africa/scripts/ocean_data.csv' OVERWRITE INTO TABLE ocean_data")
    
    print("Data ingestion complete.")
    conn.close()

if __name__ == '__main__':
    try:
        setup_hive_database()
    except Exception as e:
        print(f"Error: {e}")
