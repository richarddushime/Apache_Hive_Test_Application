-- Portfolio-Grade Hive Schema Setup for MBV Africa
-- Objectives: ORC Format, SNAPPY Compression, Partitioning, Bucketing

CREATE DATABASE IF NOT EXISTS mbv_africa;
USE mbv_africa;

-- 1. Create Staging Table (Raw Data Ingestion)
-- Using CSV format to match the generated portfolio data
CREATE EXTERNAL TABLE IF NOT EXISTS climate_observations_staging (
    station_id STRING,
    observation_date STRING,
    year INT,
    month INT,
    temp_max DOUBLE,
    temp_min DOUBLE,
    temp_mean DOUBLE,
    precipitation DOUBLE,
    humidity DOUBLE,
    sea_surface_temp DOUBLE,
    ocean_salinity DOUBLE,
    region STRING
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION '/mbv_africa/staging/observations'
TBLPROPERTIES ("skip.header.line.count"="1");

-- 2. Create Production Table (Optimized for Analytics)
-- Optimized with ORC, Snappy, Partitioning, and Bucketing
CREATE TABLE IF NOT EXISTS africa_climate_observations (
    station_id STRING,
    observation_date STRING,
    month INT,
    temp_max DOUBLE,
    temp_min DOUBLE,
    temp_mean DOUBLE,
    precipitation DOUBLE,
    humidity DOUBLE,
    sea_surface_temp DOUBLE,
    ocean_salinity DOUBLE
)
PARTITIONED BY (year INT, region STRING)
CLUSTERED BY (station_id) INTO 32 BUCKETS
STORED AS ORC
TBLPROPERTIES ("orc.compress"="SNAPPY");

-- 3. Create Weather Stations Table
CREATE TABLE IF NOT EXISTS weather_stations (
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
STORED AS ORC
TBLPROPERTIES ("orc.compress"="SNAPPY");

-- 4. Create Regions Table
CREATE TABLE IF NOT EXISTS regions (
    name STRING,
    code STRING,
    description STRING
)
STORED AS ORC;

-- Enable dynamic partitioning for ingestion
SET hive.exec.dynamic.partition=true;
SET hive.exec.dynamic.partition.mode=nonstrict;
SET hive.optimize.bucketmapjoin=true;
SET hive.optimize.bucketmapjoin.sortedmerge=true;
