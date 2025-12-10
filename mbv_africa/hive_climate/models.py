from django.db import models
from django.contrib.auth.models import User


class Region(models.Model):
    """Geographic regions for climate data"""
    name = models.CharField(max_length=50, unique=True)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class WeatherStation(models.Model):
    """Weather stations collecting climate data"""
    station_id = models.CharField(max_length=50, unique=True, db_index=True)
    station_name = models.CharField(max_length=200)
    country = models.CharField(max_length=2, help_text="ISO 3166 country code")
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='stations')
    latitude = models.FloatField()
    longitude = models.FloatField()
    elevation = models.FloatField(null=True, blank=True, help_text="Elevation in meters")
    is_coastal = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['country', 'station_name']
        indexes = [
            models.Index(fields=['country', 'region']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.station_name} ({self.station_id})"


class ClimateObservation(models.Model):
    """Climate and ocean observations from weather stations"""
    station = models.ForeignKey(WeatherStation, on_delete=models.CASCADE, related_name='observations')
    observation_date = models.DateField(db_index=True)
    year = models.IntegerField(db_index=True)
    month = models.IntegerField()
    
    # Temperature data
    temp_max = models.FloatField(null=True, blank=True, help_text="Maximum temperature (°C)")
    temp_min = models.FloatField(null=True, blank=True, help_text="Minimum temperature (°C)")
    temp_mean = models.FloatField(null=True, blank=True, help_text="Mean temperature (°C)")
    
    # Precipitation and humidity
    precipitation = models.FloatField(null=True, blank=True, help_text="Precipitation (mm)")
    humidity = models.FloatField(null=True, blank=True, help_text="Relative humidity (%)")
    
    # Ocean data (for coastal stations)
    sea_surface_temp = models.FloatField(null=True, blank=True, help_text="Sea surface temperature (°C)")
    ocean_salinity = models.FloatField(null=True, blank=True, help_text="Ocean salinity (PSU)")
    
    # Metadata
    data_quality = models.CharField(max_length=20, default='good', choices=[
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-observation_date']
        unique_together = ['station', 'observation_date']
        indexes = [
            models.Index(fields=['year', 'month']),
            models.Index(fields=['observation_date', 'station']),
            models.Index(fields=['station', 'year']),
        ]
    
    def __str__(self):
        return f"{self.station.station_id} - {self.observation_date}"


class DataImportLog(models.Model):
    """Track data imports from Hive"""
    import_type = models.CharField(max_length=50, choices=[
        ('full', 'Full Import'),
        ('incremental', 'Incremental'),
        ('manual', 'Manual'),
    ])
    source = models.CharField(max_length=100, default='hive')
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ], default='running')
    records_processed = models.IntegerField(default=0)
    records_imported = models.IntegerField(default=0)
    records_updated = models.IntegerField(default=0)
    records_failed = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    executed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-start_time']
    
    def __str__(self):
        return f"{self.import_type} - {self.start_time.strftime('%Y-%m-%d %H:%M')} - {self.status}"
    
    @property
    def duration(self):
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None


class HiveQueryLog(models.Model):
    """Log Hive queries for auditing and optimization"""
    query = models.TextField()
    query_type = models.CharField(max_length=50, choices=[
        ('select', 'SELECT'),
        ('insert', 'INSERT'),
        ('create', 'CREATE'),
        ('other', 'Other'),
    ])
    execution_time = models.FloatField(help_text="Execution time in seconds")
    rows_returned = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('success', 'Success'),
        ('error', 'Error'),
    ])
    error_message = models.TextField(blank=True)
    executed_at = models.DateTimeField(auto_now_add=True)
    executed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-executed_at']
    
    def __str__(self):
        return f"{self.query_type} - {self.executed_at.strftime('%Y-%m-%d %H:%M:%S')}"
