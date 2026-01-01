import os
import sys
import django
import pandas as pd

# Setup Django environment
sys.path.append('/Users/rdm/Desktop/oss/upr_work/DATABASES-FOR-BIG-DATA/Apache_Hive_Test_Application/mbv_africa')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mbv_africa.settings')
django.setup()

from hive_climate.models import Region, WeatherStation

def populate_metadata():
    print("Reading portfolio_stations.csv...")
    stations_df = pd.read_csv('/Users/rdm/Desktop/oss/upr_work/DATABASES-FOR-BIG-DATA/Apache_Hive_Test_Application/mbv_africa/scripts/portfolio_stations.csv')
    
    # 1. Populate Regions
    regions = stations_df['region'].unique()
    for region_name in regions:
        region, created = Region.objects.get_or_create(
            name=region_name,
            defaults={'code': region_name[:3].upper(), 'description': f"{region_name} African Region"}
        )
        if created:
            print(f"Created region: {region_name}")

    # 2. Populate Stations
    print(f"Populating {len(stations_df)} weather stations...")
    for _, row in stations_df.iterrows():
        region = Region.objects.get(name=row['region'])
        station, created = WeatherStation.objects.get_or_create(
            station_id=row['station_id'],
            defaults={
                'station_name': row['station_name'],
                'country': row['country'],
                'region': region,
                'latitude': row['latitude'],
                'longitude': row['longitude'],
                'elevation': row['elevation'],
                'is_coastal': bool(row['is_coastal']),
                'is_active': True
            }
        )
    
    print("Django metadata population complete.")

if __name__ == "__main__":
    populate_metadata()
