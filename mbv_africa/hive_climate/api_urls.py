"""
API URL Configuration for hive_climate app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from hive_climate.api_views import (
    RegionViewSet, WeatherStationViewSet, ClimateObservationViewSet,
    AnalyticsViewSet, HiveQueryViewSet, DataImportLogViewSet, HealthViewSet
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r'regions', RegionViewSet, basename='region')
router.register(r'stations', WeatherStationViewSet, basename='weatherstation')
router.register(r'observations', ClimateObservationViewSet, basename='climateobservation')
router.register(r'analytics', AnalyticsViewSet, basename='analytics')
router.register(r'hive', HiveQueryViewSet, basename='hive')
router.register(r'import-logs', DataImportLogViewSet, basename='importlog')
router.register(r'health', HealthViewSet, basename='health')

app_name = 'api'

urlpatterns = [
    # API endpoints
    path('', include(router.urls)),
    
    # JWT Authentication
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # API Documentation
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='api:schema'), name='swagger-ui'),
]
