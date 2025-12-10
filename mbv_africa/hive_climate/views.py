from django.shortcuts import render


def dashboard_view(request):
    """Main dashboard view with all climate data context"""
    
    # Table Schema Data
    table_schema = {
        'name': 'africa_climate_observations',
        'format': 'ORC',
        'compression': 'SNAPPY',
        'partitioned_by': ['year', 'region'],
        'clustered_by': 'station_id',
        'columns': [
            {'name': 'station_id', 'type': 'STRING', 'description': 'Unique weather station identifier'},
            {'name': 'station_name', 'type': 'STRING', 'description': 'Weather station name'},
            {'name': 'country', 'type': 'STRING', 'description': 'African country code (ISO 3166)'},
            {'name': 'region', 'type': 'STRING', 'description': 'Geographic region (East, West, North, South, Central)'},
            {'name': 'latitude', 'type': 'DOUBLE', 'description': 'Station latitude coordinate'},
            {'name': 'longitude', 'type': 'DOUBLE', 'description': 'Station longitude coordinate'},
            {'name': 'observation_date', 'type': 'DATE', 'description': 'Date of observation'},
            {'name': 'year', 'type': 'INT', 'description': 'Observation year (partition key)'},
            {'name': 'month', 'type': 'INT', 'description': 'Observation month'},
            {'name': 'temp_max', 'type': 'DOUBLE', 'description': 'Maximum temperature (°C)'},
            {'name': 'temp_min', 'type': 'DOUBLE', 'description': 'Minimum temperature (°C)'},
            {'name': 'temp_mean', 'type': 'DOUBLE', 'description': 'Mean temperature (°C)'},
            {'name': 'precipitation', 'type': 'DOUBLE', 'description': 'Precipitation amount (mm)'},
            {'name': 'humidity', 'type': 'DOUBLE', 'description': 'Relative humidity (%)'},
            {'name': 'sea_surface_temp', 'type': 'DOUBLE', 'description': 'Sea surface temperature (°C) - coastal stations'},
            {'name': 'ocean_salinity', 'type': 'DOUBLE', 'description': 'Ocean salinity (PSU) - coastal stations'},
        ]
    }
    
    # Sample Climate Data
    sample_data = [
        {
            'station_id': 'KE-NAI-001',
            'station_name': 'Nairobi Wilson',
            'country': 'KE',
            'region': 'East',
            'latitude': -1.3219,
            'longitude': 36.8148,
            'observation_date': '2024-01-15',
            'year': 2024,
            'month': 1,
            'temp_max': 28.5,
            'temp_min': 14.2,
            'temp_mean': 21.4,
            'precipitation': 45.2,
            'humidity': 72.5,
            'sea_surface_temp': None,
            'ocean_salinity': None,
        },
        {
            'station_id': 'ZA-CPT-001',
            'station_name': 'Cape Town Intl',
            'country': 'ZA',
            'region': 'South',
            'latitude': -33.9648,
            'longitude': 18.6017,
            'observation_date': '2024-01-15',
            'year': 2024,
            'month': 1,
            'temp_max': 32.1,
            'temp_min': 18.7,
            'temp_mean': 25.4,
            'precipitation': 2.1,
            'humidity': 58.3,
            'sea_surface_temp': 19.8,
            'ocean_salinity': 35.2,
        },
        {
            'station_id': 'NG-LOS-001',
            'station_name': 'Lagos Murtala',
            'country': 'NG',
            'region': 'West',
            'latitude': 6.5774,
            'longitude': 3.3215,
            'observation_date': '2024-01-15',
            'year': 2024,
            'month': 1,
            'temp_max': 33.8,
            'temp_min': 24.5,
            'temp_mean': 29.2,
            'precipitation': 12.4,
            'humidity': 85.1,
            'sea_surface_temp': 28.4,
            'ocean_salinity': 34.8,
        },
        {
            'station_id': 'EG-CAI-001',
            'station_name': 'Cairo Intl',
            'country': 'EG',
            'region': 'North',
            'latitude': 30.1219,
            'longitude': 31.4056,
            'observation_date': '2024-01-15',
            'year': 2024,
            'month': 1,
            'temp_max': 19.2,
            'temp_min': 9.8,
            'temp_mean': 14.5,
            'precipitation': 8.3,
            'humidity': 62.4,
            'sea_surface_temp': None,
            'ocean_salinity': None,
        },
        {
            'station_id': 'CD-KIN-001',
            'station_name': 'Kinshasa N\'djili',
            'country': 'CD',
            'region': 'Central',
            'latitude': -4.3855,
            'longitude': 15.4446,
            'observation_date': '2024-01-15',
            'year': 2024,
            'month': 1,
            'temp_max': 31.2,
            'temp_min': 22.8,
            'temp_mean': 27.0,
            'precipitation': 142.5,
            'humidity': 89.2,
            'sea_surface_temp': None,
            'ocean_salinity': None,
        },
    ]
    
    # ETL Pipeline Steps
    pipeline_steps = [
        {
            'id': 1,
            'name': 'Raw Ingestion',
            'description': 'Parse fixed-width climate data from GHCN, ERA5, and African Met services',
            'details': ['Handle multiple data formats', 'Validate checksums', 'Log ingestion metadata'],
            'status': 'complete',
        },
        {
            'id': 2,
            'name': 'Data Cleaning',
            'description': 'Filter invalid values, handle missing data, normalize units',
            'details': [
                'Remove -9999 placeholder values',
                'Convert temperature units to Celsius',
                'Interpolate missing readings',
            ],
            'status': 'complete',
        },
        {
            'id': 3,
            'name': 'Station Metadata Join',
            'description': 'Enrich observations with station metadata (lat/lon, region, country)',
            'details': ['Broadcast join for station table', 'Add geographic classifications', 'Validate coordinates'],
            'status': 'complete',
        },
        {
            'id': 4,
            'name': 'Derived Fields',
            'description': 'Compute monthly means, anomalies, and climate indices',
            'details': ['Calculate monthly aggregations', 'Compute temperature anomalies', 'Generate drought indices'],
            'status': 'running',
        },
        {
            'id': 5,
            'name': 'ORC Partitioning',
            'description': 'Store in ORC format with SNAPPY compression, partitioned by year/region',
            'details': ['Dynamic partitioning enabled', '32 buckets by station_id', 'Column statistics generated'],
            'status': 'pending',
        },
    ]
    
    # Hive Optimizations
    optimizations = [
        {
            'name': 'Vectorized ORC Reads',
            'description': 'Enables batch processing of rows for faster query execution',
            'setting': 'SET hive.vectorized.execution.enabled = true;',
        },
        {
            'name': 'Predicate Pushdown',
            'description': 'Filters data at storage level to reduce I/O',
            'setting': 'SET hive.optimize.ppd = true;',
        },
        {
            'name': 'Cost-Based Optimizer',
            'description': 'Uses table statistics to choose optimal query plans',
            'setting': 'SET hive.cbo.enable = true;',
        },
        {
            'name': 'Dynamic Partitioning',
            'description': 'Automatically creates partitions during INSERT operations',
            'setting': 'SET hive.exec.dynamic.partition.mode = nonstrict;',
        },
    ]
    
    # ML Models
    ml_models = [
        {
            'name': 'Temperature Forecast (LSTM)',
            'type': 'Time Series Regression',
            'target': 'Next-season temperature anomaly',
            'metrics': {
                'rmse': 1.24,
                'mae': 0.98,
                'r2': 0.87,
            },
            'status': 'production',
        },
        {
            'name': 'Precipitation Predictor (XGBoost)',
            'type': 'Gradient Boosted Trees',
            'target': 'Monthly precipitation amount',
            'metrics': {
                'rmse': 28.5,
                'mae': 19.2,
                'r2': 0.79,
            },
            'status': 'production',
        },
        {
            'name': 'Extreme Event Classifier',
            'type': 'Binary Classification',
            'target': 'Heatwave / Drought detection',
            'metrics': {
                'accuracy': 0.92,
                'precision': 0.88,
                'recall': 0.85,
                'auc': 0.94,
            },
            'status': 'staging',
        },
    ]
    
    # Feature Importance
    feature_importance = [
        {'feature': 'lag_1_temp_anomaly', 'importance': 0.23},
        {'feature': 'month_sin', 'importance': 0.18},
        {'feature': 'sea_surface_temp', 'importance': 0.15},
        {'feature': 'precipitation_30d', 'importance': 0.12},
        {'feature': 'latitude', 'importance': 0.09},
        {'feature': 'enso_index', 'importance': 0.08},
        {'feature': 'humidity_avg', 'importance': 0.07},
        {'feature': 'elevation', 'importance': 0.05},
    ]
    
    # Temperature Trends Data (for charts)
    temperature_trends = [
        {'year': '2015', 'east': 0.8, 'west': 1.1, 'north': 0.6, 'south': 0.9, 'central': 1.0},
        {'year': '2016', 'east': 1.2, 'west': 1.4, 'north': 0.9, 'south': 1.1, 'central': 1.3},
        {'year': '2017', 'east': 0.9, 'west': 1.0, 'north': 0.7, 'south': 0.8, 'central': 1.1},
        {'year': '2018', 'east': 1.1, 'west': 1.3, 'north': 0.8, 'south': 1.0, 'central': 1.2},
        {'year': '2019', 'east': 1.3, 'west': 1.5, 'north': 1.0, 'south': 1.2, 'central': 1.4},
        {'year': '2020', 'east': 1.4, 'west': 1.6, 'north': 1.1, 'south': 1.3, 'central': 1.5},
        {'year': '2021', 'east': 1.2, 'west': 1.4, 'north': 0.9, 'south': 1.1, 'central': 1.3},
        {'year': '2022', 'east': 1.5, 'west': 1.7, 'north': 1.2, 'south': 1.4, 'central': 1.6},
        {'year': '2023', 'east': 1.6, 'west': 1.8, 'north': 1.3, 'south': 1.5, 'central': 1.7},
        {'year': '2024', 'east': 1.7, 'west': 1.9, 'north': 1.4, 'south': 1.6, 'central': 1.8},
    ]
    
    # Precipitation Data
    precipitation_data = [
        {'region': 'East Africa', 'actual': 892, 'predicted': 875, 'baseline': 950},
        {'region': 'West Africa', 'actual': 1245, 'predicted': 1280, 'baseline': 1320},
        {'region': 'North Africa', 'actual': 156, 'predicted': 148, 'baseline': 180},
        {'region': 'South Africa', 'actual': 478, 'predicted': 465, 'baseline': 520},
        {'region': 'Central Africa', 'actual': 1680, 'predicted': 1720, 'baseline': 1750},
    ]
    
    # Ocean Data
    ocean_data = [
        {'month': 'Jan', 'sst': 27.2, 'salinity': 35.1},
        {'month': 'Feb', 'sst': 27.8, 'salinity': 35.0},
        {'month': 'Mar', 'sst': 28.4, 'salinity': 34.9},
        {'month': 'Apr', 'sst': 28.9, 'salinity': 34.8},
        {'month': 'May', 'sst': 28.6, 'salinity': 34.9},
        {'month': 'Jun', 'sst': 27.8, 'salinity': 35.0},
        {'month': 'Jul', 'sst': 26.9, 'salinity': 35.2},
        {'month': 'Aug', 'sst': 26.2, 'salinity': 35.3},
        {'month': 'Sep', 'sst': 26.5, 'salinity': 35.2},
        {'month': 'Oct', 'sst': 27.1, 'salinity': 35.1},
        {'month': 'Nov', 'sst': 27.5, 'salinity': 35.0},
        {'month': 'Dec', 'sst': 27.3, 'salinity': 35.1},
    ]
    
    # Stats for Data Preview
    stats = {
        'total_records': '2.4M',
        'stations': '1,247',
        'countries': '54',
        'date_range': '1950 - 2024',
    }
    
    context = {
        'table_schema': table_schema,
        'sample_data': sample_data,
        'stats': stats,
        'pipeline_steps': pipeline_steps,
        'optimizations': optimizations,
        'ml_models': ml_models,
        'feature_importance': feature_importance,
        'temperature_trends': temperature_trends,
        'precipitation_data': precipitation_data,
        'ocean_data': ocean_data,
    }
    
    return render(request, 'hive_climate/dashboard.html', context)
