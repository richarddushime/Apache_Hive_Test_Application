"""
Admin configuration for Hive Assessment
"""
from django.contrib import admin
from hive_assessment.models import (
    AssessmentScenario, HiveConfiguration, QueryBenchmark,
    PerformanceMetric, OptimizationRecommendation
)


@admin.register(AssessmentScenario)
class AssessmentScenarioAdmin(admin.ModelAdmin):
    list_display = ['name', 'scenario_type', 'record_count', 'is_active', 'created_at']
    list_filter = ['scenario_type', 'is_active']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(HiveConfiguration)
class HiveConfigurationAdmin(admin.ModelAdmin):
    list_display = ['setting_key', 'setting_value', 'category', 'impact_level']
    list_filter = ['category', 'impact_level']
    search_fields = ['setting_key', 'description']


@admin.register(QueryBenchmark)
class QueryBenchmarkAdmin(admin.ModelAdmin):
    list_display = ['scenario', 'execution_time', 'status', 'executed_at', 'executed_by']
    list_filter = ['status', 'executed_at']
    readonly_fields = ['executed_at']
    filter_horizontal = ['configurations_used']


@admin.register(PerformanceMetric)
class PerformanceMetricAdmin(admin.ModelAdmin):
    list_display = ['benchmark', 'metric_name', 'metric_value', 'metric_unit', 'status']
    list_filter = ['status', 'metric_name']


@admin.register(OptimizationRecommendation)
class OptimizationRecommendationAdmin(admin.ModelAdmin):
    list_display = ['benchmark', 'configuration', 'priority', 'is_applied', 'created_at']
    list_filter = ['priority', 'is_applied']
    readonly_fields = ['created_at']
