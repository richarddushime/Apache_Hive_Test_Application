# Via Beeline
docker exec -it hive-server beeline -u "jdbc:hive2://localhost:10000/;auth=noSasl" \
  -e "SELECT region, COUNT(*) as cnt FROM mbv_africa.portfolio_observations GROUP BY region;"

# Via Django API
curl http://localhost:8080/api/health/hive_test/


With a million rows and a multi-node cluster, you can now move beyond simple connectivity tests to **Performance and Architectural Benchmarking**.

The following queries are designed to stress the system and reveal how Hive handles distributed joins, partition pruning, and column-oriented storage (ORC).

### 1. Data Distribution & Storage Analysis


```sql
-- Switch to your database
USE mbv_africa;

-- Check how many files the million rows are split into across HDFS
DESCRIBE FORMATTED portfolio_observations;

-- Calculate raw storage metrics (Row count, total size on disk)
ANALYZE TABLE portfolio_observations COMPUTE STATISTICS;
DESCRIBE EXTENDED portfolio_observations;

```

### 2. Testing the "Query Optimizer" (CBO)

Use `EXPLAIN` to see the **Directed Acyclic Graph (DAG)**. This shows you exactly how Hive plans to distribute the work between your NameNode and DataNodes.

```sql
-- Test 1: Simple Filter (Testing Partition Pruning)
-- If your table is partitioned by 'region', this should only scan one folder in HDFS
EXPLAIN 
SELECT COUNT(*) 
FROM portfolio_observations 
WHERE region = 'North';

-- Test 2: Complex Aggregation
-- This forces a "Shuffle" phase where data is moved between nodes
EXPLAIN 
SELECT region, month, AVG(temp_mean), SUM(precipitation)
FROM portfolio_observations
GROUP BY region, month
ORDER BY region, month;

```

### 3. Join Algorithm Benchmarking

Your `portfolio_stations` table is small (lookup table), while `portfolio_observations` is large (fact table). This is the perfect scenario to test **Map-Side Joins**.

```sql
-- Force a Broadcast (Map-Side) Join
-- The small 'stations' table is cached in memory on every DataNode to avoid a slow Reduce phase
SET hive.auto.convert.join=true;

SELECT 
    s.country, 
    o.year, 
    AVG(o.sea_surface_temp) as avg_sst
FROM portfolio_observations o
JOIN portfolio_stations s ON o.station_id = s.station_id
WHERE s.is_active = true
GROUP BY s.country, o.year;

-- Compare execution time by disabling the optimizer
SET hive.auto.convert.join=false;
-- (Run the SELECT above again and notice the "Time Taken" increase)

```

### 4. Vectorized Execution & Columnar Storage

Hive 4.0.0 is optimized for **ORC** files. Vectorization allows Hive to process 1,024 rows in a single CPU instruction instead of one row at a time.

```sql
-- Enable Vectorization
SET hive.vectorized.execution.enabled = true;
SET hive.vectorized.execution.reduce.enabled = true;

-- Heavy math query to test CPU throughput on the million rows
SELECT 
    region,
    STDDEV_POP(temp_max - temp_min) as temp_variance,
    CORR(humidity, precipitation) as moisture_correlation
FROM portfolio_observations
GROUP BY region;

```

### 5. Multi-Table Climate Analytics

This query simulates a real-world "Climate Intelligence" request by joining your diverse datasets to find anomalies.

```sql
-- Identify regions where high rainfall (climate_data) 
-- correlates with low ocean salinity (ocean_data)
SELECT 
    c.region,
    c.date,
    c.rainfall,
    o.salinity
FROM mbv_africa.climate_data c
JOIN mbv_africa.ocean_data o ON (c.date = o.date AND c.region = o.region)
WHERE c.rainfall > 100 AND o.salinity < 33
ORDER BY c.rainfall DESC;

```

### 6. System Integrity & Transaction Checks (ACID)

Since you are using Hive 4.0.0, it uses ACID transactions to ensure that if a DataNode crashes during a query, the database doesn't get corrupted.

```sql
-- Check if the system is managing locks correctly for your million rows
SHOW LOCKS;

-- Check the status of the background "Compactor" 
-- (Hive merges small files into large ORC files automatically)
SHOW COMPACTIONS;

-- Verify the "Write ID" to see how many updates have occurred
DESCRIBE EXTENDED portfolio_observations;

```

### How to run these via CLI:

If you want to run these directly from your terminal to get the timing metrics, use this syntax:

```bash
docker exec -it hive-server beeline -u "jdbc:hive2://localhost:10000/mbv_africa;auth=noSasl" \
  --showHeader=true --outputformat=table \
  -e "SET hive.vectorized.execution.enabled=true; SELECT region, AVG(temp_mean) FROM portfolio_observations GROUP BY region;"

```

**Observation Tip:** While these queries run, open a second terminal and run `docker stats`. You will see `datanode1` and `datanode2` CPU usage spike simultaneously, proving the **Distributed Query Execution** is working!


rdm@rdm ~ % docker exec hive-server beeline -u jdbc:hive2://localhost:10000 -e "SHOW DATABASES;"
Error response from daemon: container 18a62a7621ca1a2b0b843a35713b4c099a49779a563f800633104b7beca58dd2 is not running
rdm@rdm ~ % docker exec -it hive-server beeline -u "jdbc:hive2://localhost:10000/mbv_africa;auth=noSasl" \
  --showHeader=true --outputformat=table \
  -e "SET hive.vectorized.execution.enabled=true; SELECT region, AVG(temp_mean) FROM portfolio_observations GROUP BY region;"
SLF4J: Class path contains multiple SLF4J bindings.
SLF4J: Found binding in [jar:file:/opt/hive/lib/log4j-slf4j-impl-2.6.2.jar!/org/slf4j/impl/StaticLoggerBinder.class]
SLF4J: Found binding in [jar:file:/opt/hadoop-2.7.4/share/hadoop/common/lib/slf4j-log4j12-1.7.10.jar!/org/slf4j/impl/StaticLoggerBinder.class]
SLF4J: See http://www.slf4j.org/codes.html#multiple_bindings for an explanation.
SLF4J: Actual binding is of type [org.apache.logging.slf4j.Log4jLoggerFactory]
Connecting to jdbc:hive2://localhost:10000/mbv_africa;auth=noSasl
Connected to: Apache Hive (version 2.3.2)
Driver: Hive JDBC (version 2.3.2)
Transaction isolation: TRANSACTION_REPEATABLE_READ
No rows affected (0.126 seconds)
WARNING: Hive-on-MR is deprecated in Hive 2 and may not be available in the future versions. Consider using a different execution engine (i.e. spark, tez) or using Hive 1.X releases.
+----------+---------------------+
|  region  |         _c1         |
+----------+---------------------+
| Central  | 30.488045497634584  |
| East     | 26.501613637710754  |
| North    | 24.496983927505234  |
| South    | 20.530209133713786  |
| West     | 29.517723303982514  |
+----------+---------------------+
5 rows selected (4.004 seconds)
Beeline version 2.3.2 by Apache Hive
Closing: 0: jdbc:hive2://localhost:10000/mbv_africa;auth=noSasl
rdm@rdm ~ % 


CONTAINER ID   NAME                CPU %     MEM USAGE / LIMIT     MEM %     NET I/O           BLOCK I/O         PIDS 
3ac1356ac423   django-app          2.66%     114.8MiB / 7.653GiB   1.46%     128kB / 802kB     32.2MB / 569kB    12 
ef0cd96e0979   hive-server         1.01%     954.3MiB / 7.653GiB   12.18%    329MB / 75.8MB    180kB / 13.7MB    47 
f2abf7a026a7   hive-metastore      0.43%     569.9MiB / 7.653GiB   7.27%     1.14MB / 1.35MB   143kB / 35.6MB    234 
50e90626f16a   slave-node-1        0.41%     686.7MiB / 7.653GiB   8.76%     74.8MB / 212MB    12.3kB / 81MB     67 
2e951db813db   slave-node-2        0.21%     588.1MiB / 7.653GiB   7.50%     74.7MB / 194MB    12.3kB / 81MB     69 
f3572fbce12f   hive-metastore-db   0.01%     31.63MiB / 7.653GiB   0.40%     1.12MB / 970kB    4.1kB / 64.5MB    12 
180aa1f4e6c8   master-node         0.29%     603.9MiB / 7.653GiB   7.71%     4.35MB / 1.44MB   4.34MB / 9.71MB   71 
 