"""
Django management command to load sample data from CSV files into SQLite
Use this when Hive is unavailable for development/demo purposes
"""
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from pathlib import Path

from hive_climate.services.data_sync import DataSyncService


class Command(BaseCommand):
    help = 'Load sample data from CSV files into SQLite database (fallback mode)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--data-dir',
            type=str,
            help='Directory containing CSV files (defaults to settings.DATA_DIR)',
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit number of observations to load',
        )
        parser.add_argument(
            '--stations-only',
            action='store_true',
            help='Only load station data (skip observations)',
        )
        parser.add_argument(
            '--observations-only',
            action='store_true',
            help='Only load observation data (assumes stations exist)',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before loading',
        )

    def handle(self, *args, **options):
        data_dir = options.get('data_dir')
        if data_dir:
            data_dir = Path(data_dir)
        else:
            data_dir = getattr(settings, 'DATA_DIR', None)
        
        if data_dir is None or not data_dir.exists():
            self.stderr.write(
                self.style.ERROR(f'Data directory not found: {data_dir}')
            )
            self.stdout.write('Please ensure CSV files are in the data/ directory:')
            self.stdout.write('  - portfolio_stations.csv')
            self.stdout.write('  - portfolio_observations.csv')
            return
        
        self.stdout.write(f'Loading sample data from: {data_dir}')
        
        # Clear data if requested
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            from hive_climate.models import ClimateObservation, WeatherStation, Region
            ClimateObservation.objects.all().delete()
            WeatherStation.objects.all().delete()
            Region.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Data cleared'))
        
        sync_service = DataSyncService()
        
        # Ensure regions exist
        self.stdout.write('Creating regions...')
        regions_stats = sync_service.sync_regions()
        self.stdout.write(
            f"Regions: {regions_stats['created']} created, {regions_stats['updated']} updated"
        )
        
        # Load stations
        if not options['observations_only']:
            stations_file = data_dir / 'portfolio_stations.csv'
            if stations_file.exists():
                self.stdout.write(f'Loading stations from {stations_file}...')
                stats = sync_service._load_stations_from_csv(stations_file)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Stations: {stats['created']} created, "
                        f"{stats['updated']} updated, {stats['errors']} errors"
                    )
                )
            else:
                self.stderr.write(
                    self.style.WARNING(f'Stations file not found: {stations_file}')
                )
        
        # Load observations
        if not options['stations_only']:
            observations_file = data_dir / 'portfolio_observations.csv'
            if observations_file.exists():
                limit = options.get('limit')
                self.stdout.write(
                    f'Loading observations from {observations_file}...'
                    + (f' (limit: {limit})' if limit else '')
                )
                stats = sync_service._load_observations_from_csv(observations_file, limit=limit)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Observations: {stats['created']} created, "
                        f"{stats['skipped']} skipped, {stats['errors']} errors"
                    )
                )
            else:
                self.stderr.write(
                    self.style.WARNING(f'Observations file not found: {observations_file}')
                )
        
        # Show summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Sample data loading complete!'))
        
        status = sync_service.get_status()
        self.stdout.write(f"Database now contains:")
        self.stdout.write(f"  - {status['regions_count']} regions")
        self.stdout.write(f"  - {status['stations_count']} weather stations")
        self.stdout.write(f"  - {status['observations_count']} climate observations")
