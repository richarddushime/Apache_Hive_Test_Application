"""
Data Sync Service
Synchronizes data from Apache Hive to Django database
With SQLite fallback support for offline development
"""
import csv
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from django.db import transaction
from django.conf import settings
from django.utils import timezone

from hive_climate.models import Region, WeatherStation, ClimateObservation, DataImportLog
from hive_climate.hive_connector import get_hive_manager, is_hive_available, is_hive_enabled

logger = logging.getLogger(__name__)


class DataSyncService:
    """Service to synchronize data from Hive to Django database"""
    
    def __init__(self):
        self.hive = None
        self.hive_available = False
        self.import_log = None
        self._check_hive_availability()
    
    def _check_hive_availability(self):
        """Check if Hive is available and initialize connection"""
        if is_hive_enabled():
            self.hive_available = is_hive_available()
            if self.hive_available:
                self.hive = get_hive_manager()
                logger.info("Hive connection available")
            else:
                logger.warning("Hive is enabled but not available - using SQLite fallback")
        else:
            logger.info("Hive is disabled - running in SQLite-only mode")
    
    def start_import_log(self, import_type='manual', user=None):
        """Create import log entry"""
        self.import_log = DataImportLog.objects.create(
            import_type=import_type,
            source='hive',
            status='running',
            executed_by=user
        )
        return self.import_log
    
    def finish_import_log(self, status='completed', error_message=''):
        """Update import log with final status"""
        if self.import_log:
            self.import_log.status = status
            self.import_log.end_time = timezone.now()
            self.import_log.error_message = error_message
            self.import_log.save()
    
    def sync_regions(self) -> Dict[str, Any]:
        """
        Sync region data from Hive
        
        Returns:
            Dictionary with sync statistics
        """
        logger.info("Syncing regions from Hive...")
        stats = {'created': 0, 'updated': 0, 'errors': 0}
        
        try:
            # Define regions (usually static, but could come from Hive)
            regions_data = [
                {'name': 'East Africa', 'code': 'EAST', 'description': 'Eastern African region'},
                {'name': 'West Africa', 'code': 'WEST', 'description': 'Western African region'},
                {'name': 'North Africa', 'code': 'NORTH', 'description': 'Northern African region'},
                {'name': 'South Africa', 'code': 'SOUTH', 'description': 'Southern African region'},
                {'name': 'Central Africa', 'code': 'CENTRAL', 'description': 'Central African region'},
            ]
            
            for region_data in regions_data:
                region, created = Region.objects.update_or_create(
                    code=region_data['code'],
                    defaults={
                        'name': region_data['name'],
                        'description': region_data['description']
                    }
                )
                if created:
                    stats['created'] += 1
                else:
                    stats['updated'] += 1
            
            logger.info(f"Region sync completed: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error syncing regions: {str(e)}")
            stats['errors'] += 1
            return stats
    
    def sync_weather_stations(self, table_name='africa_climate_observations') -> Dict[str, Any]:
        """
        Sync weather station data from Hive
        
        Args:
            table_name: Hive table name
            
        Returns:
            Dictionary with sync statistics
        """
        logger.info(f"Syncing weather stations from Hive table: {table_name}...")
        stats = {'created': 0, 'updated': 0, 'errors': 0}
        
        if not self.hive_available:
            logger.warning("Hive not available - skipping station sync from Hive")
            return stats
        
        try:
            # Query to get distinct stations from Hive
            query = f"""
                SELECT DISTINCT 
                    station_id,
                    station_name,
                    country,
                    region,
                    latitude,
                    longitude,
                    MAX(sea_surface_temp) as has_ocean_data
                FROM {table_name}
                GROUP BY station_id, station_name, country, region, latitude, longitude
            """
            
            df = self.hive.execute_query_to_dataframe(query)
            
            for _, row in df.iterrows():
                try:
                    # Find region
                    region_obj = Region.objects.filter(name__iexact=row['region']).first()
                    if not region_obj:
                        logger.warning(f"Region not found for station {row['station_id']}: {row['region']}")
                        # Create a default region if needed
                        region_obj, _ = Region.objects.get_or_create(
                            code=row['region'].upper()[:10],
                            defaults={'name': row['region']}
                        )
                    
                    # Create or update station
                    station, created = WeatherStation.objects.update_or_create(
                        station_id=row['station_id'],
                        defaults={
                            'station_name': row['station_name'],
                            'country': row['country'],
                            'region': region_obj,
                            'latitude': float(row['latitude']),
                            'longitude': float(row['longitude']),
                            'is_coastal': row['has_ocean_data'] is not None and row['has_ocean_data'] != ''
                        }
                    )
                    
                    if created:
                        stats['created'] += 1
                    else:
                        stats['updated'] += 1
                        
                except Exception as e:
                    logger.error(f"Error processing station {row['station_id']}: {str(e)}")
                    stats['errors'] += 1
            
            logger.info(f"Weather station sync completed: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error syncing weather stations: {str(e)}")
            raise
    
    def sync_climate_observations(self, table_name='africa_climate_observations', 
                                  start_date=None, end_date=None, 
                                  limit=None) -> Dict[str, Any]:
        """
        Sync climate observations from Hive
        
        Args:
            table_name: Hive table name
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            limit: Optional limit on number of records
            
        Returns:
            Dictionary with sync statistics
        """
        logger.info(f"Syncing climate observations from Hive table: {table_name}...")
        stats = {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}
        
        if not self.hive_available:
            logger.warning("Hive not available - skipping observations sync from Hive")
            return stats
        
        try:
            # Build query
            query = f"""
                SELECT 
                    station_id,
                    observation_date,
                    year,
                    month,
                    temp_max,
                    temp_min,
                    temp_mean,
                    precipitation,
                    humidity,
                    sea_surface_temp,
                    ocean_salinity
                FROM {table_name}
            """
            
            # Add date filters
            where_clauses = []
            if start_date:
                where_clauses.append(f"observation_date >= '{start_date}'")
            if end_date:
                where_clauses.append(f"observation_date <= '{end_date}'")
            
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
            
            query += " ORDER BY observation_date DESC"
            
            if limit:
                query += f" LIMIT {limit}"
            
            df = self.hive.execute_query_to_dataframe(query)
            logger.info(f"Retrieved {len(df)} observations from Hive")
            
            # Process in batches
            batch_size = 1000
            observations_to_create = []
            observations_to_update = []
            
            for _, row in df.iterrows():
                try:
                    # Find station
                    station = WeatherStation.objects.filter(station_id=row['station_id']).first()
                    if not station:
                        logger.warning(f"Station not found: {row['station_id']}")
                        stats['skipped'] += 1
                        continue
                    
                    # Prepare observation data
                    obs_data = {
                        'station': station,
                        'observation_date': row['observation_date'],
                        'year': int(row['year']),
                        'month': int(row['month']),
                        'temp_max': float(row['temp_max']) if row['temp_max'] is not None else None,
                        'temp_min': float(row['temp_min']) if row['temp_min'] is not None else None,
                        'temp_mean': float(row['temp_mean']) if row['temp_mean'] is not None else None,
                        'precipitation': float(row['precipitation']) if row['precipitation'] is not None else None,
                        'humidity': float(row['humidity']) if row['humidity'] is not None else None,
                        'sea_surface_temp': float(row['sea_surface_temp']) if row['sea_surface_temp'] is not None else None,
                        'ocean_salinity': float(row['ocean_salinity']) if row['ocean_salinity'] is not None else None,
                    }
                    
                    # Check if observation exists
                    existing = ClimateObservation.objects.filter(
                        station=station,
                        observation_date=row['observation_date']
                    ).first()
                    
                    if existing:
                        # Update existing
                        for key, value in obs_data.items():
                            if key != 'station':  # Don't update station FK
                                setattr(existing, key, value)
                        observations_to_update.append(existing)
                        stats['updated'] += 1
                    else:
                        # Create new
                        observations_to_create.append(ClimateObservation(**obs_data))
                        stats['created'] += 1
                    
                    # Batch insert/update
                    if len(observations_to_create) >= batch_size:
                        ClimateObservation.objects.bulk_create(observations_to_create, ignore_conflicts=True)
                        observations_to_create = []
                    
                    if len(observations_to_update) >= batch_size:
                        ClimateObservation.objects.bulk_update(
                            observations_to_update,
                            ['temp_max', 'temp_min', 'temp_mean', 'precipitation', 
                             'humidity', 'sea_surface_temp', 'ocean_salinity']
                        )
                        observations_to_update = []
                        
                except Exception as e:
                    logger.error(f"Error processing observation: {str(e)}")
                    stats['errors'] += 1
            
            # Final batch insert/update
            if observations_to_create:
                ClimateObservation.objects.bulk_create(observations_to_create, ignore_conflicts=True)
            
            if observations_to_update:
                ClimateObservation.objects.bulk_update(
                    observations_to_update,
                    ['temp_max', 'temp_min', 'temp_mean', 'precipitation', 
                     'humidity', 'sea_surface_temp', 'ocean_salinity']
                )
            
            logger.info(f"Climate observation sync completed: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error syncing climate observations: {str(e)}")
            raise
    
    def full_sync(self, limit=None) -> Dict[str, Any]:
        """
        Perform full data synchronization
        
        Args:
            limit: Optional limit on observations
            
        Returns:
            Dictionary with overall statistics
        """
        logger.info("Starting full data synchronization...")
        
        overall_stats = {
            'regions': {},
            'stations': {},
            'observations': {},
            'success': False
        }
        
        try:
            # Sync regions
            overall_stats['regions'] = self.sync_regions()
            
            # Sync weather stations
            overall_stats['stations'] = self.sync_weather_stations()
            
            # Sync climate observations
            overall_stats['observations'] = self.sync_climate_observations(limit=limit)
            
            overall_stats['success'] = True
            overall_stats['hive_available'] = self.hive_available
            logger.info("Full synchronization completed successfully")
            
        except Exception as e:
            logger.error(f"Full synchronization failed: {str(e)}")
            overall_stats['error'] = str(e)
            raise
        
        return overall_stats
    
    def load_sample_data_from_csv(self, data_dir: Path = None) -> Dict[str, Any]:
        """
        Load sample data from CSV files into SQLite (fallback mode)
        Used when Hive is unavailable for development/demo purposes
        
        Args:
            data_dir: Directory containing CSV files (defaults to settings.DATA_DIR)
            
        Returns:
            Dictionary with load statistics
        """
        if data_dir is None:
            data_dir = getattr(settings, 'DATA_DIR', Path(__file__).parent.parent.parent / 'data')
        
        logger.info(f"Loading sample data from CSV files in {data_dir}...")
        stats = {
            'stations': {'created': 0, 'updated': 0, 'errors': 0},
            'observations': {'created': 0, 'updated': 0, 'errors': 0},
            'success': False
        }
        
        # First ensure regions exist
        self.sync_regions()
        
        # Load portfolio stations
        stations_file = data_dir / 'portfolio_stations.csv'
        if stations_file.exists():
            stats['stations'] = self._load_stations_from_csv(stations_file)
        else:
            logger.warning(f"Stations file not found: {stations_file}")
        
        # Load portfolio observations
        observations_file = data_dir / 'portfolio_observations.csv'
        if observations_file.exists():
            stats['observations'] = self._load_observations_from_csv(observations_file)
        else:
            logger.warning(f"Observations file not found: {observations_file}")
        
        stats['success'] = stats['stations'].get('errors', 0) == 0 and stats['observations'].get('errors', 0) == 0
        return stats
    
    def _load_stations_from_csv(self, csv_path: Path) -> Dict[str, Any]:
        """Load weather stations from CSV file"""
        stats = {'created': 0, 'updated': 0, 'errors': 0}
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        # Get or create region
                        region_name = row.get('region', 'Unknown')
                        region, _ = Region.objects.get_or_create(
                            code=region_name.upper()[:10].replace(' ', '_'),
                            defaults={'name': region_name}
                        )
                        
                        # Create or update station
                        station, created = WeatherStation.objects.update_or_create(
                            station_id=row['station_id'],
                            defaults={
                                'station_name': row.get('station_name', row['station_id']),
                                'country': row.get('country', 'Unknown'),
                                'region': region,
                                'latitude': float(row.get('latitude', 0)),
                                'longitude': float(row.get('longitude', 0)),
                                'elevation': float(row.get('elevation', 0)) if row.get('elevation') else None,
                                'is_coastal': row.get('is_coastal', '').lower() in ('true', '1', 'yes'),
                                'is_active': True
                            }
                        )
                        
                        if created:
                            stats['created'] += 1
                        else:
                            stats['updated'] += 1
                            
                    except Exception as e:
                        logger.error(f"Error loading station {row.get('station_id')}: {e}")
                        stats['errors'] += 1
        
        except Exception as e:
            logger.error(f"Error reading stations CSV: {e}")
            stats['errors'] += 1
        
        logger.info(f"Loaded stations from CSV: {stats}")
        return stats
    
    def _load_observations_from_csv(self, csv_path: Path, limit: int = None) -> Dict[str, Any]:
        """Load climate observations from CSV file"""
        stats = {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}
        observations_to_create = []
        batch_size = 1000
        count = 0
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if limit and count >= limit:
                        break
                    
                    try:
                        # Find station
                        station = WeatherStation.objects.filter(station_id=row['station_id']).first()
                        if not station:
                            stats['skipped'] += 1
                            continue
                        
                        # Parse date
                        obs_date = row.get('observation_date', row.get('date_col', ''))
                        if not obs_date:
                            stats['skipped'] += 1
                            continue
                        
                        # Parse year and month
                        try:
                            date_obj = datetime.strptime(obs_date.split()[0], '%Y-%m-%d')
                            year = int(row.get('year', date_obj.year))
                            month = int(row.get('month', date_obj.month))
                        except:
                            year = int(row.get('year', 2024))
                            month = int(row.get('month', 1))
                        
                        # Create observation object
                        obs = ClimateObservation(
                            station=station,
                            observation_date=obs_date.split()[0],
                            year=year,
                            month=month,
                            temp_max=float(row['temp_max']) if row.get('temp_max') else None,
                            temp_min=float(row['temp_min']) if row.get('temp_min') else None,
                            temp_mean=float(row['temp_mean']) if row.get('temp_mean') else None,
                            precipitation=float(row['precipitation']) if row.get('precipitation') else None,
                            humidity=float(row['humidity']) if row.get('humidity') else None,
                            sea_surface_temp=float(row['sea_surface_temp']) if row.get('sea_surface_temp') else None,
                            ocean_salinity=float(row['ocean_salinity']) if row.get('ocean_salinity') else None,
                        )
                        observations_to_create.append(obs)
                        count += 1
                        
                        # Batch insert
                        if len(observations_to_create) >= batch_size:
                            ClimateObservation.objects.bulk_create(observations_to_create, ignore_conflicts=True)
                            stats['created'] += len(observations_to_create)
                            observations_to_create = []
                            
                    except Exception as e:
                        logger.error(f"Error loading observation: {e}")
                        stats['errors'] += 1
            
            # Final batch
            if observations_to_create:
                ClimateObservation.objects.bulk_create(observations_to_create, ignore_conflicts=True)
                stats['created'] += len(observations_to_create)
        
        except Exception as e:
            logger.error(f"Error reading observations CSV: {e}")
            stats['errors'] += 1
        
        logger.info(f"Loaded observations from CSV: {stats}")
        return stats
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current sync service status
        
        Returns:
            Dictionary with service status information
        """
        return {
            'hive_enabled': is_hive_enabled(),
            'hive_available': self.hive_available,
            'mode': 'hive' if self.hive_available else 'sqlite_fallback',
            'regions_count': Region.objects.count(),
            'stations_count': WeatherStation.objects.count(),
            'observations_count': ClimateObservation.objects.count(),
        }
