import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

# Constants
REGIONS = ['East', 'West', 'North', 'South', 'Central']
COUNTRIES_BY_REGION = {
    'East': ['KE', 'TZ', 'UG', 'ET', 'SO'],
    'West': ['NG', 'GH', 'SN', 'CI', 'ML'],
    'North': ['EG', 'MA', 'DZ', 'TN', 'LY'],
    'South': ['ZA', 'NA', 'BW', 'ZW', 'MZ'],
    'Central': ['CD', 'GA', 'CM', 'CF', 'CG']
}
STATIONS_COUNT = 1247
START_DATE = datetime(1950, 1, 1)
END_DATE = datetime(2024, 12, 31)

def generate_stations():
    stations = []
    for i in range(STATIONS_COUNT):
        region = random.choice(REGIONS)
        country = random.choice(COUNTRIES_BY_REGION[region])
        station_id = f"{country}-{region[:3].upper()}-{i:04d}"
        
        stations.append({
            'station_id': station_id,
            'station_name': f"Station {station_id}",
            'country': country,
            'region': region,
            'latitude': round(random.uniform(-35, 37), 4),
            'longitude': round(random.uniform(-17, 51), 4),
            'elevation': round(random.uniform(0, 3000), 1),
            'is_coastal': random.choice([True, False]),
            'is_active': True
        })
    return pd.DataFrame(stations)

def generate_observations(stations_df, rows_per_station=100):
    observations = []
    
    # Selecting a subset of dates to keep the file size manageable for simulation
    # but still statistically significant
    current_date = END_DATE
    dates = []
    for _ in range(rows_per_station):
        dates.append(current_date)
        current_date -= timedelta(days=random.randint(10, 30))
        
    for index, station in stations_df.iterrows():
        for date in dates:
            # Base variables based on region (simple simulation)
            base_temp = 25 if station['region'] in ['Central', 'West'] else 20
            
            temp_mean = round(base_temp + random.uniform(-10, 15), 1)
            temp_max = round(temp_mean + random.uniform(2, 8), 1)
            temp_min = round(temp_mean - random.uniform(2, 8), 1)
            
            precipitation = round(random.uniform(0, 200) if station['region'] in ['Central', 'East'] else random.uniform(0, 50), 1)
            humidity = round(random.uniform(40, 95), 1)
            
            sst = round(random.uniform(15, 30), 1) if station['is_coastal'] else None
            salinity = round(random.uniform(33, 37), 1) if station['is_coastal'] else None
            
            observations.append({
                'station_id': station['station_id'],
                'observation_date': date.strftime('%Y-%m-%d'),
                'year': date.year,
                'month': date.month,
                'temp_max': temp_max,
                'temp_min': temp_min,
                'temp_mean': temp_mean,
                'precipitation': precipitation,
                'humidity': humidity,
                'sea_surface_temp': sst,
                'ocean_salinity': salinity,
                'region': station['region'] # Added for partitioning convenience
            })
            
    return pd.DataFrame(observations)

if __name__ == "__main__":
    print(f"Generating {STATIONS_COUNT} stations...")
    stations_df = generate_stations()
    stations_df.to_csv('mbv_africa/data/portfolio_stations.csv', index=False)
    
    print("Generating observations (this may take a moment)...")
    observations_df = generate_observations(stations_df)
    observations_df.to_csv('mbv_africa/data/portfolio_observations.csv', index=False)
    
    print("Portfolio data generation complete.")
    print(f"Stations saved to mbv_africa/data/portfolio_stations.csv")
    print(f"Observations saved to mbv_africa/data/portfolio_observations.csv")
