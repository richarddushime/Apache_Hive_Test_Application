from django.urls import path
from . import views

app_name = 'hive_climate'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
]
