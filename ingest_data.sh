#!/bin/bash

# Create database and tables using beeline
docker exec hive-server beeline -u jdbc:hive2://localhost:10000 -e "
CREATE DATABASE IF NOT EXISTS mbv_africa;
USE mbv_africa;

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
TBLPROPERTIES ('skip.header.line.count'='1');

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
TBLPROPERTIES ('skip.header.line.count'='1');
"

echo "Tables created successfully!"

# Load data
echo "Loading climate data..."
docker exec hive-server beeline -u jdbc:hive2://localhost:10000/mbv_africa -e "
LOAD DATA LOCAL INPATH '/Apache_Hive_Test_Application/mbv_africa/scripts/climate_data.csv' OVERWRITE INTO TABLE climate_data;
"

echo "Loading ocean data..."
docker exec hive-server beeline -u jdbc:hive2://localhost:10000/mbv_africa -e "
LOAD DATA LOCAL INPATH '/Apache_Hive_Test_Application/mbv_africa/scripts/ocean_data.csv' OVERWRITE INTO TABLE ocean_data;
"

echo "Data loaded successfully!"
