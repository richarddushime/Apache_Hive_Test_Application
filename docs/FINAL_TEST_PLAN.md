# Final Test Plan: Apache Hive Seminar Validation

---

## Pre-Test Checklist

### 1. Infrastructure Verification
```bash
# Start all containers
cd /Users/rdm/Desktop/oss/upr_work/DATABASES-FOR-BIG-DATA/Apache_Hive_Test_Application
docker-compose up -d

# Verify all 7 containers are healthy
docker-compose ps

# Expected: All services "Up" and "healthy"
# - master-node (NameNode)
# - slave-node-1 (DataNode)
# - slave-node-2 (DataNode)
# - hive-metastore
# - hive-server
# - hive-metastore-postgresql
# - django-app
```

---

## Test Suite

### TEST 1: Multi-Node Cluster Verification (Requirement: nodes >= 2)

```bash
# Check HDFS cluster report
docker exec -it master-node hdfs dfsadmin -report

# Expected output should show:
# - Live datanodes: 2
# - slave-node-1 and slave-node-2 both active
# - Configured capacity, DFS remaining, block counts
```

**Validation Criteria:**
- [ ] 2+ DataNodes are live and healthy
- [ ] Replication factor = 2
- [ ] No under-replicated blocks
- [ ] No corrupt blocks

---

### TEST 2: Data Scale Verification (5+ Million Records)

```bash
# Connect to Hive and count records
docker exec -it hive-server beeline \
  -u "jdbc:hive2://localhost:10000/mbv_africa;auth=noSasl" \
  -e "SELECT COUNT(*) as total_records FROM portfolio_observations;"

# Check all tables
docker exec -it hive-server beeline \
  -u "jdbc:hive2://localhost:10000/mbv_africa;auth=noSasl" \
  -e "SELECT 'portfolio_observations' as tbl, COUNT(*) as cnt FROM portfolio_observations
      UNION ALL
      SELECT 'portfolio_stations', COUNT(*) FROM portfolio_stations
      UNION ALL  
      SELECT 'climate_data', COUNT(*) FROM climate_data
      UNION ALL
      SELECT 'ocean_data', COUNT(*) FROM ocean_data;"

# Check HDFS storage usage
docker exec -it master-node hdfs dfs -du -h /user/hive/warehouse/mbv_africa.db/
```

**Validation Criteria:**
- [ ] Total records >= 5,000,000
- [ ] HDFS storage reflects new data size
- [ ] Data distributed across both DataNodes

---

### TEST 3: Storage Model Analysis

```bash
# Examine table storage format and properties
docker exec -it hive-server beeline \
  -u "jdbc:hive2://localhost:10000/mbv_africa;auth=noSasl" \
  -e "DESCRIBE FORMATTED portfolio_observations;"

# Check HDFS block distribution
docker exec -it master-node hdfs fsck /user/hive/warehouse/mbv_africa.db/portfolio_observations -files -blocks -locations
```

**Validation Criteria:**
- [ ] Document SerDe library (LazySimpleSerDe or ORC)
- [ ] Document InputFormat/OutputFormat
- [ ] Verify block replication across nodes
- [ ] Note compression settings (if any)

---

### TEST 4: Query Execution & MapReduce Jobs

#### 4a. Simple Aggregation Query
```bash
docker exec -it hive-server beeline \
  -u "jdbc:hive2://localhost:10000/mbv_africa;auth=noSasl" \
  -e "SET hive.vectorized.execution.enabled=true;
      SELECT region, COUNT(*) as obs_count, AVG(temp_mean) as avg_temp
      FROM portfolio_observations
      GROUP BY region;"
```

**Record:**
- [ ] Execution time: _____ seconds
- [ ] Number of MapReduce jobs: _____
- [ ] HDFS bytes read: _____

#### 4b. Complex Aggregation (GROUP BY + ORDER BY)
```bash
docker exec -it hive-server beeline \
  -u "jdbc:hive2://localhost:10000/mbv_africa;auth=noSasl" \
  -e "SELECT region, month, 
          AVG(temp_mean) as avg_temp,
          SUM(precipitation) as total_precip
      FROM portfolio_observations
      GROUP BY region, month
      ORDER BY region, month;"
```

**Record:**
- [ ] Execution time: _____ seconds
- [ ] Number of MapReduce stages: _____
- [ ] Reducer count (auto-estimated): _____

#### 4c. Statistical Analysis with Vectorization
```bash
docker exec -it hive-server beeline \
  -u "jdbc:hive2://localhost:10000/mbv_africa;auth=noSasl" \
  -e "SET hive.vectorized.execution.enabled=true;
      SET hive.vectorized.execution.reduce.enabled=true;
      SELECT region,
          STDDEV_POP(temp_max - temp_min) as temp_variance,
          CORR(humidity, precipitation) as moisture_corr,
          PERCENTILE_APPROX(temp_mean, 0.5) as median_temp
      FROM portfolio_observations
      GROUP BY region;"
```

**Record:**
- [ ] Execution time: _____ seconds
- [ ] Vectorization confirmation in logs

---

### TEST 5: Query Optimization (CBO & Join Algorithms)

#### 5a. Collect Table Statistics (Required for CBO)
```bash
docker exec -it hive-server beeline \
  -u "jdbc:hive2://localhost:10000/mbv_africa;auth=noSasl" \
  -e "ANALYZE TABLE portfolio_observations COMPUTE STATISTICS;
      ANALYZE TABLE portfolio_stations COMPUTE STATISTICS;
      ANALYZE TABLE portfolio_observations COMPUTE STATISTICS FOR COLUMNS;"
```

**Record:**
- [ ] Statistics computation time: _____ seconds

#### 5b. Map-Side (Broadcast) Join Test
```bash
docker exec -it hive-server beeline \
  -u "jdbc:hive2://localhost:10000/mbv_africa;auth=noSasl" \
  -e "SET hive.auto.convert.join=true;
      SET hive.auto.convert.join.noconditionaltask.size=100000000;
      EXPLAIN
      SELECT s.country, s.region, AVG(o.temp_mean) as avg_temp
      FROM portfolio_observations o
      JOIN portfolio_stations s ON o.station_id = s.station_id
      GROUP BY s.country, s.region;"
```

**Validation:**
- [ ] EXPLAIN shows "Map Join" operator
- [ ] Small table (stations) broadcast to mappers

#### 5c. Execute Join and Compare
```bash
# Map-Side Join (enabled)
docker exec -it hive-server beeline \
  -u "jdbc:hive2://localhost:10000/mbv_africa;auth=noSasl" \
  -e "SET hive.auto.convert.join=true;
      SELECT s.country, s.region, COUNT(*) as cnt, AVG(o.temp_mean) as avg_temp
      FROM portfolio_observations o
      JOIN portfolio_stations s ON o.station_id = s.station_id
      GROUP BY s.country, s.region
      LIMIT 20;"

# Reduce-Side Join (disabled for comparison)
docker exec -it hive-server beeline \
  -u "jdbc:hive2://localhost:10000/mbv_africa;auth=noSasl" \
  -e "SET hive.auto.convert.join=false;
      SELECT s.country, s.region, COUNT(*) as cnt, AVG(o.temp_mean) as avg_temp
      FROM portfolio_observations o
      JOIN portfolio_stations s ON o.station_id = s.station_id
      GROUP BY s.country, s.region
      LIMIT 20;"
```

**Record:**
- [ ] Map-Side Join time: _____ seconds
- [ ] Reduce-Side Join time: _____ seconds
- [ ] Performance ratio: _____x faster

---

### TEST 6: Transaction Management (ACID)

```bash
# Check if ACID is enabled
docker exec -it hive-server beeline \
  -u "jdbc:hive2://localhost:10000/mbv_africa;auth=noSasl" \
  -e "SET hive.support.concurrency;
      SET hive.txn.manager;"

# Test table locking (if enabled)
docker exec -it hive-server beeline \
  -u "jdbc:hive2://localhost:10000/mbv_africa;auth=noSasl" \
  -e "SHOW LOCKS;"
```

**Note:** If ACID not configured, document this as a limitation of the test environment.

---

### TEST 7: Django Application Integration

#### 7a. Test REST API Endpoints
```bash
# Climate data endpoint
curl -s http://localhost:8080/api/climate/ | head -100

# Stations endpoint
curl -s http://localhost:8080/api/stations/ | head -100

# Schema endpoint
curl -s http://localhost:8080/api/schema/

# Dashboard
open http://localhost:8080/
```

#### 7b. Test Hive Connection from Django
```bash
# Check Django logs for Hive connectivity
docker logs django-app 2>&1 | grep -i hive

# Test via Django shell (if needed)
docker exec -it django-app python manage.py shell -c "
from hive_climate.hive_connector import HiveConnectionManager
hm = HiveConnectionManager()
print('Connection status:', hm.test_connection())
"
```

**Validation:**
- [ ] REST API returns data
- [ ] Dashboard loads with charts
- [ ] Hive connection successful (or SQLite fallback works)

---

### TEST 8: Distributed Execution Verification

```bash
# Monitor container resource usage during query
docker stats --no-stream

# Run a heavy query and monitor
docker exec -it hive-server beeline \
  -u "jdbc:hive2://localhost:10000/mbv_africa;auth=noSasl" \
  -e "SELECT year, month, region,
          AVG(temp_mean), AVG(humidity), SUM(precipitation)
      FROM portfolio_observations
      GROUP BY year, month, region
      ORDER BY year, month, region;" &

# In another terminal, watch resource usage
watch -n 2 'docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"'
```

**Validation:**
- [ ] Both slave-node-1 and slave-node-2 show CPU activity
- [ ] Query distributed across DataNodes

---

### TEST 9: Performance Benchmarks (5M+ Records)

| Test | Query Type | Expected Time | Actual Time | HDFS Read |
|------|-----------|---------------|-------------|-----------|
| 1 | Simple COUNT(*) | < 30s | _____ | _____ |
| 2 | Regional AVG | < 60s | _____ | _____ |
| 3 | GROUP BY + ORDER BY | < 120s | _____ | _____ |
| 4 | Statistical (STDDEV, CORR) | < 180s | _____ | _____ |
| 5 | Map-Side JOIN | < 90s | _____ | _____ |
| 6 | Reduce-Side JOIN | < 180s | _____ | _____ |

---

### TEST 10: Error Handling & Edge Cases

```bash
# Test reserved keyword handling
docker exec -it hive-server beeline \
  -u "jdbc:hive2://localhost:10000/mbv_africa;auth=noSasl" \
  -e "SELECT \`date\`, region FROM climate_data LIMIT 5;"

# Test non-existent column (should fail gracefully)
docker exec -it hive-server beeline \
  -u "jdbc:hive2://localhost:10000/mbv_africa;auth=noSasl" \
  -e "SELECT nonexistent_column FROM portfolio_observations LIMIT 1;" 2>&1

# Test large result set handling
docker exec -it hive-server beeline \
  -u "jdbc:hive2://localhost:10000/mbv_africa;auth=noSasl" \
  -e "SELECT * FROM portfolio_observations LIMIT 1000000;" > /dev/null
```

---

## Post-Test Documentation

### Update Report (new_main.tex) with:
1. [ ] New record count (5M+)
2. [ ] Updated query performance times
3. [ ] New HDFS storage statistics
4. [ ] Revised MapReduce job metrics
5. [ ] Updated HDFS cluster report

### Update Slides (slides.tex) with:
1. [ ] Update slide 2: Test data statistics
2. [ ] Update slide 6: Experimental results table
3. [ ] Update slide 9: Achievement metrics

---

## Quick Verification Script

Save and run this all-in-one verification:

```bash
#!/bin/bash
# final_verification.sh

echo "=== Apache Hive Seminar Final Verification ==="
echo "Date: $(date)"
echo ""

echo "1. Container Status:"
docker-compose ps
echo ""

echo "2. HDFS Cluster Report:"
docker exec master-node hdfs dfsadmin -report 2>/dev/null | head -30
echo ""

echo "3. Data Record Counts:"
docker exec hive-server beeline -u "jdbc:hive2://localhost:10000/mbv_africa;auth=noSasl" --silent=true \
  -e "SELECT 'Total Records' as metric, COUNT(*) as value FROM portfolio_observations;" 2>/dev/null
echo ""

echo "4. Sample Query (Regional AVG):"
time docker exec hive-server beeline -u "jdbc:hive2://localhost:10000/mbv_africa;auth=noSasl" --silent=true \
  -e "SELECT region, AVG(temp_mean) FROM portfolio_observations GROUP BY region;" 2>/dev/null
echo ""

echo "5. Django API Test:"
curl -s http://localhost:8080/api/schema/ | head -20
echo ""

echo "=== Verification Complete ==="
```

---

## Seminar Requirements Checklist

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Install on local network (nodes >= 2) | ☐ | HDFS report shows 2 DataNodes |
| Study architecture/components | ☐ | Report Chapter 2 |
| Storage model | ☐ | TEST 3 results |
| Transaction management | ☐ | TEST 6 results |
| Query execution | ☐ | TEST 4 results |
| Query optimization | ☐ | TEST 5 results |
| Join algorithms | ☐ | TEST 5c comparison |
| Define simple application | ☐ | Django climate dashboard |
| System design | ☐ | Architecture diagram |
| Implement application | ☐ | Working REST API |
| Experiment with system | ☐ | All TEST results |
| Short paper (6-10 pages) | ☐ | new_main.tex |

---

## Expected Timeline

| Phase | Duration | Tasks |
|-------|----------|-------|
| Setup | 10 min | Start containers, verify health |
| Data Verification | 5 min | Count records, check distribution |
| Core Tests (1-6) | 30 min | Execute all query tests |
| Integration Tests (7-8) | 10 min | Django API, distributed execution |
| Benchmarks (9) | 20 min | Performance timing |
| Documentation | 15 min | Update report and slides |
| **Total** | **~90 min** | |

---

## Notes

- With 5M+ records, expect significantly longer query times than the original 127K dataset
- MapReduce jobs will show more map/reduce tasks
- Monitor memory usage - may need to increase Docker resource limits
- Save all query outputs for report appendix
