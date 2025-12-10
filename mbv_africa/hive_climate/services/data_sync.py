"""
Data Sync Service
Synchronizes data from Apache Hive to Django database
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from django.db import transaction
from django.utils import timezone

from hive_climate.models import Region, WeatherStation, ClimateObservation, DataImportLog
from hive_climate.hive_connector import get_hive_manager

logger = logging.getLogger(__name__)


class DataSyncService:
    """Service to synchronize data from Hive to Django database"""
    
    def __init__(self):
        self.hive = get_hive_manager()
        self.import_log = None
    
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
            logger.info("Full synchronization completed successfully")
            
        except Exception as e:
            logger.error(f"Full synchronization failed: {str(e)}")
            overall_stats['error'] = str(e)
            raise
        
        return overall_stats
