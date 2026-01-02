"""
Django management command to sync data from Hive
Usage: python manage.py sync_hive_data [--full | --regions | --stations | --observations] [options]
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from hive_climate.services.data_sync import DataSyncService
from hive_climate.hive_connector import get_hive_manager


class Command(BaseCommand):
    help = 'Synchronize climate data from Apache Hive to Django database'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--full',
            action='store_true',
            help='Perform full synchronization (regions, stations, and observations)'
        )
        parser.add_argument(
            '--regions',
            action='store_true',
            help='Sync only regions'
        )
        parser.add_argument(
            '--stations',
            action='store_true',
            help='Sync only weather stations'
        )
        parser.add_argument(
            '--observations',
            action='store_true',
            help='Sync only climate observations'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit number of observations to sync'
        )
        parser.add_argument(
            '--start-date',
            type=str,
            default=None,
            help='Start date for observations (YYYY-MM-DD)'
        )
        parser.add_argument(
            '--end-date',
            type=str,
            default=None,
            help='End date for observations (YYYY-MM-DD)'
        )
        parser.add_argument(
            '--test-connection',
            action='store_true',
            help='Test Hive connection without syncing data'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('Hive Data Synchronization Tool'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        
        # Test connection if requested
        if options['test_connection']:
            self.test_hive_connection()
            return
        
        # Initialize sync service
        sync_service = DataSyncService()
        
        # Start import log
        import_type = 'full' if options['full'] else 'incremental'
        import_log = sync_service.start_import_log(import_type=import_type)
        
        self.stdout.write(f"Import log ID: {import_log.id}")
        self.stdout.write(f"Started at: {timezone.now()}\n")
        
        try:
            # Determine what to sync
            if options['full']:
                self.stdout.write(self.style.WARNING('Performing FULL synchronization...'))
                stats = sync_service.full_sync(limit=options['limit'])
                self.print_full_stats(stats)
                
            elif options['regions']:
                self.stdout.write(self.style.WARNING('Syncing regions...'))
                stats = sync_service.sync_regions()
                self.print_stats('Regions', stats)
                
            elif options['stations']:
                self.stdout.write(self.style.WARNING('Syncing weather stations...'))
                stats = sync_service.sync_weather_stations()
                self.print_stats('Weather Stations', stats)
                
            elif options['observations']:
                self.stdout.write(self.style.WARNING('Syncing climate observations...'))
                stats = sync_service.sync_climate_observations(
                    start_date=options['start_date'],
                    end_date=options['end_date'],
                    limit=options['limit']
                )
                self.print_stats('Climate Observations', stats)
                
            else:
                self.stdout.write(self.style.ERROR('No sync option specified. Use --help for available options.'))
                return
            
            # Update import log
            if 'success' in stats and stats['success']:
                # Calculate totals from nested stats
                total_created = sum(stats.get(key, {}).get('created', 0) for key in ['regions', 'stations', 'observations'])
                total_updated = sum(stats.get(key, {}).get('updated', 0) for key in ['regions', 'stations', 'observations'])
                
                import_log.records_imported = total_created
                import_log.records_updated = total_updated
                sync_service.finish_import_log(status='completed')
            else:
                import_log.records_imported = stats.get('created', 0)
                import_log.records_updated = stats.get('updated', 0)
                sync_service.finish_import_log(status='completed')
            
            self.stdout.write(self.style.SUCCESS('\n✓ Synchronization completed successfully!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n✗ Synchronization failed: {str(e)}'))
            sync_service.finish_import_log(status='failed', error_message=str(e))
            raise
        
        self.stdout.write(self.style.SUCCESS('=' * 70))
    
    def test_hive_connection(self):
        """Test connection to Hive"""
        self.stdout.write(self.style.WARNING('Testing Hive connection...'))
        
        try:
            hive = get_hive_manager()
            
            # Test basic connectivity
            if hive.test_connection():
                self.stdout.write(self.style.SUCCESS('✓ Connection successful!'))
                
                # Get databases
                databases = hive.get_databases()
                self.stdout.write(f"\nAvailable databases: {', '.join(databases)}")
                
                # Get tables in default database
                tables = hive.get_tables()
                self.stdout.write(f"Tables in default database: {', '.join(tables) if tables else 'None'}")
                
            else:
                self.stdout.write(self.style.ERROR('✗ Connection failed!'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Connection error: {str(e)}'))
    
    def print_stats(self, entity_name, stats):
        """Print statistics for a single entity type"""
        self.stdout.write(f"\n{entity_name} Statistics:")
        self.stdout.write(f"  Created: {stats.get('created', 0)}")
        self.stdout.write(f"  Updated: {stats.get('updated', 0)}")
        if 'skipped' in stats:
            self.stdout.write(f"  Skipped: {stats.get('skipped', 0)}")
        if 'errors' in stats:
            self.stdout.write(self.style.WARNING(f"  Errors:  {stats.get('errors', 0)}"))
    
    def print_full_stats(self, stats):
        """Print statistics for full synchronization"""
        if 'regions' in stats:
            self.print_stats('Regions', stats['regions'])
        if 'stations' in stats:
            self.print_stats('Weather Stations', stats['stations'])
        if 'observations' in stats:
            self.print_stats('Climate Observations', stats['observations'])
