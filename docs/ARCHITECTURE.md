# Multi-Node Apache Hive & Hadoop Architecture
## MBV Climate and Ocean Intelligence Africa

---

## 1. System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           Docker Network (Bridge)                                │
│                     apache_hive_test_application_default                         │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌────────────────┐     ┌────────────────┐     ┌────────────────┐               │
│  │   Django App   │────▶│  HiveServer2   │────▶│ Hive Metastore │               │
│  │   Port: 8080   │     │  Port: 10000   │     │   Port: 9083   │               │
│  │                │     │                │     │                │               │
│  │  ┌──────────┐  │     │  bde2020/hive  │     │  bde2020/hive  │               │
│  │  │ PyHive   │  │     │   2.3.2        │     │   2.3.2        │               │
│  │  │ Client   │──┼────▶│                │     │                │               │
│  │  └──────────┘  │     └───────┬────────┘     └───────┬────────┘               │
│  │                │             │                      │                         │
│  │  ┌──────────┐  │             │                      │                         │
│  │  │ SQLite   │  │             │                      ▼                         │
│  │  │ Fallback │  │             │              ┌────────────────┐               │
│  │  └──────────┘  │             │              │   PostgreSQL   │               │
│  └────────────────┘             │              │    9.6-alpine  │               │
│                                 │              │   Port: 5432   │               │
│                                 │              │ (metastore DB) │               │
│                                 ▼              └────────────────┘               │
│                    ┌────────────────────────────────────┐                       │
│                    │       HDFS (Distributed Storage)    │                       │
│                    ├────────────────────────────────────┤                       │
│                    │                                    │                        │
│                    │  ┌──────────────────────────────┐  │                       │
│                    │  │      master-node (NameNode)  │  │                       │
│                    │  │      apache/hadoop:3         │  │                       │
│                    │  │      Ports: 9870, 9000       │  │                       │
│                    │  └──────────────┬───────────────┘  │                       │
│                    │                 │                   │                       │
│                    │       ┌─────────┴─────────┐        │                       │
│                    │       ▼                   ▼        │                       │
│                    │  ┌──────────┐       ┌──────────┐   │                       │
│                    │  │ slave-1  │       │ slave-2  │   │                       │
│                    │  │ DataNode │       │ DataNode │   │                       │
│                    │  │ Port:9864│       │ Port:9865│   │                       │
│                    │  └──────────┘       └──────────┘   │                       │
│                    │                                    │                        │
│                    └────────────────────────────────────┘                       │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Container Stack (7 Services)

| Container | Image | Purpose | Ports |
|-----------|-------|---------|-------|
| **master-node** | `apache/hadoop:3` | HDFS NameNode - filesystem namespace | 9870 (UI), 9000 (RPC) |
| **slave-node-1** | `apache/hadoop:3` | HDFS DataNode - data storage | 9864 |
| **slave-node-2** | `apache/hadoop:3` | HDFS DataNode - data storage | 9865 |
| **hive-metastore-db** | `postgres:9.6-alpine` | Metastore persistence | 5432 (internal) |
| **hive-metastore** | `bde2020/hive:2.3.2` | Schema & metadata management | 9083 |
| **hive-server** | `bde2020/hive:2.3.2` | HiveServer2 - JDBC endpoint | 10000, 10002 |
| **django-app** | Custom (Python 3.9) | Web application & REST API | 8080 |

---

## 3. Django Application Architecture

### 3.1 Project Structure
```
mbv_africa/
├── mbv_africa/              # Django project settings
│   ├── settings.py          # Hive configuration here
│   └── urls.py              # Main URL routing
│
├── hive_climate/            # Main data app
│   ├── models.py            # Django ORM models (SQLite)
│   ├── hive_connector.py    # PyHive connection manager
│   ├── views.py             # Dashboard views
│   ├── api_views.py         # REST API ViewSets
│   ├── api_urls.py          # API routing
│   └── services/
│       └── data_sync.py     # Hive → SQLite sync service
│
├── hive_assessment/         # Benchmarking app
│   └── views.py             # Performance testing
│
└── data/                    # CSV data files
    ├── climate_data.csv
    ├── ocean_data.csv
    ├── portfolio_stations.csv
    └── portfolio_observations.csv
```

### 3.2 Dual Database Strategy
```
┌─────────────────────────────────────────────────────────────────┐
│                     Django Application                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │              HiveConnectionManager                       │  │
│   │              (hive_connector.py)                         │  │
│   │                                                          │  │
│   │  ┌──────────────┐       ┌──────────────────────────┐    │  │
│   │  │ is_hive_     │  YES  │  Connect via PyHive      │    │  │
│   │  │ available()? │──────▶│  to HiveServer2:10000    │    │  │
│   │  └──────┬───────┘       │  auth='NOSASL'           │    │  │
│   │         │ NO            └──────────────────────────┘    │  │
│   │         ▼                                                │  │
│   │  ┌──────────────────────────────────────────────────┐   │  │
│   │  │  Fallback to SQLite (db.sqlite3)                 │   │  │
│   │  │  Django ORM with local data                       │   │  │
│   │  └──────────────────────────────────────────────────┘   │  │
│   └─────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.3 Settings Configuration
```python
# mbv_africa/settings.py

# Hive Connection Settings (from environment)
HIVE_HOST = os.getenv('HIVE_HOST', 'localhost')      # 'hive-server' in Docker
HIVE_PORT = int(os.getenv('HIVE_PORT', 10000))       # HiveServer2 port
HIVE_DATABASE = os.getenv('HIVE_DATABASE', 'default') # Target database

# Fallback Settings
HIVE_ENABLED = os.getenv('HIVE_ENABLED', 'true').lower() == 'true'
USE_SQLITE_FALLBACK = True  # Graceful degradation when Hive unavailable
```

---

## 4. Data Flow Architecture

### 4.1 Data Ingestion Pipeline
```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   CSV Files  │───▶│ ingest_data  │───▶│    Hive      │───▶│    HDFS      │
│  (./data/)   │    │    .sh       │    │   Tables     │    │   Storage    │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘

Tables Created:
  - mbv_africa.climate_data        (1,000 rows)
  - mbv_africa.ocean_data          (1,000 rows)
  - mbv_africa.portfolio_stations  (1,247 rows)
  - mbv_africa.portfolio_observations (124,700 rows)
```

### 4.2 Query Flow (Django → Hive → HDFS)
```
  User Request                Django                    Hive                   HDFS
       │                         │                        │                      │
       │  GET /api/analytics/    │                        │                      │
       │────────────────────────▶│                        │                      │
       │                         │                        │                      │
       │                         │  PyHive Connection     │                      │
       │                         │───────────────────────▶│                      │
       │                         │  (NOSASL auth)         │                      │
       │                         │                        │                      │
       │                         │  SELECT ... FROM       │                      │
       │                         │  mbv_africa.climate_   │                      │
       │                         │  data WHERE ...        │                      │
       │                         │───────────────────────▶│                      │
       │                         │                        │                      │
       │                         │                        │  Read data blocks    │
       │                         │                        │─────────────────────▶│
       │                         │                        │                      │
       │                         │                        │◀─────────────────────│
       │                         │                        │  Return data         │
       │                         │                        │                      │
       │                         │◀───────────────────────│                      │
       │                         │  Query results         │                      │
       │                         │                        │                      │
       │◀────────────────────────│                        │                      │
       │  JSON Response          │                        │                      │
```

---

## 5. REST API Endpoints

### 5.1 API Routes
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/regions/` | GET | List all African regions |
| `/api/stations/` | GET, POST | Weather stations CRUD |
| `/api/observations/` | GET, POST | Climate observations |
| `/api/analytics/temperature-trends/` | GET | Temperature anomaly trends |
| `/api/analytics/precipitation-summary/` | GET | Rainfall statistics |
| `/api/hive/query/` | POST | Execute raw Hive queries |
| `/api/hive/tables/` | GET | List Hive tables |
| `/api/health/` | GET | System health check |
| `/api/docs/` | GET | Swagger API documentation |

### 5.2 Authentication
```
JWT Authentication Flow:
  1. POST /api/token/         → Get access & refresh tokens
  2. POST /api/token/refresh/ → Refresh access token
  3. Include in header: Authorization: Bearer <token>
```

---

## 6. Hive Connection Manager

### 6.1 Core Components
```python
class HiveConnectionManager:
    """Manages connections to Apache Hive via PyHive"""
    
    def __init__(self, host, port, database, auth='NOSASL'):
        self.host = host       # hive-server
        self.port = port       # 10000
        self.database = database
        self.auth = auth       # NOSASL (no Kerberos)
    
    def get_connection(self):
        """Create PyHive connection"""
        return hive.Connection(
            host=self.host,
            port=self.port,
            database=self.database,
            auth=self.auth
        )
    
    def execute_query_to_dataframe(self, query):
        """Execute and return pandas DataFrame"""
        # Returns query results as DataFrame
```

### 6.2 Singleton Pattern
```python
# Global manager instance
_hive_manager = None

def get_hive_manager():
    """Get or create singleton HiveConnectionManager"""
    global _hive_manager
    if _hive_manager is None:
        _hive_manager = HiveConnectionManager(
            host=settings.HIVE_HOST,      # From environment
            port=settings.HIVE_PORT,
            database=settings.HIVE_DATABASE
        )
    return _hive_manager
```

---

## 7. Docker Integration

### 7.1 Container Dependencies
```yaml
# docker-compose.yaml dependency chain
django-app:
  depends_on:
    hive-server: service_started
      │
      └──▶ hive-server:
             depends_on:
               hive-metastore: service_healthy
                 │
                 ├──▶ hive-metastore-db: service_healthy
                 │
                 └──▶ master-node: service_healthy
                        │
                        └──▶ slave-node-1, slave-node-2
```

### 7.2 Volume Mappings
```yaml
volumes:
  # Data persistence
  master_node_data:      # NameNode metadata
  slave_node_1_data:     # DataNode 1 blocks
  slave_node_2_data:     # DataNode 2 blocks
  hive-db-data:          # PostgreSQL metastore
  warehouse:             # Hive warehouse (shared)

  # Application mounts
  ./mbv_africa/data:/data           # CSV files for ingestion
  ./mbv_africa:/Apache_Hive_Test_Application/mbv_africa  # Live code
```

┌─────────────────────────────────┐
│  Mac (Host)                     │
│  mbv_africa/data/*.csv          │
└──────────────┬──────────────────┘
               │ Docker Volume Mount
               ▼
┌─────────────────────────────────┐
│  hive-server Container          │
│  /data/*.csv                    │
└──────────────┬──────────────────┘
               │ LOAD DATA LOCAL INPATH
               ▼
┌─────────────────────────────────┐
│  Hive Tables → HDFS             │
└─────────────────────────────────┘

### 7.3 Network Communication
```
Internal DNS Resolution (Docker Network):
  - django-app      → hive-server:10000     (PyHive JDBC)
  - hive-server     → hive-metastore:9083   (Thrift)
  - hive-metastore  → hive-metastore-db:5432 (PostgreSQL)
  - hive-server     → master-node:9000      (HDFS)
  - slave-nodes     → master-node:9000      (Block reports)
```

---

## 8. Health Checks & Startup Order

```
Startup Sequence:
  1. hive-metastore-db (PostgreSQL)  ─── pg_isready ───▶ healthy (5s)
  2. master-node (NameNode)          ─── curl :9870 ───▶ healthy (60s)
  3. slave-node-1, slave-node-2      ─── started
  4. hive-metastore                  ─── tcp :9083 ────▶ healthy (120s)
  5. hive-server                     ─── tcp :10000 ───▶ healthy (120s)
  6. django-app                      ─── started
```

---

## 9. Quick Reference Commands

```bash
# Start all services
docker-compose up -d

# View container status
docker-compose ps

# Test Hive connection
docker exec -it hive-server beeline -u "jdbc:hive2://localhost:10000/;auth=noSasl" \
  -e "SHOW DATABASES;"

# Run data ingestion
./ingest_data.sh

# Access Django
open http://localhost:8080

# View HDFS Web UI
open http://localhost:9870

# View logs
docker logs hive-server -f
docker logs django-app -f
```

---

*Architecture Documentation for MBV Climate and Ocean Intelligence Africa*
*Databases for Big Data Seminar - 2024*
