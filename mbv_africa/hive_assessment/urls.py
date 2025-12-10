"""
URL Configuration for hive_assessment app
"""
from django.urls import path
from hive_assessment import views

app_name = 'hive_assessment'

urlpatterns = [
    path('', views.assessment_dashboard, name='dashboard'),
    path('run/', views.run_assessment, name='run_assessment'),
    path('results/<int:benchmark_id>/', views.get_benchmark_results, name='benchmark_results'),
    path('history/', views.benchmark_history, name='history'),
]
