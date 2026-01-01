-- Use the database
USE mbv_africa;

-- Analyze Average Temperature by Region
SELECT region, AVG(temperature) as avg_temp, AVG(rainfall) as avg_rain
FROM climate_data
GROUP BY region;

-- Identify potentially harmful ocean conditions (High Temp + Low pH)
SELECT * FROM ocean_data
WHERE sea_surface_temp > 28.0 AND ph_level < 8.0;

-- Join analysis: Correlate High Rainfall with Salinity changes
SELECT c.date_col, c.region, c.rainfall, o.salinity
FROM climate_data c
JOIN ocean_data o ON c.date_col = o.date_col AND c.region = o.region
WHERE c.rainfall > 40.0;
