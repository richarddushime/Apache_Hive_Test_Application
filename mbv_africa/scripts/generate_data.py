#!/usr/bin/env python3
"""
MBV Climate and Ocean Intelligence Africa - Data Generator
===========================================================
Unified script to generate all CSV data for Hive ingestion.

Usage:
    python generate_data.py                    # Default: ~1 million rows
    python generate_data.py --size small       # ~10,000 rows (dev/testing)
    python generate_data.py --size medium      # ~100,000 rows
    python generate_data.py --size large       # ~1,000,000 rows
    python generate_data.py --size xlarge      # ~5,000,000 rows
    python generate_data.py --rows 500000      # Custom row count
"""

import argparse
import csv
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

# =============================================================================
# Configuration
# =============================================================================

# Preset sizes (approximate total rows)
SIZE_PRESETS = {
    'small':  {'stations': 100,  'obs_per_station': 50,   'climate': 1000,   'ocean': 1000},
    'medium': {'stations': 500,  'obs_per_station': 150,  'climate': 10000,  'ocean': 10000},
    'large':  {'stations': 2500, 'obs_per_station': 380,  'climate': 25000,  'ocean': 25000},
    'xlarge': {'stations': 5000, 'obs_per_station': 950,  'climate': 100000, 'ocean': 100000},
}

# Geographic constants
REGIONS = ['East', 'West', 'North', 'South', 'Central']

COUNTRIES_BY_REGION = {
    'East':    ['KE', 'TZ', 'UG', 'ET', 'SO', 'RW', 'BI', 'DJ', 'ER'],
    'West':    ['NG', 'GH', 'SN', 'CI', 'ML', 'BF', 'NE', 'GN', 'BJ', 'TG'],
    'North':   ['EG', 'MA', 'DZ', 'TN', 'LY', 'SD', 'MR'],
    'South':   ['ZA', 'NA', 'BW', 'ZW', 'MZ', 'ZM', 'AO', 'MW', 'LS', 'SZ'],
    'Central': ['CD', 'GA', 'CM', 'CF', 'CG', 'TD', 'GQ', 'ST']
}

# Coordinate ranges by region (latitude, longitude)
LAT_RANGES = {
    'North': (15, 37), 'South': (-35, -10), 'East': (-10, 15),
    'West': (5, 20), 'Central': (-5, 10)
}
LON_RANGES = {
    'North': (-17, 35), 'South': (10, 40), 'East': (30, 51),
    'West': (-17, 15), 'Central': (8, 30)
}

# Temperature baselines by region (Celsius)
BASE_TEMPS = {
    'Central': 28, 'West': 27, 'East': 24, 'North': 22, 'South': 18
}

# Output directory
OUTPUT_DIR = Path(__file__).parent.parent / 'data'


# =============================================================================
# Data Generators
# =============================================================================

def generate_stations(count: int) -> pd.DataFrame:
    """
    Generate weather station metadata.
    
    Args:
        count: Number of stations to generate
        
    Returns:
        DataFrame with station data
    """
    print(f"  Generating {count:,} weather stations...")
    
    stations = []
    for i in range(count):
        region = np.random.choice(REGIONS)
        country = np.random.choice(COUNTRIES_BY_REGION[region])
        station_id = f"{country}-{region[:3].upper()}-{i:05d}"
        
        lat = round(np.random.uniform(*LAT_RANGES[region]), 4)
        lon = round(np.random.uniform(*LON_RANGES[region]), 4)
        
        stations.append({
            'station_id': station_id,
            'station_name': f"Station {station_id}",
            'country': country,
            'region': region,
            'latitude': lat,
            'longitude': lon,
            'elevation': round(np.random.uniform(0, 3000), 1),
            'is_coastal': np.random.random() < 0.3,
            'is_active': np.random.random() < 0.95
        })
    
    return pd.DataFrame(stations)


def generate_observations(stations_df: pd.DataFrame, rows_per_station: int, output_file: Path):
    """
    Generate climate observations with batch writing for memory efficiency.
    
    Args:
        stations_df: DataFrame of stations
        rows_per_station: Observations per station
        output_file: Path to output CSV
    """
    total_expected = len(stations_df) * rows_per_station
    print(f"  Generating {total_expected:,} observations...")
    
    # Pre-generate date range (1980-2024)
    date_range = pd.date_range(start='1980-01-01', end='2024-12-31', freq='D')
    
    # Write CSV header
    fieldnames = [
        'station_id', 'observation_date', 'year', 'month',
        'temp_max', 'temp_min', 'temp_mean', 'precipitation',
        'humidity', 'sea_surface_temp', 'ocean_salinity', 'region'
    ]
    
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        rows_written = 0
        batch = []
        batch_size = 50000
        
        for idx, station in stations_df.iterrows():
            if idx % 500 == 0 and idx > 0:
                print(f"    Processing station {idx + 1:,}/{len(stations_df):,}...")
            
            # Random sample of dates
            selected_dates = np.random.choice(date_range, size=rows_per_station, replace=False)
            
            # Base temperature for region
            base_temp = BASE_TEMPS.get(station['region'], 25)
            
            # Vectorized generation
            temps_mean = base_temp + np.random.uniform(-10, 15, rows_per_station)
            temps_max = temps_mean + np.random.uniform(2, 8, rows_per_station)
            temps_min = temps_mean - np.random.uniform(2, 8, rows_per_station)
            
            precip_base = 100 if station['region'] in ['Central', 'East'] else 30
            precipitations = np.clip(np.random.exponential(precip_base / 3, rows_per_station), 0, 500)
            
            humidities = np.random.uniform(40, 95, rows_per_station)
            
            # Ocean data for coastal stations
            is_coastal = station['is_coastal']
            if is_coastal:
                ssts = np.random.uniform(18, 28, rows_per_station)
                salinities = np.random.uniform(33, 37, rows_per_station)
            
            for i, date in enumerate(selected_dates):
                ts = pd.Timestamp(date)
                row = {
                    'station_id': station['station_id'],
                    'observation_date': ts.strftime('%Y-%m-%d'),
                    'year': ts.year,
                    'month': ts.month,
                    'temp_max': round(temps_max[i], 1),
                    'temp_min': round(temps_min[i], 1),
                    'temp_mean': round(temps_mean[i], 1),
                    'precipitation': round(precipitations[i], 1),
                    'humidity': round(humidities[i], 1),
                    'sea_surface_temp': round(ssts[i], 1) if is_coastal else '',
                    'ocean_salinity': round(salinities[i], 1) if is_coastal else '',
                    'region': station['region']
                }
                batch.append(row)
                
                if len(batch) >= batch_size:
                    writer.writerows(batch)
                    rows_written += len(batch)
                    batch = []
        
        # Write remaining
        if batch:
            writer.writerows(batch)
            rows_written += len(batch)
    
    return rows_written


def generate_climate_data(rows: int) -> pd.DataFrame:
    """
    Generate simple climate data table.
    
    Args:
        rows: Number of rows to generate
        
    Returns:
        DataFrame with climate data
    """
    print(f"  Generating {rows:,} climate data rows...")
    
    date_range = pd.date_range(start='2020-01-01', end='2024-12-31', freq='D')
    dates = np.random.choice(date_range, size=rows)
    regions = np.random.choice(REGIONS, size=rows)
    
    return pd.DataFrame({
        'date': [pd.Timestamp(d).strftime('%Y-%m-%d') for d in dates],
        'region': regions,
        'temperature': np.round(np.random.uniform(15.0, 45.0, rows), 2),
        'rainfall': np.round(np.random.uniform(0.0, 200.0, rows), 2),
        'humidity': np.round(np.random.uniform(20.0, 95.0, rows), 2)
    })


def generate_ocean_data(rows: int) -> pd.DataFrame:
    """
    Generate ocean monitoring data table.
    
    Args:
        rows: Number of rows to generate
        
    Returns:
        DataFrame with ocean data
    """
    print(f"  Generating {rows:,} ocean data rows...")
    
    date_range = pd.date_range(start='2020-01-01', end='2024-12-31', freq='D')
    dates = np.random.choice(date_range, size=rows)
    regions = np.random.choice(REGIONS, size=rows)
    
    return pd.DataFrame({
        'date': [pd.Timestamp(d).strftime('%Y-%m-%d') for d in dates],
        'region': regions,
        'sea_surface_temp': np.round(np.random.uniform(10.0, 30.0, rows), 2),
        'ph_level': np.round(np.random.uniform(7.8, 8.4, rows), 2),
        'salinity': np.round(np.random.uniform(32.0, 38.0, rows), 2)
    })


# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Generate CSV data for MBV Africa Hive ingestion',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_data.py                  # Default large dataset (~1M rows)
  python generate_data.py --size small     # Small dataset for testing
  python generate_data.py --rows 500000    # Custom ~500K observations
        """
    )
    parser.add_argument(
        '--size', 
        choices=['small', 'medium', 'large', 'xlarge'],
        default='large',
        help='Preset dataset size (default: large)'
    )
    parser.add_argument(
        '--rows',
        type=int,
        help='Custom number of observations (overrides --size for observations)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        help='Output directory (default: mbv_africa/data/)'
    )
    
    args = parser.parse_args()
    
    # Get configuration
    config = SIZE_PRESETS[args.size].copy()
    
    # Override observations if custom rows specified
    if args.rows:
        config['obs_per_station'] = max(1, args.rows // config['stations'])
    
    output_dir = Path(args.output_dir) if args.output_dir else OUTPUT_DIR
    
    # Print header
    print("=" * 60)
    print("MBV Africa - Climate Data Generator")
    print("=" * 60)
    print(f"Configuration: {args.size}")
    print(f"  Stations:           {config['stations']:,}")
    print(f"  Obs/Station:        {config['obs_per_station']:,}")
    print(f"  Climate rows:       {config['climate']:,}")
    print(f"  Ocean rows:         {config['ocean']:,}")
    expected_total = (
        config['stations'] + 
        config['stations'] * config['obs_per_station'] + 
        config['climate'] + 
        config['ocean']
    )
    print(f"  Expected total:     ~{expected_total:,} rows")
    print(f"  Output directory:   {output_dir}")
    print("=" * 60)
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Track totals
    totals = {}
    
    # 1. Generate stations
    print("\n[1/4] Weather Stations")
    stations_df = generate_stations(config['stations'])
    stations_file = output_dir / 'portfolio_stations.csv'
    stations_df.to_csv(stations_file, index=False)
    totals['portfolio_stations'] = len(stations_df)
    print(f"  ✓ Saved to {stations_file}")
    
    # 2. Generate observations
    print("\n[2/4] Portfolio Observations")
    observations_file = output_dir / 'portfolio_observations.csv'
    obs_count = generate_observations(stations_df, config['obs_per_station'], observations_file)
    totals['portfolio_observations'] = obs_count
    print(f"  ✓ Saved to {observations_file}")
    
    # 3. Generate climate data
    print("\n[3/4] Climate Data")
    climate_df = generate_climate_data(config['climate'])
    climate_file = output_dir / 'climate_data.csv'
    climate_df.to_csv(climate_file, index=False)
    totals['climate_data'] = len(climate_df)
    print(f"  ✓ Saved to {climate_file}")
    
    # 4. Generate ocean data
    print("\n[4/4] Ocean Data")
    ocean_df = generate_ocean_data(config['ocean'])
    ocean_file = output_dir / 'ocean_data.csv'
    ocean_df.to_csv(ocean_file, index=False)
    totals['ocean_data'] = len(ocean_df)
    print(f"  ✓ Saved to {ocean_file}")
    
    # Summary
    total_rows = sum(totals.values())
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for table, count in totals.items():
        print(f"  {table:25} {count:>12,} rows")
    print("  " + "-" * 40)
    print(f"  {'TOTAL':25} {total_rows:>12,} rows")
    print("=" * 60)
    
    # File sizes
    print("\nFile Sizes:")
    for f in output_dir.glob('*.csv'):
        size_mb = f.stat().st_size / (1024 * 1024)
        print(f"  {f.name:30} {size_mb:>8.2f} MB")
    
    print("\n✓ Data generation complete!")
    print(f"\nNext step: Run ./ingest_data.sh to load into Hive")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
