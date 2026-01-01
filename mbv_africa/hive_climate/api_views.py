"""
API ViewSets for Climate Data
"""
from django.db.models import Avg, Sum, Count, Q, Min, Max
from django.utils import timezone
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from hive_climate.models import (
    Region, WeatherStation, ClimateObservation,
    DataImportLog, HiveQueryLog
)
from hive_climate.serializers import (
    RegionSerializer, WeatherStationSerializer, WeatherStationListSerializer,
    ClimateObservationSerializer, ClimateObservationCreateSerializer,
    TemperatureTrendSerializer, PrecipitationDataSerializer,
    OceanConditionsSerializer, DataImportLogSerializer,
    HiveQueryLogSerializer, HiveQueryExecuteSerializer
)
from hive_climate.hive_connector import get_hive_manager
import logging

logger = logging.getLogger(__name__)


class RegionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing Region data
    """
    queryset = Region.objects.all()
    serializer_class = RegionSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    @extend_schema(
        summary="Get stations in region",
        description="Retrieve all weather stations in the specified region"
    )
    @action(detail=True, methods=['get'])
    def stations(self, request, pk=None):
        """Get all stations in a region"""
        region = self.get_object()
        stations = region.stations.filter(is_active=True)
        serializer = WeatherStationListSerializer(stations, many=True)
        return Response(serializer.data)


class WeatherStationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Weather Station data
    """
    queryset = WeatherStation.objects.select_related('region').all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['country', 'region', 'is_coastal', 'is_active']
    search_fields = ['station_id', 'station_name', 'country']
    ordering_fields = ['station_name', 'country', 'created_at']
    ordering = ['station_name']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return WeatherStationListSerializer
        return WeatherStationSerializer
    
    @extend_schema(
        summary="Get recent observations",
        description="Retrieve recent climate observations for this station",
        parameters=[
            OpenApiParameter('limit', OpenApiTypes.INT, description='Number of observations to return', default=10)
        ]
    )
    @action(detail=True, methods=['get'])
    def recent_observations(self, request, pk=None):
        """Get recent observations for a station"""
        station = self.get_object()
        limit = int(request.query_params.get('limit', 10))
        observations = station.observations.order_by('-observation_date')[:limit]
        serializer = ClimateObservationSerializer(observations, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Get station statistics",
        description="Get statistical summary for this station"
    )
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Get statistics for a station"""
        station = self.get_object()
        stats = station.observations.aggregate(
            total_observations=Count('id'),
            avg_temp=Avg('temp_mean'),
            avg_precipitation=Avg('precipitation'),
            avg_humidity=Avg('humidity'),
            min_date=Min('observation_date'),
            max_date=Max('observation_date')
        )
        return Response(stats)


class ClimateObservationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Climate Observation data
    """
    queryset = ClimateObservation.objects.select_related('station', 'station__region').all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = {
        'station__country': ['exact'],
        'station__region': ['exact'],
        'year': ['exact', 'gte', 'lte'],
        'month': ['exact'],
        'observation_date': ['exact', 'gte', 'lte'],
        'data_quality': ['exact'],
    }
    ordering_fields = ['observation_date', 'year', 'month', 'temp_mean']
    ordering = ['-observation_date']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ClimateObservationCreateSerializer
        return ClimateObservationSerializer
    
    @extend_schema(
        summary="Export data",
        description="Export filtered observations as CSV or JSON",
        parameters=[
            OpenApiParameter('format', OpenApiTypes.STR, description='Export format (csv or json)', default='json')
        ]
    )
    @action(detail=False, methods=['get'])
    def export(self, request):
        """Export observations"""
        from django.http import HttpResponse
        import csv
        import json
        
        export_format = request.query_params.get('format', 'json')
        queryset = self.filter_queryset(self.get_queryset())[:1000]  # Limit exports
        
        if export_format == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="climate_data.csv"'
            
            writer = csv.writer(response)
            writer.writerow([
                'Station ID', 'Station Name', 'Country', 'Region', 'Date',
                'Temp Max', 'Temp Min', 'Temp Mean', 'Precipitation', 
                'Humidity', 'SST', 'Salinity'
            ])
            
            for obs in queryset:
                writer.writerow([
                    obs.station.station_id,
                    obs.station.station_name,
                    obs.station.country,
                    obs.station.region.name,
                    obs.observation_date,
                    obs.temp_max,
                    obs.temp_min,
                    obs.temp_mean,
                    obs.precipitation,
                    obs.humidity,
                    obs.sea_surface_temp,
                    obs.ocean_salinity,
                ])
            return response
        else:
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)


class AnalyticsViewSet(viewsets.ViewSet):
    """
    ViewSet for Analytics and Aggregated Data
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    @extend_schema(
        summary="Temperature trends by region",
        description="Get temperature trends across regions over time",
        parameters=[
            OpenApiParameter('start_year', OpenApiTypes.INT, description='Start year'),
            OpenApiParameter('end_year', OpenApiTypes.INT, description='End year'),
        ]
    )
    @action(detail=False, methods=['get'])
    def temperature_trends(self, request):
        """Get temperature trends"""
        start_year = request.query_params.get('start_year', 2015)
        end_year = request.query_params.get('end_year', 2024)
        
        trends = ClimateObservation.objects.filter(
            year__gte=start_year,
            year__lte=end_year
        ).values('year', 'station__region__name').annotate(
            avg_temp_max=Avg('temp_max'),
            avg_temp_min=Avg('temp_min'),
            avg_temp_mean=Avg('temp_mean')
        ).order_by('year', 'station__region__name')
        
        data = []
        for item in trends:
            data.append({
                'year': item['year'],
                'region': item['station__region__name'],
                'avg_temp_max': round(item['avg_temp_max'], 2) if item['avg_temp_max'] else None,
                'avg_temp_min': round(item['avg_temp_min'], 2) if item['avg_temp_min'] else None,
                'avg_temp_mean': round(item['avg_temp_mean'], 2) if item['avg_temp_mean'] else None,
            })
        
        serializer = TemperatureTrendSerializer(data, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Precipitation data",
        description="Get precipitation statistics by region"
    )
    @action(detail=False, methods=['get'])
    def precipitation(self, request):
        """Get precipitation data"""
        year = request.query_params.get('year', timezone.now().year)
        
        data = ClimateObservation.objects.filter(
            year=year,
            precipitation__isnull=False
        ).values('station__region__name').annotate(
            total_precipitation=Sum('precipitation'),
            avg_precipitation=Avg('precipitation'),
            observation_count=Count('id')
        )
        
        results = []
        for item in data:
            results.append({
                'region': item['station__region__name'],
                'year': year,
                'total_precipitation': round(item['total_precipitation'], 2),
                'avg_precipitation': round(item['avg_precipitation'], 2),
                'observation_count': item['observation_count']
            })
        
        serializer = PrecipitationDataSerializer(results, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Ocean conditions",
        description="Get ocean temperature and salinity data"
    )
    @action(detail=False, methods=['get'])
    def ocean_conditions(self, request):
        """Get ocean conditions"""
        year = request.query_params.get('year', timezone.now().year)
        
        data = ClimateObservation.objects.filter(
            year=year,
            sea_surface_temp__isnull=False
        ).values('month').annotate(
            avg_sst=Avg('sea_surface_temp'),
            avg_salinity=Avg('ocean_salinity'),
            station_count=Count('station', distinct=True)
        ).order_by('month')
        
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        results = []
        for item in data:
            results.append({
                'month': month_names[item['month'] - 1],
                'avg_sst': round(item['avg_sst'], 2),
                'avg_salinity': round(item['avg_salinity'], 2) if item['avg_salinity'] else None,
                'station_count': item['station_count']
            })
        
        serializer = OceanConditionsSerializer(results, many=True)
        return Response(serializer.data)


class HiveQueryViewSet(viewsets.ViewSet):
    """
    ViewSet for executing Hive queries (Admin only)
    """
    permission_classes = [IsAdminUser]
    
    @extend_schema(
        summary="Execute Hive query",
        description="Execute a custom Hive query (admin only)",
        request=HiveQueryExecuteSerializer,
    )
    @action(detail=False, methods=['post'])
    def execute(self, request):
        """Execute a Hive query"""
        serializer = HiveQueryExecuteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        query = serializer.validated_data['query']
        fetch_results = serializer.validated_data['fetch_results']
        
        try:
            hive = get_hive_manager()
            start_time = timezone.now()
            
            if fetch_results:
                results = hive.execute_query(query)
                execution_time = (timezone.now() - start_time).total_seconds()
                
                # Log query
                HiveQueryLog.objects.create(
                    query=query,
                    query_type='select',
                    execution_time=execution_time,
                    rows_returned=len(results) if results else 0,
                    status='success',
                    executed_by=request.user
                )
                
                return Response({
                    'success': True,
                    'rows_returned': len(results) if results else 0,
                    'execution_time': execution_time,
                    'results': results[:100]  # Limit results
                })
            else:
                hive.execute_query(query, fetch_all=False)
                execution_time = (timezone.now() - start_time).total_seconds()
                
                HiveQueryLog.objects.create(
                    query=query,
                    query_type='other',
                    execution_time=execution_time,
                    status='success',
                    executed_by=request.user
                )
                
                return Response({
                    'success': True,
                    'message': 'Query executed successfully',
                    'execution_time': execution_time
                })
                
        except Exception as e:
            logger.error(f"Hive query failed: {str(e)}")
            
            # Log failed query
            HiveQueryLog.objects.create(
                query=query,
                query_type='other',
                execution_time=0,
                status='error',
                error_message=str(e),
                executed_by=request.user
            )
            
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DataImportLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing Data Import Logs
    """
    queryset = DataImportLog.objects.all()
    serializer_class = DataImportLogSerializer
    permission_classes = [IsAuthenticated]
    ordering = ['-start_time']


class HealthViewSet(viewsets.ViewSet):
    """
    ViewSet for health checks and system status
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    @extend_schema(
        summary="System health check",
        description="Get system health status including Hive connection status and database stats"
    )
    @action(detail=False, methods=['get'], url_path='')
    def health(self, request):
        """Get system health status"""
        from hive_climate.hive_connector import is_hive_enabled, is_hive_available
        from hive_climate.services.data_sync import DataSyncService
        
        sync_service = DataSyncService()
        status_info = sync_service.get_status()
        
        return Response({
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'hive': {
                'enabled': status_info['hive_enabled'],
                'available': status_info['hive_available'],
            },
            'mode': status_info['mode'],
            'database': {
                'type': 'sqlite',
                'regions': status_info['regions_count'],
                'stations': status_info['stations_count'],
                'observations': status_info['observations_count'],
            }
        })
    
    @extend_schema(
        summary="Test Hive connection",
        description="Test the connection to Apache Hive"
    )
    @action(detail=False, methods=['get'])
    def hive_test(self, request):
        """Test Hive connection"""
        from hive_climate.hive_connector import get_hive_manager, is_hive_enabled, is_hive_available
        
        if not is_hive_enabled():
            return Response({
                'success': False,
                'message': 'Hive integration is disabled',
                'hive_enabled': False,
            })
        
        try:
            hive = get_hive_manager()
            is_connected = hive.is_available()
            
            if is_connected:
                # Get additional info
                databases = hive.get_databases()
                return Response({
                    'success': True,
                    'message': 'Successfully connected to Hive',
                    'hive_enabled': True,
                    'host': hive.host,
                    'port': hive.port,
                    'databases': databases,
                })
            else:
                return Response({
                    'success': False,
                    'message': 'Could not connect to Hive',
                    'hive_enabled': True,
                    'host': hive.host,
                    'port': hive.port,
                })
                
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Hive connection failed: {str(e)}',
                'hive_enabled': True,
            })
