"""
Models for Hive Assessment Tool
"""
from django.db import models
from django.contrib.auth.models import User
import json


class AssessmentScenario(models.Model):
    """Test scenarios for Hive performance assessment"""
    SCENARIO_TYPES = [
        ('joins', 'Large-Table JOIN Performance'),
        ('aggregation', 'Complex Aggregations'),
        ('complex_types', 'Nested JSON/Arrays'),
        ('io', 'High I/O Read'),
        ('partitioning', 'Partition Pruning'),
    ]
    
    name = models.CharField(max_length=100)
    scenario_type = models.CharField(max_length=50, choices=SCENARIO_TYPES)
    description = models.TextField()
    test_query = models.TextField(help_text="Hive SQL query to execute")
    record_count = models.BigIntegerField(default=1000000, help_text="Simulated record count")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        ordering = ['scenario_type', 'name']
    
    def __str__(self):
        return f"{self.get_scenario_type_display()} - {self.name}"


class HiveConfiguration(models.Model):
    """Hive configuration parameters for testing"""
    name = models.CharField(max_length=100)
    description = models.TextField()
    setting_key = models.CharField(max_length=200, help_text="Hive configuration key")
    setting_value = models.CharField(max_length=200, help_text="Configuration value")
    category = models.CharField(max_length=50, choices=[
        ('join', 'Join Optimization'),
        ('aggregation', 'Aggregation'),
        ('io', 'I/O Optimization'),
        ('partitioning', 'Partitioning'),
        ('execution', 'Execution Engine'),
        ('other', 'Other'),
    ])
    impact_level = models.CharField(max_length=20, choices=[
        ('high', 'High Impact'),
        ('medium', 'Medium Impact'),
        ('low', 'Low Impact'),
    ], default='medium')
    
    class Meta:
        ordering = ['category', 'name']
        unique_together = ['setting_key', 'setting_value']
    
    def __str__(self):
        return f"{self.setting_key}={self.setting_value}"


class QueryBenchmark(models.Model):
    """Results from benchmark queries"""
    scenario = models.ForeignKey(AssessmentScenario, on_delete=models.CASCADE, related_name='benchmarks')
    query_executed = models.TextField()
    execution_time = models.FloatField(help_text="Execution time in seconds")
    rows_processed = models.BigIntegerField(null=True, blank=True)
    rows_returned = models.IntegerField(null=True, blank=True)
    data_read_mb = models.FloatField(null=True, blank=True, help_text="Data read in MB")
    status = models.CharField(max_length=20, choices=[
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('timeout', 'Timeout'),
    ])
    error_message = models.TextField(blank=True)
    
    # Configuration used
    configurations_used = models.ManyToManyField(HiveConfiguration, blank=True)
    
    # Execution metadata
    executed_at = models.DateTimeField(auto_now_add=True)
    executed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        ordering = ['-executed_at']
    
    def __str__(self):
        return f"{self.scenario.name} - {self.executed_at.strftime('%Y-%m-%d %H:%M')}"


class PerformanceMetric(models.Model):
    """Detailed performance metrics"""
    benchmark = models.ForeignKey(QueryBenchmark, on_delete=models.CASCADE, related_name='metrics')
    metric_name = models.CharField(max_length=100)
    metric_value = models.FloatField()
    metric_unit = models.CharField(max_length=50, blank=True)
    target_value = models.FloatField(null=True, blank=True, help_text="Target/goal value")
    status = models.CharField(max_length=20, choices=[
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
    ], default='good')
    
    class Meta:
        ordering = ['benchmark', 'metric_name']
    
    def __str__(self):
        return f"{self.metric_name}: {self.metric_value} {self.metric_unit}"


class OptimizationRecommendation(models.Model):
    """Optimization recommendations based on benchmarks"""
    benchmark = models.ForeignKey(QueryBenchmark, on_delete=models.CASCADE, related_name='recommendations')
    configuration = models.ForeignKey(HiveConfiguration, on_delete=models.CASCADE)
    priority = models.CharField(max_length=20, choices=[
        ('critical', 'Critical'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ])
    reason = models.TextField(help_text="Why this optimization is recommended")
    expected_improvement = models.CharField(max_length=200, blank=True)
    is_applied = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_priority_display()}: {self.configuration.setting_key}"
