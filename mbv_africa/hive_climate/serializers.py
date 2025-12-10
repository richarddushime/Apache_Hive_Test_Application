"""
Serializers for Climate Data API
"""
from rest_framework import serializers
from hive_climate.models import (
    Region, WeatherStation, ClimateObservation,
    DataImportLog, HiveQueryLog
)


class RegionSerializer(serializers.ModelSerializer):
    """Serializer for Region model"""
    station_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Region
        fields = ['id', 'name', 'code', 'description', 'station_count']
    
    def get_station_count(self, obj):
        return obj.stations.count()


class WeatherStationSerializer(serializers.ModelSerializer):
    """Serializer for WeatherStation model"""
    region_name = serializers.CharField(source='region.name', read_only=True)
    observation_count = serializers.SerializerMethodField()
    latest_observation = serializers.SerializerMethodField()
    
    class Meta:
        model = WeatherStation
        fields = [
            'id', 'station_id', 'station_name', 'country', 'region',
            'region_name', 'latitude', 'longitude', 'elevation',
            'is_coastal', 'is_active', 'created_at', 'updated_at',
            'observation_count', 'latest_observation'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_observation_count(self, obj):
        return obj.observations.count()
    
    def get_latest_observation(self, obj):
        latest = obj.observations.first()
        return latest.observation_date if latest else None


class WeatherStationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views"""
    region_name = serializers.CharField(source='region.name', read_only=True)
    
    class Meta:
        model = WeatherStation
        fields = [
            'id', 'station_id', 'station_name', 'country',
            'region_name', 'latitude', 'longitude', 'is_coastal', 'is_active'
        ]


class ClimateObservationSerializer(serializers.ModelSerializer):
    """Serializer for ClimateObservation model"""
    station_name = serializers.CharField(source='station.station_name', read_only=True)
    station_id = serializers.CharField(source='station.station_id', read_only=True)
    region = serializers.CharField(source='station.region.name', read_only=True)
    country = serializers.CharField(source='station.country', read_only=True)
    
    class Meta:
        model = ClimateObservation
        fields = [
            'id', 'station', 'station_id', 'station_name', 'region', 'country',
            'observation_date', 'year', 'month',
            'temp_max', 'temp_min', 'temp_mean',
            'precipitation', 'humidity',
            'sea_surface_temp', 'ocean_salinity',
            'data_quality', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class ClimateObservationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating observations"""
    
    class Meta:
        model = ClimateObservation
        fields = [
            'station', 'observation_date', 'year', 'month',
            'temp_max', 'temp_min', 'temp_mean',
            'precipitation', 'humidity',
            'sea_surface_temp', 'ocean_salinity', 'data_quality'
        ]
    
    def validate(self, data):
        # Ensure year and month match observation_date
        if data['observation_date']:
            if data.get('year') and data['year'] != data['observation_date'].year:
                raise serializers.ValidationError("Year must match observation date")
            if data.get('month') and data['month'] != data['observation_date'].month:
                raise serializers.ValidationError("Month must match observation date")
        return data


class TemperatureTrendSerializer(serializers.Serializer):
    """Serializer for temperature trend analytics"""
    year = serializers.IntegerField()
    region = serializers.CharField()
    avg_temp_max = serializers.FloatField()
    avg_temp_min = serializers.FloatField()
    avg_temp_mean = serializers.FloatField()
    temp_anomaly = serializers.FloatField(required=False)


class PrecipitationDataSerializer(serializers.Serializer):
    """Serializer for precipitation analytics"""
    region = serializers.CharField()
    year = serializers.IntegerField()
    month = serializers.IntegerField(required=False)
    total_precipitation = serializers.FloatField()
    avg_precipitation = serializers.FloatField()
    observation_count = serializers.IntegerField()


class OceanConditionsSerializer(serializers.Serializer):
    """Serializer for ocean conditions analytics"""
    month = serializers.CharField()
    avg_sst = serializers.FloatField()
    avg_salinity = serializers.FloatField()
    station_count = serializers.IntegerField()


class DataImportLogSerializer(serializers.ModelSerializer):
    """Serializer for DataImportLog model"""
    executed_by_username = serializers.CharField(source='executed_by.username', read_only=True)
    duration_seconds = serializers.SerializerMethodField()
    
    class Meta:
        model = DataImportLog
        fields = [
            'id', 'import_type', 'source', 'start_time', 'end_time',
            'status', 'records_processed', 'records_imported',
            'records_updated', 'records_failed', 'error_message',
            'executed_by', 'executed_by_username', 'duration_seconds'
        ]
        read_only_fields = ['start_time', 'end_time', 'duration_seconds']
    
    def get_duration_seconds(self, obj):
        return obj.duration


class HiveQueryLogSerializer(serializers.ModelSerializer):
    """Serializer for HiveQueryLog model"""
    executed_by_username = serializers.CharField(source='executed_by.username', read_only=True)
    
    class Meta:
        model = HiveQueryLog
        fields = [
            'id', 'query', 'query_type', 'execution_time', 'rows_returned',
            'status', 'error_message', 'executed_at', 'executed_by',
            'executed_by_username'
        ]
        read_only_fields = ['executed_at']


class HiveQueryExecuteSerializer(serializers.Serializer):
    """Serializer for executing Hive queries"""
    query = serializers.CharField(required=True, help_text="SQL query to execute")
    fetch_results = serializers.BooleanField(default=True, help_text="Whether to fetch query results")
    
    def validate_query(self, value):
        # Basic SQL injection prevention
        dangerous_keywords = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE']
        query_upper = value.upper()
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                raise serializers.ValidationError(
                    f"Query contains potentially dangerous keyword: {keyword}"
                )
        return value
