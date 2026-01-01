USE mbv_africa;

-- Enable dynamic partitioning
SET hive.exec.dynamic.partition=true;
SET hive.exec.dynamic.partition.mode=nonstrict;

-- 1. Load data into Staging (External table already points to /mbv_africa/staging/observations)
-- We just need to ensure the stations staging exists as well if we want to follow the same pattern
CREATE EXTERNAL TABLE IF NOT EXISTS weather_stations_staging (
    station_id STRING,
    station_name STRING,
    country STRING,
    region STRING,
    latitude DOUBLE,
    longitude DOUBLE,
    elevation DOUBLE,
    is_coastal BOOLEAN,
    is_active BOOLEAN
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION '/mbv_africa/staging/stations'
TBLPROPERTIES ("skip.header.line.count"="1");

-- 2. Populate Production Observations (Partitioned & Bucketed ORC)
PRINT 'Populating africa_climate_observations...';
INSERT OVERWRITE TABLE africa_climate_observations PARTITION(year, region)
SELECT 
    station_id, 
    observation_date, 
    month, 
    temp_max, 
    temp_min, 
    temp_mean, 
    precipitation, 
    humidity, 
    sea_surface_temp, 
    ocean_salinity,
    year, 
    region
FROM climate_observations_staging;

-- 3. Populate Production Weather Stations (ORC)
PRINT 'Populating weather_stations...';
INSERT OVERWRITE TABLE weather_stations
SELECT * FROM weather_stations_staging;

-- 4. Populate Regions
PRINT 'Populating regions...';
INSERT OVERWRITE TABLE regions
SELECT DISTINCT region, 
       CASE 
         WHEN region = 'East' THEN 'EA'
         WHEN region = 'West' THEN 'WA'
         WHEN region = 'North' THEN 'NA'
         WHEN region = 'South' THEN 'SA'
         WHEN region = 'Central' THEN 'CA'
       END as code,
       CONCAT(region, ' African Region') as description
FROM weather_stations_staging;

-- 5. Verification
SELECT region, year, COUNT(*) as record_count 
FROM africa_climate_observations 
GROUP BY region, year 
LIMIT 10;
