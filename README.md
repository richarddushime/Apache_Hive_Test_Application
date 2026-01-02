# MBV Climate and Ocean Intelligence Africa
## Multi-Node Apache Hive & Hadoop Big Data Platform

A production-grade distributed OLAP environment for climate data analysis, featuring a 7-container Docker stack with Apache Hive, HDFS, and a Django REST API.

---

##  Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Docker Network                                │
├─────────────────────────────────────────────────────────────────┤
│  Django App ──▶ HiveServer2 ──▶ Hive Metastore ──▶ PostgreSQL   │
│  (8080)         (10000)         (9083)             (5432)       │
│                      │                                          │
│                      ▼                                          │
│              ┌──────────────┐                                   │
│              │   HDFS       │                                   │
│              │  NameNode    │                                   │
│              │   (9870)     │                                   │
│              └──────┬───────┘                                   │
│              ┌──────┴───────┐                                   │
│              ▼              ▼                                   │
│         DataNode-1    DataNode-2                                │
│          (9864)        (9865)                                   │
└─────────────────────────────────────────────────────────────────┘
```

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| master-node | apache/hadoop:3 | 9870, 9000 | HDFS NameNode |
| slave-node-1 | apache/hadoop:3 | 9864 | HDFS DataNode |
| slave-node-2 | apache/hadoop:3 | 9865 | HDFS DataNode |
| hive-metastore-db | postgres:9.6-alpine | 5432 | Metastore DB |
| hive-metastore | bde2020/hive:2.3.2 | 9083 | Schema management |
| hive-server | bde2020/hive:2.3.2 | 10000, 10002 | HiveServer2 |
| django-app | Python 3.9 | 8080 | REST API |

---

##  Quick Start

### Prerequisites
- Docker Desktop (20.10+)
- Docker Compose v2
- Python 3.9+ (for data generation)
- 8GB+ RAM recommended

### 1. Start the Cluster
```bash
# Clone and navigate to project
cd Apache_Hive_Test_Application

# Start all 7 containers
docker-compose up -d

# Wait for all services to be healthy (2-3 minutes)
docker-compose ps
```

### 2. Generate Test Data
```bash
# Generate ~1 million rows (default)
python mbv_africa/scripts/generate_data.py

# Or choose a preset size
python mbv_africa/scripts/generate_data.py --size small    # ~10K rows
python mbv_africa/scripts/generate_data.py --size medium   # ~100K rows
python mbv_africa/scripts/generate_data.py --size large    # ~1M rows
python mbv_africa/scripts/generate_data.py --size xlarge   # ~5M rows
```

### 3. Ingest Data into Hive
```bash
./ingest_data.sh
```

### 4. Access Services
| Service | URL |
|---------|-----|
| Django Dashboard | http://localhost:8080 |
| REST API | http://localhost:8080/api/ |
| Swagger Docs | http://localhost:8080/api/docs/ |
| HDFS Web UI | http://localhost:9870 |
| HiveServer2 Web UI | http://localhost:10002 |

---

## 🔍 Testing Hive Queries Directly

### Using Beeline (Hive CLI)

```bash
# Connect to Hive
docker exec -it hive-server beeline -u "jdbc:hive2://localhost:10000/;auth=noSasl"

# Once connected, you'll see: 0: jdbc:hive2://localhost:10000/>
```

### Common Hive Queries

```sql
-- List databases
SHOW DATABASES;

-- Use the climate database
USE mbv_africa;

-- List tables
SHOW TABLES;

-- Check row counts
SELECT COUNT(*) FROM climate_data;
SELECT COUNT(*) FROM portfolio_observations;

-- Sample data
SELECT * FROM portfolio_observations LIMIT 10;

-- Aggregation by region
SELECT region, COUNT(*) as obs_count, 
       AVG(temp_mean) as avg_temp,
       AVG(precipitation) as avg_precip
FROM portfolio_observations 
GROUP BY region;

-- Temperature trends by year
SELECT year, 
       AVG(temp_mean) as avg_temp,
       MAX(temp_max) as max_temp,
       MIN(temp_min) as min_temp
FROM portfolio_observations 
GROUP BY year 
ORDER BY year;

-- Coastal vs inland stations
SELECT 
    CASE WHEN sea_surface_temp IS NOT NULL THEN 'Coastal' ELSE 'Inland' END as station_type,
    COUNT(*) as observation_count,
    AVG(temp_mean) as avg_temperature
FROM portfolio_observations
GROUP BY CASE WHEN sea_surface_temp IS NOT NULL THEN 'Coastal' ELSE 'Inland' END;

-- Exit Beeline
!quit
```

### One-liner Query Execution

```bash
# Execute single query
docker exec -it hive-server beeline -u "jdbc:hive2://localhost:10000/;auth=noSasl" \
  -e "SELECT region, COUNT(*) FROM mbv_africa.portfolio_observations GROUP BY region;"

# Execute multiple queries from file
docker exec -it hive-server beeline -u "jdbc:hive2://localhost:10000/;auth=noSasl" \
  -f /path/to/queries.sql
```

---

## Getting Metrics & Monitoring

### HDFS Metrics

```bash
# Cluster health report
docker exec master-node hdfs dfsadmin -report

# File system usage
docker exec master-node hdfs dfs -df -h

# List files in Hive warehouse
docker exec master-node hdfs dfs -ls -R /user/hive/warehouse/

# Check replication status
docker exec master-node hdfs fsck / -files -blocks
```

### Hive Table Metrics

```bash
# Table statistics
docker exec -it hive-server beeline -u "jdbc:hive2://localhost:10000/;auth=noSasl" \
  -e "DESCRIBE FORMATTED mbv_africa.portfolio_observations;"

# Analyze table for statistics
docker exec -it hive-server beeline -u "jdbc:hive2://localhost:10000/;auth=noSasl" \
  -e "ANALYZE TABLE mbv_africa.portfolio_observations COMPUTE STATISTICS;"

# Column statistics
docker exec -it hive-server beeline -u "jdbc:hive2://localhost:10000/;auth=noSasl" \
  -e "ANALYZE TABLE mbv_africa.portfolio_observations COMPUTE STATISTICS FOR COLUMNS;"
```

### Container & Resource Metrics

```bash
# Container status
docker-compose ps

# Resource usage (CPU, Memory)
docker stats --no-stream

# Container logs
docker logs hive-server -f --tail 100
docker logs master-node -f --tail 100

# Health check status
docker inspect --format='{{.State.Health.Status}}' hive-server
```

### Django API Health Check

```bash
# Hive connectivity test
curl -s http://localhost:8080/api/health/hive_test/ | python3 -m json.tool

# API root
curl -s http://localhost:8080/api/ | python3 -m json.tool
```

---

## Web UIs

### HDFS NameNode UI (http://localhost:9870)
- **Overview**: Cluster summary, capacity, live/dead nodes
- **Datanodes**: Individual node status and capacity
- **Utilities → Browse**: Browse HDFS file system
- **Utilities → Logs**: NameNode logs

### HiveServer2 UI (http://localhost:10002)
- **Active Sessions**: Current connections
- **Query Information**: Running/completed queries
- **Metrics**: Server performance metrics
- **Configuration**: Hive settings

---

##  Project Structure

```
Apache_Hive_Test_Application/
├── docker-compose.yaml      # 7-container orchestration
├── Dockerfile               # Django app container
├── ingest_data.sh          # Data ingestion script
├── hadoop.env              # Hadoop environment vars
├── hadoop_conf/            # Hadoop/Hive configuration
│   ├── core-site.xml
│   ├── hdfs-site.xml
│   └── hive-site.xml
├── mbv_africa/             # Django application
│   ├── manage.py
│   ├── data/               # CSV data files
│   ├── hive_climate/       # Main app with Hive connector
│   └── scripts/
│       └── generate_data.py  # Data generator
└── docs/
    ├── ARCHITECTURE.md     # Detailed architecture
    └── main.tex            # LaTeX report
```

---

##  Troubleshooting

### Container Not Starting
```bash
# Check logs
docker-compose logs hive-server
docker-compose logs master-node

# Restart specific service
docker-compose restart hive-server

# Full restart
docker-compose down && docker-compose up -d
```

### Hive Connection Issues
```bash
# Verify HiveServer2 is healthy
docker inspect --format='{{.State.Health.Status}}' hive-server

# Check port is listening
docker exec hive-server netstat -tlnp | grep 10000

# Test with simple query
docker exec hive-server beeline -u "jdbc:hive2://localhost:10000/;auth=noSasl" \
  -e "SHOW DATABASES;"
```

### HDFS Issues
```bash
# Check NameNode status
docker exec master-node hdfs dfsadmin -report

# Safe mode check (should be OFF)
docker exec master-node hdfs dfsadmin -safemode get

# Leave safe mode if stuck
docker exec master-node hdfs dfsadmin -safemode leave
```

### Port Conflicts
Ensure these ports are available:
- 8080 (Django)
- 9000 (HDFS RPC)
- 9083 (Hive Metastore)
- 9864, 9865 (DataNodes)
- 9870 (HDFS UI)
- 10000 (HiveServer2 Thrift)
- 10002 (HiveServer2 UI)

---

##  Documentation

- [Architecture Details](docs/ARCHITECTURE.md) - Complete system architecture
- [API Documentation](http://localhost:8080/api/docs/) - Swagger UI (when running)

---

##  License

This project is for educational purposes - Databases for Big Data Seminar.

---

*MBV Climate and Ocean Intelligence Africa - University of Primorska, 2026*
