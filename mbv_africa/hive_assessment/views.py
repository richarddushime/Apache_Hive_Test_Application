"""
Views for Hive Assessment Tool
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Avg
import time
import logging

from hive_assessment.models import (
    AssessmentScenario, QueryBenchmark, PerformanceMetric,
    HiveConfiguration, OptimizationRecommendation
)
from hive_climate.hive_connector import get_hive_manager

logger = logging.getLogger(__name__)


def assessment_dashboard(request):
    """
    Main assessment dashboard view
    """
    scenarios = AssessmentScenario.objects.filter(is_active=True)
    recent_benchmarks = QueryBenchmark.objects.select_related('scenario').order_by('-executed_at')[:10]
    
    # Get scenario types for dropdown
    scenario_choices = AssessmentScenario.SCENARIO_TYPES
    
    context = {
        'scenarios': scenarios,
        'scenario_choices': scenario_choices,
        'recent_benchmarks': recent_benchmarks,
    }
    
    return render(request, 'hive_assessment/dashboard.html', context)


def run_assessment(request):
    """
    Execute a benchmark assessment
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)
    
    scenario_id = request.POST.get('scenario_id')
    record_count = int(request.POST.get('record_count', 100000000))
    
    try:
        scenario = get_object_or_404(AssessmentScenario, id=scenario_id)
        
        # Execute Hive query
        hive = get_hive_manager()
        start_time = time.time()
        
        try:
            results = hive.execute_query(scenario.test_query)
            execution_time = time.time() - start_time
            
            # Create benchmark record
            benchmark = QueryBenchmark.objects.create(
                scenario=scenario,
                query_executed=scenario.test_query,
                execution_time=execution_time,
                rows_processed=record_count,
                rows_returned=len(results) if results else 0,
                status='success',
                executed_by=request.user if request.user.is_authenticated else None
            )
            
            # Generate performance metrics
            create_performance_metrics(benchmark, scenario.scenario_type, execution_time, record_count)
            
            # Generate optimization recommendations
            create_recommendations(benchmark, scenario.scenario_type)
            
            return JsonResponse({
                'success': True,
                'benchmark_id': benchmark.id,
                'execution_time': execution_time,
                'rows_returned': benchmark.rows_returned,
            })
            
        except Exception as e:
            #  Query failed
            logger.error(f"Benchmark query failed: {str(e)}")
            execution_time = time.time() - start_time
            
            benchmark = QueryBenchmark.objects.create(
                scenario=scenario,
                query_executed=scenario.test_query,
                execution_time=execution_time,
                status='failed',
                error_message=str(e),
                executed_by=request.user if request.user.is_authenticated else None
            )
            
            return JsonResponse({
                'success': False,
                'error': str(e),
                'execution_time': execution_time
            })
    
    except Exception as e:
        logger.error(f"Assessment failed: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


def get_benchmark_results(request, benchmark_id):
    """
    Get detailed results for a specific benchmark
    """
    benchmark = get_object_or_404(QueryBenchmark, id=benchmark_id)
    
    metrics = benchmark.metrics.all()
    recommendations = benchmark.recommendations.select_related('configuration').all()
    
    metrics_data = []
    for metric in metrics:
        metrics_data.append({
            'name': metric.metric_name,
            'value': metric.metric_value,
            'unit': metric.metric_unit,
            'target': metric.target_value,
            'status': metric.status,
        })
    
    recommendations_data = []
    for rec in recommendations:
        recommendations_data.append({
            'setting': f"{rec.configuration.setting_key}={rec.configuration.setting_value}",
            'details': rec.reason,
            'priority': rec.priority,
            'expected_improvement': rec.expected_improvement,
        })
    
    return JsonResponse({
        'scenario': benchmark.scenario.name,
        'description': benchmark.scenario.description,
        'test_query': benchmark.query_executed,
        'execution_time': benchmark.execution_time,
        'status': benchmark.status,
        'error_message': benchmark.error_message,
        'metrics': metrics_data,
        'recommendations': recommendations_data,
    })


def create_performance_metrics(benchmark, scenario_type, execution_time, record_count):
    """Create performance metrics based on scenario type"""
    
    # Define metrics based on scenario type (from index.html)
    metrics_config = {
        'joins': [
            {'name': 'Query Execution Time', 'value': execution_time * 1000, 'unit': 'ms', 'target': 2000},
            {'name': 'Spill to Disk', 'value': max(0, (execution_time - 2) * 1.25), 'unit': 'GB', 'target': 0.5},
            {'name': 'CPU Utilization', 'value': min(95, 70 + (execution_time / 10)), 'unit': '%', 'target': 95},
        ],
        'aggregation': [
            {'name': 'Query Execution Time', 'value': execution_time * 1000, 'unit': 'ms', 'target': 3500},
            {'name': 'Data Skew Ratio', 'value': max(1, execution_time / 2), 'unit': 'ratio', 'target': 1.5},
        ],
        'complex_types': [
            {'name': 'Query Execution Time', 'value': execution_time * 1000, 'unit': 'ms', 'target': 4000},
            {'name': 'Deserialization Overhead', 'value': min(30, execution_time * 5), 'unit': '%', 'target': 10},
        ],
        'io': [
            {'name': 'Query Execution Time', 'value': execution_time * 1000, 'unit': 'ms', 'target': 4500},
            {'name': 'Data Read', 'value': max(100, 500 - execution_time * 50), 'unit': 'MB/s', 'target': 300},
        ],
        'partitioning': [
            {'name': 'Query Execution Time', 'value': execution_time * 1000, 'unit': 'ms', 'target': 800},
            {'name': 'Partitions Scanned', 'value': max(1, int(execution_time / 0.5)), 'unit': 'count', 'target': 1},
        ],
    }
    
    metrics = metrics_config.get(scenario_type, [])
    
    for metric_def in metrics:
        # Determine status based on performance vs target
        value = metric_def['value']
        target = metric_def['target']
        
        if 'Time' in metric_def['name'] or 'Spill' in metric_def['name'] or 'Skew' in metric_def['name']:
            # Lower is better
            if value <= target:
                status = 'excellent'
            elif value <= target * 1.5:
                status = 'good'
            elif value <= target * 2:
                status = 'fair'
            else:
                status = 'poor'
        else:
            # Higher is better
            if value >= target:
                status = 'excellent'
            elif value >= target * 0.75:
                status = 'good'
            elif value >= target * 0.5:
                status = 'fair'
            else:
                status = 'poor'
        
        PerformanceMetric.objects.create(
            benchmark=benchmark,
            metric_name=metric_def['name'],
            metric_value=value,
           metric_unit=metric_def['unit'],
            target_value=target,
            status=status
        )


def create_recommendations(benchmark, scenario_type):
    """Create optimization recommendations based on scenario"""
    
    # Recommendations from index.html
    recommendations_config = {
        'joins': [
            ('hive.auto.convert.join', 'true', 'Enables automatic conversion to map-side joins'),
            ('hive.optimize.bucketmapjoin', 'true', 'Crucial for optimized joins if tables are bucketed'),
            ('hive.exec.parallel', 'true', 'Allows parallel execution of dependent stages'),
        ],
        'aggregation': [
            ('hive.map.aggr', 'true', 'Performs partial aggregation in the map phase'),
            ('hive.groupby.skewindata', 'true', 'Handles data skew in GROUP BY by breaking into two phases'),
            ('tez.grouping.max-size', '1000000000', 'Controls maximum size of grouped output in Tez'),
        ],
        'complex_types': [
            ('hive.optimize.json.serde', 'true', 'Ensures the most efficient JSON SerDe is used'),
            ('hive.optimize.index.filter', 'true', 'Attempts to filter data before deserializing'),
            ('hive.cbo.enable', 'true', 'Cost-Based Optimizer helps estimate cost of complex operations'),
        ],
        'io': [
            ('hive.exec.orc.split.strategy', 'HYBRID', 'Hybrid strategy to combine row-group and stripe-level filtering'),
            ('hive.exec.scratchdir', '/tmp/hive_scratch', 'Ensures scratch directories are on fast local storage'),
            ('tez.runtime.compress.intermediate', 'true', 'Compresses intermediate data written by mappers/reducers'),
        ],
        'partitioning': [
            ('hive.mapred.mode', 'strict', 'Prevents queries that try to scan all partitions'),
            ('hive.optimize.ppd', 'true', 'Enables partition pruning and predicate pushdown'),
            ('metastore.client.socket.timeout', '1800', 'Increases timeout for Metastore interaction'),
        ],
    }
    
    configs = recommendations_config.get(scenario_type, [])
    
    for config_key, config_value, reason in configs:
        # Get or create configuration
        config, _ = HiveConfiguration.objects.get_or_create(
            setting_key=config_key,
            setting_value=config_value,
            defaults={
                'name': config_key,
                'description': reason,
                'category': scenario_type if scenario_type in ['join', 'aggregation', 'io', 'partitioning'] else 'other',
                'impact_level': 'high'
            }
        )
        
        # Create recommendation
        OptimizationRecommendation.objects.create(
            benchmark=benchmark,
            configuration=config,
            priority='high',
            reason=reason,
            expected_improvement='Significant performance improvement expected'
        )


def benchmark_history(request):
    """View benchmark history and comparisons"""
    benchmarks = QueryBenchmark.objects.select_related('scenario').order_by('-executed_at')[:50]
    
    # Group by scenario for comparison
    scenario_stats = {}
    for benchmark in benchmarks:
        scenario_name = benchmark.scenario.name
        if scenario_name not in scenario_stats:
            scenario_stats[scenario_name] = {
                'benchmarks': [],
                'avg_time': 0,
            }
        scenario_stats[scenario_name]['benchmarks'].append(benchmark)
    
    # Calculate averages
    for scenario_name, stats in scenario_stats.items():
        times = [b.execution_time for b in stats['benchmarks'] if b.status == 'success']
        if times:
            stats['avg_time'] = sum(times) / len(times)
    
    context = {
        'benchmarks': benchmarks,
        'scenario_stats': scenario_stats,
    }
    
    return render(request, 'hive_assessment/history.html', context)
