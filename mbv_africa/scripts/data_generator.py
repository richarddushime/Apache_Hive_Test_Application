import csv
import random
import datetime

REGIONS = ['North', 'South', 'East', 'West', 'Central']
START_DATE = datetime.date(2023, 1, 1)

def generate_weather_data(filename='climate_data.csv', rows=1000):
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['date', 'region', 'temperature', 'rainfall', 'humidity']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for _ in range(rows):
            date = START_DATE + datetime.timedelta(days=random.randint(0, 365))
            region = random.choice(REGIONS)
            temp = round(random.uniform(15.0, 45.0), 2)
            rainfall = round(random.uniform(0.0, 50.0), 2)
            humidity = round(random.uniform(20.0, 90.0), 2)
            
            writer.writerow({
                'date': date,
                'region': region,
                'temperature': temp,
                'rainfall': rainfall,
                'humidity': humidity
            })
    print(f"Generated {rows} rows of weather data in {filename}")

def generate_ocean_data(filename='ocean_data.csv', rows=1000):
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['date', 'region', 'sea_surface_temp', 'ph_level', 'salinity']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for _ in range(rows):
            date = START_DATE + datetime.timedelta(days=random.randint(0, 365))
            region = random.choice(REGIONS)
            sst = round(random.uniform(10.0, 30.0), 2)
            ph = round(random.uniform(7.8, 8.4), 2)
            salinity = round(random.uniform(32.0, 38.0), 2)
            
            writer.writerow({
                'date': date,
                'region': region,
                'sea_surface_temp': sst,
                'ph_level': ph,
                'salinity': salinity
            })
    print(f"Generated {rows} rows of ocean data in {filename}")

if __name__ == '__main__':
    generate_weather_data()
    generate_ocean_data()
