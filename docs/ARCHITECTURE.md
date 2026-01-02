# Multi-Node Apache Hive & Hadoop Architecture Analysis

## Overview
This document provides a comprehensive analysis of the implemented multi-node Hive cluster simulation for MBV Climate and Ocean Intelligence Africa.

## Architecture Components

### 1. **Distributed Storage Layer (HDFS)**

#### NameNode (Master)
- **Container**: `namenode` (bde2020/hadoop-namenode:2.0.0-hadoop3.2.1-java8)
- **Purpose**: Manages the HDFS namespace and metadata
- **Ports**: 
  - 9000: HDFS RPC
  - 9870: NameNode WebUI
- **Configuration**: `core-site.xml`, `hdfs-site.xml`

#### Hive & Metastore
- **Hive Version**: **Apache Hive 4.0.0**
- **Metastore DB**: PostgreSQL 9.6

#### DataNode1 & DataNode2 (Workers)
- **Containers**: `datanode1`, `datanode2`
- **Purpose**: Store actual data blocks with replication factor of 2
- **Ports**: 9864, 9865 (DataNode service)
- **Data Volume**: Persistent volumes for distributed data storage

**How it simulates distribution**: Each DataNode acts as an independent storage unit. When data is written to HDFS, it's automatically split into blocks (128MB by default) and replicated across both DataNodes, simulating true distributed storage.

### 2. **Metadata & Query Layer (Hive)**

#### Hive Metastore Database
- **Container**: `hive-metastore-db` (PostgreSQL 9.6)
- **Purpose**: Stores Hive table schemas, partitions, and statistics
- **Database**: `metastore`

#### Hive Metastore Service
- **Container**: `hive-metastore`
- **Purpose**: Manages metadata queries and schema operations
- **Port**: 9083 (Thrift)
- **Configuration**: Connects to PostgreSQL backend

#### HiveServer2
- **Container**: `hive-server`
- **Purpose**: SQL interface accepting JDBC/ODBC connections
- **Ports**:
  - 10000: Thrift/JDBC
  - 10002: WebUI
- **Execution Engine**: Can use MapReduce, Tez, or Spark

### 3. **Application Layer**

#### Django Application
- **Container**: `app`
- **Purpose**: Provides REST API and web interface for climate data analysis
- **Port**: 8080
- **Components**:
  - `hive_connector.py`: PyHive integration
  - REST APIs for data analysis
  - Django admin interface

## Docker Integration & Networking

### Container Communication
All services are connected via a Docker bridge network (`apache_hive_test_application_default`), allowing hostname-based communication:

```
app → hive-server:10000 (JDBC/PyHive)
hive-server → hive-metastore:9083 (Thrift)
hive-metastore → hive-metastore-db:5432 (PostgreSQL)
hive-server → namenode:9000 (HDFS)
datanodes → namenode:9000 (HDFS coordination)
```

### Volume Persistence
- `namenode_data`: NameNode metadata
- `slave_node_1_data`: Node 1 data blocks
- `slave_node_2_data`: Node 2 data blocks
- `hive-db-data`: Metastore database
- `./mbv_africa` → mounted to app container for live development

**Verification**:
```bash
docker logs hive-server -f
```

**Test Connection**:
```bash
docker exec hive-server beeline -u jdbc:hive2://localhost:10000 -e "SHOW DATABASES;"
```
