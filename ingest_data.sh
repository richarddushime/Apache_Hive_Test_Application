#!/bin/bash
# Hive Data Ingestion Script
# This script creates the database, tables, and loads CSV data into Hive

set -e

HIVE_CONTAINER="hive-server"
HIVE_URL="jdbc:hive2://localhost:10000/;auth=noSasl"
DATA_DIR="/data"

echo "=============================================="
echo "MBV Africa - Hive Data Ingestion"
echo "=============================================="

# Function to run beeline command
run_hive() {
    docker exec $HIVE_CONTAINER beeline -u "$HIVE_URL" --silent=true -e "$1"
}

# Function to check if Hive is ready
wait_for_hive() {
    echo "Checking HiveServer2 health..."
    
    # First check if container health is good
    local health=$(docker inspect --format='{{.State.Health.Status}}' $HIVE_CONTAINER 2>/dev/null || echo "unknown")
    
    if [ "$health" != "healthy" ]; then
        echo "HiveServer2 container is not healthy yet (status: $health)"
        echo "Run 'docker-compose up -d' and wait for services to be healthy"
        echo "Check with: docker-compose ps"
        exit 1
    fi
    
    echo "HiveServer2 is healthy!"
}

# Check Hive readiness
wait_for_hive

# Create database and tables
echo ""
echo "Creating database and tables..."
run_hive "CREATE DATABASE IF NOT EXISTS mbv_africa;"

echo "  Creating climate_data table..."
run_hive "DROP TABLE IF EXISTS mbv_africa.climate_data;"
run_hive "CREATE TABLE mbv_africa.climate_data (date_col STRING, region STRING, temperature FLOAT, rainfall FLOAT, humidity FLOAT) ROW FORMAT DELIMITED FIELDS TERMINATED BY ',' STORED AS TEXTFILE TBLPROPERTIES ('skip.header.line.count'='1');"

echo "  Creating ocean_data table..."
run_hive "DROP TABLE IF EXISTS mbv_africa.ocean_data;"
run_hive "CREATE TABLE mbv_africa.ocean_data (date_col STRING, region STRING, sea_surface_temp FLOAT, ph_level FLOAT, salinity FLOAT) ROW FORMAT DELIMITED FIELDS TERMINATED BY ',' STORED AS TEXTFILE TBLPROPERTIES ('skip.header.line.count'='1');"

echo "  Creating portfolio_stations table..."
run_hive "DROP TABLE IF EXISTS mbv_africa.portfolio_stations;"
run_hive "CREATE TABLE mbv_africa.portfolio_stations (station_id STRING, station_name STRING, country STRING, region STRING, latitude DOUBLE, longitude DOUBLE, elevation DOUBLE, is_coastal BOOLEAN) ROW FORMAT DELIMITED FIELDS TERMINATED BY ',' STORED AS TEXTFILE TBLPROPERTIES ('skip.header.line.count'='1');"

echo "  Creating portfolio_observations table..."
run_hive "DROP TABLE IF EXISTS mbv_africa.portfolio_observations;"
run_hive "CREATE TABLE mbv_africa.portfolio_observations (station_id STRING, observation_date STRING, year INT, month INT, temp_max FLOAT, temp_min FLOAT, temp_mean FLOAT, precipitation FLOAT, humidity FLOAT, sea_surface_temp FLOAT, ocean_salinity FLOAT, region STRING) ROW FORMAT DELIMITED FIELDS TERMINATED BY ',' STORED AS TEXTFILE TBLPROPERTIES ('skip.header.line.count'='1');"

echo "Tables created!"

# Load data from CSV files
echo ""
echo "Loading data from CSV files..."

if docker exec $HIVE_CONTAINER test -f "$DATA_DIR/climate_data.csv"; then
    echo "  Loading climate_data.csv..."
    run_hive "LOAD DATA LOCAL INPATH '$DATA_DIR/climate_data.csv' OVERWRITE INTO TABLE mbv_africa.climate_data;"
fi

if docker exec $HIVE_CONTAINER test -f "$DATA_DIR/ocean_data.csv"; then
    echo "  Loading ocean_data.csv..."
    run_hive "LOAD DATA LOCAL INPATH '$DATA_DIR/ocean_data.csv' OVERWRITE INTO TABLE mbv_africa.ocean_data;"
fi

if docker exec $HIVE_CONTAINER test -f "$DATA_DIR/portfolio_stations.csv"; then
    echo "  Loading portfolio_stations.csv..."
    run_hive "LOAD DATA LOCAL INPATH '$DATA_DIR/portfolio_stations.csv' OVERWRITE INTO TABLE mbv_africa.portfolio_stations;"
fi

if docker exec $HIVE_CONTAINER test -f "$DATA_DIR/portfolio_observations.csv"; then
    echo "  Loading portfolio_observations.csv..."
    run_hive "LOAD DATA LOCAL INPATH '$DATA_DIR/portfolio_observations.csv' OVERWRITE INTO TABLE mbv_africa.portfolio_observations;"
fi

# Verify data loaded
echo ""
echo "Verifying data..."
run_hive "
SELECT 'climate_data' as table_name, COUNT(*) as row_count FROM mbv_africa.climate_data
UNION ALL
SELECT 'ocean_data', COUNT(*) FROM mbv_africa.ocean_data
UNION ALL
SELECT 'portfolio_stations', COUNT(*) FROM mbv_africa.portfolio_stations
UNION ALL
SELECT 'portfolio_observations', COUNT(*) FROM mbv_africa.portfolio_observations;
"

echo ""
echo "=============================================="
echo "Data ingestion complete!"
echo "=============================================="
