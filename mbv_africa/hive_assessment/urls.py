"""
URL Configuration for hive_assessment app
"""
from django.urls import path
from hive_assessment import views

app_name = 'hive_assessment'

urlpatterns = [
    # Dashboard views
    path('', views.assessment_dashboard, name='dashboard'),
    path('run/', views.run_assessment, name='run_assessment'),
    path('results/<int:benchmark_id>/', views.get_benchmark_results, name='benchmark_results'),
    path('history/', views.benchmark_history, name='history'),
    
    # API endpoints
    path('api/status/', views.api_status, name='api_status'),
    path('api/scenarios/', views.api_scenarios, name='api_scenarios'),
    path('api/quick-check/', views.api_quick_check, name='api_quick_check'),
    path('api/recommendations/', views.api_recommendations, name='api_recommendations'),
    path('api/load-scenarios/', views.load_sample_scenarios, name='load_scenarios'),
    path('api/metrics/', views.api_full_metrics, name='api_full_metrics'),
    path('api/query/', views.api_hive_query, name='api_hive_query'),
]
