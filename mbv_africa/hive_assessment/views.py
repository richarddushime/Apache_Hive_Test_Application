"""
Views for Hive Assessment Tool
Dynamic data retrieval with SQLite fallback
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Avg, Count, Max, Min
import time
import random
import logging

from hive_assessment.models import (
    AssessmentScenario, QueryBenchmark, PerformanceMetric,
    HiveConfiguration, OptimizationRecommendation
)
from hive_climate.hive_connector import get_hive_manager, is_hive_available, is_hive_enabled
from hive_climate.models import ClimateObservation, WeatherStation, Region

logger = logging.getLogger(__name__)


def get_assessment_stats():
    """Get assessment statistics from database"""
    return {
        'total_scenarios': AssessmentScenario.objects.count(),
        'active_scenarios': AssessmentScenario.objects.filter(is_active=True).count(),
        'total_benchmarks': QueryBenchmark.objects.count(),
        'successful_benchmarks': QueryBenchmark.objects.filter(status='success').count(),
        'failed_benchmarks': QueryBenchmark.objects.filter(status='failed').count(),
        'total_recommendations': OptimizationRecommendation.objects.count(),
        'configurations': HiveConfiguration.objects.count(),
        'avg_execution_time': QueryBenchmark.objects.filter(
            status='success'
        ).aggregate(avg=Avg('execution_time'))['avg'] or 0,
    }


def get_climate_data_stats():
    """Get climate data statistics for display"""
    return {
        'observations': ClimateObservation.objects.count(),
        'stations': WeatherStation.objects.count(),
        'regions': Region.objects.count(),
        'countries': WeatherStation.objects.values('country').distinct().count(),
    }


def assessment_dashboard(request):
    """
    Main assessment dashboard view with dynamic data
    """
    scenarios = AssessmentScenario.objects.filter(is_active=True)
    recent_benchmarks = QueryBenchmark.objects.select_related('scenario').order_by('-executed_at')[:10]
    
    # Get scenario types for dropdown
    scenario_choices = AssessmentScenario.SCENARIO_TYPES
    
    # Get statistics
    assessment_stats = get_assessment_stats()
    climate_stats = get_climate_data_stats()
    
    # Check Hive status
    hive_status = {
        'enabled': is_hive_enabled(),
        'available': is_hive_available() if is_hive_enabled() else False,
    }
    
    # Get performance metrics summary
    metrics_summary = PerformanceMetric.objects.values('status').annotate(
        count=Count('id')
    ).order_by('status')
    
    # Get latest benchmark by scenario type
    latest_by_type = {}
    for scenario_type, _ in AssessmentScenario.SCENARIO_TYPES:
        latest = QueryBenchmark.objects.filter(
            scenario__scenario_type=scenario_type,
            status='success'
        ).order_by('-executed_at').first()
        if latest:
            latest_by_type[scenario_type] = {
                'execution_time': latest.execution_time,
                'executed_at': latest.executed_at,
            }
    
    context = {
        'scenarios': scenarios,
        'scenario_choices': scenario_choices,
        'recent_benchmarks': recent_benchmarks,
        'assessment_stats': assessment_stats,
        'climate_stats': climate_stats,
        'hive_status': hive_status,
        'metrics_summary': list(metrics_summary),
        'latest_by_type': latest_by_type,
    }
    
    return render(request, 'hive_assessment/dashboard.html', context)


def run_assessment(request):
    """
    Execute a benchmark assessment
    Supports both real Hive queries and simulated mode
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)
    
    scenario_id = request.POST.get('scenario_id')
    record_count = int(request.POST.get('record_count', 100000000))
    simulate = request.POST.get('simulate', 'false').lower() == 'true'
    
    try:
        scenario = get_object_or_404(AssessmentScenario, id=scenario_id)
        
        # Check if Hive is available or if simulation is requested
        hive_available = is_hive_available() if is_hive_enabled() else False
        
        if hive_available and not simulate:
            # Execute real Hive query
            hive = get_hive_manager()
            start_time = time.time()
            
            try:
                results = hive.execute_query(scenario.test_query)
                execution_time = time.time() - start_time
                rows_returned = len(results) if results else 0
                status = 'success'
                error_message = ''
            except Exception as e:
                logger.error(f"Benchmark query failed: {str(e)}")
                execution_time = time.time() - start_time
                rows_returned = 0
                status = 'failed'
                error_message = str(e)
        else:
            # Simulate benchmark results based on scenario type
            execution_time = simulate_execution_time(scenario.scenario_type)
            rows_returned = random.randint(100, 10000)
            status = 'success'
            error_message = ''
            
        # Create benchmark record
        benchmark = QueryBenchmark.objects.create(
            scenario=scenario,
            query_executed=scenario.test_query,
            execution_time=execution_time,
            rows_processed=record_count,
            rows_returned=rows_returned,
            status=status,
            error_message=error_message,
            executed_by=request.user if request.user.is_authenticated else None
        )
        
        if status == 'success':
            # Generate performance metrics
            create_performance_metrics(benchmark, scenario.scenario_type, execution_time, record_count)
            
            # Generate optimization recommendations
            create_recommendations(benchmark, scenario.scenario_type)
        
        return JsonResponse({
            'success': status == 'success',
            'benchmark_id': benchmark.id,
            'execution_time': execution_time,
            'rows_returned': rows_returned,
            'simulated': not hive_available or simulate,
            'error': error_message if error_message else None,
        })
    
    except Exception as e:
        logger.error(f"Assessment failed: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


def simulate_execution_time(scenario_type):
    """Simulate realistic execution times based on scenario type"""
    base_times = {
        'joins': (1.5, 4.0),       # Complex joins take 1.5-4 seconds
        'aggregation': (2.0, 5.0),  # Aggregations take 2-5 seconds
        'complex_types': (2.5, 6.0), # Complex types take 2.5-6 seconds
        'io': (3.0, 8.0),           # I/O intensive takes 3-8 seconds
        'partitioning': (0.3, 1.5),  # Partition pruning is fast 0.3-1.5 seconds
    }
    min_time, max_time = base_times.get(scenario_type, (1.0, 3.0))
    return round(random.uniform(min_time, max_time), 3)


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


# ============ API Endpoints ============

def api_status(request):
    """API endpoint for assessment system status"""
    stats = get_assessment_stats()
    climate_stats = get_climate_data_stats()
    
    return JsonResponse({
        'status': 'healthy',
        'hive': {
            'enabled': is_hive_enabled(),
            'available': is_hive_available() if is_hive_enabled() else False,
        },
        'assessment': stats,
        'climate_data': climate_stats,
        'timestamp': timezone.now().isoformat(),
    })


def api_scenarios(request):
    """API endpoint for listing scenarios"""
    scenarios = AssessmentScenario.objects.filter(is_active=True).values(
        'id', 'name', 'scenario_type', 'description', 'record_count'
    )
    return JsonResponse({
        'scenarios': list(scenarios),
        'scenario_types': dict(AssessmentScenario.SCENARIO_TYPES),
    })


def api_quick_check(request):
    """
    API endpoint for quick health check
    Runs simulated benchmarks for all scenario types
    """
    results = {}
    
    for scenario_type, type_name in AssessmentScenario.SCENARIO_TYPES:
        execution_time = simulate_execution_time(scenario_type)
        
        # Determine health status based on execution time
        if scenario_type == 'partitioning':
            thresholds = (0.5, 1.0, 2.0)
        else:
            thresholds = (2.0, 4.0, 6.0)
        
        if execution_time <= thresholds[0]:
            status = 'excellent'
        elif execution_time <= thresholds[1]:
            status = 'good'
        elif execution_time <= thresholds[2]:
            status = 'fair'
        else:
            status = 'poor'
        
        results[scenario_type] = {
            'name': type_name,
            'execution_time': round(execution_time, 3),
            'status': status,
        }
    
    # Calculate overall health score
    status_scores = {'excellent': 100, 'good': 75, 'fair': 50, 'poor': 25}
    total_score = sum(status_scores[r['status']] for r in results.values())
    health_score = round(total_score / len(results))
    
    return JsonResponse({
        'health_score': health_score,
        'results': results,
        'hive_available': is_hive_available() if is_hive_enabled() else False,
        'timestamp': timezone.now().isoformat(),
    })


def api_recommendations(request):
    """API endpoint for getting optimization recommendations"""
    # Get latest recommendations grouped by category
    recommendations = OptimizationRecommendation.objects.select_related(
        'configuration', 'benchmark__scenario'
    ).order_by('-created_at')[:20]
    
    rec_data = []
    for rec in recommendations:
        rec_data.append({
            'id': rec.id,
            'configuration': {
                'key': rec.configuration.setting_key,
                'value': rec.configuration.setting_value,
                'category': rec.configuration.category,
            },
            'priority': rec.priority,
            'reason': rec.reason,
            'expected_improvement': rec.expected_improvement,
            'scenario': rec.benchmark.scenario.name if rec.benchmark else None,
            'is_applied': rec.is_applied,
            'created_at': rec.created_at.isoformat(),
        })
    
    return JsonResponse({
        'recommendations': rec_data,
        'total': OptimizationRecommendation.objects.count(),
    })


def api_full_metrics(request):
    """
    API endpoint for fetching all available metrics from Hive and HDFS.
    Returns comprehensive data for the dashboard.
    """
    import subprocess
    
    metrics = {
        'timestamp': timezone.now().isoformat(),
        'hive': {'available': False, 'databases': [], 'tables': {}},
        'hdfs': {'available': False, 'capacity': {}, 'datanodes': []},
        'performance': {},
        'storage': {},
        'optimizer': {},
        'infrastructure': {},
        'climate_data': get_climate_data_stats(),
        'assessment': get_assessment_stats(),
    }
    
    # Check Hive availability and get metrics
    if is_hive_enabled() and is_hive_available():
        try:
            hive = get_hive_manager()
            metrics['hive']['available'] = True
            
            # Get databases
            try:
                dbs = hive.execute_query("SHOW DATABASES")
                metrics['hive']['databases'] = [db[0] for db in dbs] if dbs else []
            except Exception as e:
                logger.warning(f"Could not fetch databases: {e}")
            
            # Get tables for mbv_africa database
            try:
                tables = hive.execute_query("SHOW TABLES IN mbv_africa")
                metrics['hive']['tables']['mbv_africa'] = [t[0] for t in tables] if tables else []
            except Exception as e:
                logger.warning(f"Could not fetch tables: {e}")
            
            # Get table row counts
            table_counts = {}
            for table in metrics['hive']['tables'].get('mbv_africa', []):
                try:
                    result = hive.execute_query(f"SELECT COUNT(*) FROM mbv_africa.{table}")
                    table_counts[table] = result[0][0] if result else 0
                except Exception:
                    table_counts[table] = 'N/A'
            metrics['hive']['table_counts'] = table_counts
            
            # Get Hive configurations
            try:
                configs = {}
                config_keys = [
                    'hive.cbo.enable',
                    'hive.auto.convert.join',
                    'hive.optimize.ppd',
                    'hive.map.aggr',
                    'hive.exec.parallel',
                    'hive.vectorized.execution.enabled',
                ]
                for key in config_keys:
                    try:
                        result = hive.execute_query(f"SET {key}")
                        configs[key] = result[0][0].split('=')[1] if result else 'unknown'
                    except:
                        configs[key] = 'unknown'
                metrics['optimizer']['hive_configs'] = configs
            except Exception as e:
                logger.warning(f"Could not fetch Hive configs: {e}")
            
            # Test query execution time
            try:
                start = time.time()
                hive.execute_query("SELECT 1")
                metrics['performance']['hive_ping_ms'] = round((time.time() - start) * 1000, 2)
            except Exception:
                metrics['performance']['hive_ping_ms'] = None
                
        except Exception as e:
            logger.error(f"Hive metrics collection failed: {e}")
            metrics['hive']['error'] = str(e)
    
    # Get HDFS metrics via docker exec
    try:
        # HDFS report
        result = subprocess.run(
            ['docker', 'exec', 'master-node', 'hdfs', 'dfsadmin', '-report'],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            metrics['hdfs']['available'] = True
            hdfs_output = result.stdout
            
            # Parse HDFS report
            metrics['hdfs']['raw_report'] = hdfs_output[:2000]  # Truncate for JSON
            
            # Extract key metrics
            import re
            capacity_match = re.search(r'Configured Capacity:\s*(\d+)', hdfs_output)
            used_match = re.search(r'DFS Used:\s*(\d+)', hdfs_output)
            remaining_match = re.search(r'DFS Remaining:\s*(\d+)', hdfs_output)
            live_nodes_match = re.search(r'Live datanodes \((\d+)\)', hdfs_output)
            under_replicated = re.search(r'Under replicated blocks:\s*(\d+)', hdfs_output)
            missing_blocks = re.search(r'Missing blocks:\s*(\d+)', hdfs_output)
            
            if capacity_match:
                cap_bytes = int(capacity_match.group(1))
                metrics['hdfs']['capacity']['total_gb'] = round(cap_bytes / (1024**3), 2)
            if used_match:
                used_bytes = int(used_match.group(1))
                metrics['hdfs']['capacity']['used_gb'] = round(used_bytes / (1024**3), 2)
            if remaining_match:
                rem_bytes = int(remaining_match.group(1))
                metrics['hdfs']['capacity']['remaining_gb'] = round(rem_bytes / (1024**3), 2)
            if live_nodes_match:
                metrics['hdfs']['live_datanodes'] = int(live_nodes_match.group(1))
            if under_replicated:
                metrics['hdfs']['under_replicated_blocks'] = int(under_replicated.group(1))
            if missing_blocks:
                metrics['hdfs']['missing_blocks'] = int(missing_blocks.group(1))
            
            # Calculate usage percentage
            if metrics['hdfs']['capacity'].get('total_gb') and metrics['hdfs']['capacity'].get('used_gb'):
                metrics['hdfs']['capacity']['used_pct'] = round(
                    (metrics['hdfs']['capacity']['used_gb'] / metrics['hdfs']['capacity']['total_gb']) * 100, 2
                )
                
    except subprocess.TimeoutExpired:
        metrics['hdfs']['error'] = 'Timeout fetching HDFS metrics'
    except Exception as e:
        metrics['hdfs']['error'] = str(e)
    
    # Get container stats
    try:
        result = subprocess.run(
            ['docker', 'stats', '--no-stream', '--format', 
             '{"container":"{{.Name}}","cpu":"{{.CPUPerc}}","mem":"{{.MemUsage}}","mem_pct":"{{.MemPerc}}"}'],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            container_stats = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    try:
                        import json
                        stat = json.loads(line)
                        container_stats.append(stat)
                    except:
                        pass
            metrics['infrastructure']['containers'] = container_stats
    except Exception as e:
        metrics['infrastructure']['containers_error'] = str(e)
    
    # Get container health status
    try:
        containers = ['hive-server', 'hive-metastore', 'master-node', 'django-app']
        health_status = {}
        for container in containers:
            result = subprocess.run(
                ['docker', 'inspect', '--format', '{{.State.Health.Status}}', container],
                capture_output=True, text=True, timeout=10
            )
            health_status[container] = result.stdout.strip() if result.returncode == 0 else 'unknown'
        metrics['infrastructure']['health'] = health_status
    except Exception as e:
        metrics['infrastructure']['health_error'] = str(e)
    
    # Performance benchmarks from database
    recent_benchmarks = QueryBenchmark.objects.filter(
        status='success'
    ).order_by('-executed_at')[:10]
    
    metrics['performance']['recent_benchmarks'] = [
        {
            'scenario': b.scenario.name,
            'type': b.scenario.scenario_type,
            'execution_time': b.execution_time,
            'rows_processed': b.rows_processed,
            'executed_at': b.executed_at.isoformat(),
        }
        for b in recent_benchmarks
    ]
    
    # Calculate average execution times by scenario type
    from django.db.models import Avg
    avg_times = QueryBenchmark.objects.filter(
        status='success'
    ).values('scenario__scenario_type').annotate(
        avg_time=Avg('execution_time')
    )
    metrics['performance']['avg_by_type'] = {
        item['scenario__scenario_type']: round(item['avg_time'], 3)
        for item in avg_times
    }
    
    return JsonResponse(metrics)


def api_hive_query(request):
    """
    API endpoint to execute arbitrary Hive queries (for admin/testing)
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)
    
    query = request.POST.get('query', '').strip()
    if not query:
        return JsonResponse({'error': 'Query is required'}, status=400)
    
    # Basic security: prevent dangerous queries
    dangerous_keywords = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE', 'INSERT']
    if any(kw in query.upper() for kw in dangerous_keywords):
        return JsonResponse({'error': 'Dangerous query not allowed'}, status=403)
    
    if not is_hive_enabled() or not is_hive_available():
        return JsonResponse({'error': 'Hive is not available'}, status=503)
    
    try:
        hive = get_hive_manager()
        start = time.time()
        results = hive.execute_query(query)
        execution_time = time.time() - start
        
        return JsonResponse({
            'success': True,
            'query': query,
            'execution_time': round(execution_time, 3),
            'row_count': len(results) if results else 0,
            'results': results[:100] if results else [],  # Limit results
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
        }, status=500)


def load_sample_scenarios(request):
    """Load sample assessment scenarios if none exist"""
    if AssessmentScenario.objects.exists():
        return JsonResponse({
            'message': 'Scenarios already exist',
            'count': AssessmentScenario.objects.count()
        })
    
    sample_scenarios = [
        {
            'name': 'Large Table Join Test',
            'scenario_type': 'joins',
            'description': 'Tests JOIN performance between two large tables (100M+ rows)',
            'test_query': '''
                SELECT a.station_id, a.temp_mean, b.precipitation
                FROM climate_observations a
                JOIN precipitation_data b ON a.station_id = b.station_id
                WHERE a.year >= 2020
            ''',
            'record_count': 100000000,
        },
        {
            'name': 'Complex Aggregation Test',
            'scenario_type': 'aggregation',
            'description': 'Tests GROUP BY with multiple aggregation functions',
            'test_query': '''
                SELECT region, year, 
                       AVG(temp_mean) as avg_temp,
                       SUM(precipitation) as total_precip,
                       COUNT(*) as observation_count
                FROM climate_observations
                GROUP BY region, year
                ORDER BY region, year
            ''',
            'record_count': 50000000,
        },
        {
            'name': 'Nested JSON Processing',
            'scenario_type': 'complex_types',
            'description': 'Tests handling of nested JSON and array columns',
            'test_query': '''
                SELECT station_id,
                       get_json_object(metadata, '$.sensor_type') as sensor,
                       explode(measurements) as measurement
                FROM sensor_readings
                WHERE year = 2024
            ''',
            'record_count': 25000000,
        },
        {
            'name': 'High Volume I/O Test',
            'scenario_type': 'io',
            'description': 'Tests I/O throughput with large sequential scans',
            'test_query': '''
                SELECT * FROM climate_observations
                WHERE temp_mean > 30
                ORDER BY observation_date DESC
                LIMIT 1000000
            ''',
            'record_count': 200000000,
        },
        {
            'name': 'Partition Pruning Test',
            'scenario_type': 'partitioning',
            'description': 'Tests partition pruning efficiency on time-partitioned data',
            'test_query': '''
                SELECT station_id, temp_mean, precipitation
                FROM climate_observations
                WHERE year = 2024 AND month = 6
                  AND region = 'East Africa'
            ''',
            'record_count': 500000,
        },
    ]
    
    created = 0
    for scenario_data in sample_scenarios:
        AssessmentScenario.objects.create(**scenario_data)
        created += 1
    
    return JsonResponse({
        'message': f'Created {created} sample scenarios',
        'count': created
    })
